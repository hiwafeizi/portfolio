# Half Stupid: Teaching Minecraft Agents to Survive From Scratch

**April 2026**

---

What if you dropped four newborns into a world with no instructions, no labels, no pre-built knowledge — and the only thing keeping them alive was a ticking hunger bar?

That's the experiment. Four AI agents in a Minecraft world. They see numbers. They can press buttons. They get +1 for every tick they stay alive. When they die, it's -10,000. That's it. No "this is food," no "avoid lava," no "that's another player." Everything they know, they have to figure out from raw experience.

I called the project "Half Stupid" because the goal isn't artificial general intelligence. It's something more interesting: building a brain from the bottom up, layer by layer, the way evolution did it. Start with reflexes. Add memory. Add fear. Add planning. Eventually, maybe, add language. Nine stages, from brainstem to theory of mind.

This is the story of Stage 1: learning to eat.

## Why Minecraft? Why Malmo?

Minecraft is one of the few environments that gives you everything at once — 3D space, physics, inventory, crafting, other agents, day/night cycles, hunger, health, combat. It's complex enough to need real intelligence but structured enough to control.

The bridge between Minecraft and AI is Microsoft's Project Malmo, an open-source platform that lets you write programs that interact with Minecraft through observations and commands. You describe a world in XML, spawn agents, read their sensor data, and send them actions.

The limitations are real though. Malmo is built on Minecraft 1.11.2, which is from 2016. The API is clunky — observations come as JSON blobs that sometimes arrive late or not at all. Multi-agent support works but has race conditions. The documentation is thin and the community has largely moved on. The whole thing feels like duct-taping a research platform onto a game that was never meant for it.

But it has one thing nothing else does: a rich, persistent, multi-agent survival world that humans already intuitively understand. When I say "an agent learned to eat bread," you know exactly what that means. Try explaining that about a gymnasium environment with state vector [0.34, -0.12, 0.98, ...].

## The World

Stage 1 is a 16x16 grassy yard with fence walls. Daytime, clear weather. Cake blocks scattered on the ground near where the agents spawn. A small tree in the corner. Some flowers. Occasionally (20% of episodes) a lava pit appears in the center — and when it does, there's no cake. Pure survival.

Four agents: Adam, Eve, Cain, and Abel. Biblical names because they're the first of their kind.

Each episode they spawn at random positions facing random directions — some looking up at the sky, some down at their feet, some facing a wall. They get a randomized hotbar each time: some slots have food (cooked beef, bread, apples, etc.), some have junk (sticks, stones, feathers), and occasionally 1-3 slots contain poison (spider eyes, rotten flesh, poisonous potatoes). Hunger drains continuously. Starvation kills.

## What the Agents See

This is the part people misunderstand. The agents don't see Minecraft. They don't see pixels, textures, or a 3D scene. They see a flat array of numbers.

Their "vision" is a 5x5 grid sampled at 4 height levels (below feet, floor level, eye level, above head) — 100 block IDs total. Each block is just an integer. Block 0 means empty (air). Block 7 might be grass. Block 23 might be cake. The agent has no built-in knowledge that 23 means food. It's just 23.

They also get raw float numbers: health, food level, their position (x, y, z), yaw, pitch, what's in their 9 hotbar slots, which item they're holding, whether they're currently eating/moving/jumping/crouching.

More recently I added entity awareness — they can sense up to 3 other agents and 5 dropped items nearby, with distance and angle relative to where they're looking. And direction encoding: instead of raw yaw=90 (meaningless to a neural network), they get sin(yaw) and cos(yaw), which naturally represents circular direction.

Total input: 557 floating point numbers. No labels. No categories. No hand-crafted features.

## What They Can Do

23 actions, same as a keyboard player:

Walk forward/backward, strafe left/right, turn left/right, look up/down, jump, crouch, use (eat/interact), attack, throw item, select hotbar slot 1-9, and stand still.

These are masked in — meaning the agents start with only "eat" and "stand still" available, and new actions are gradually unlocked as they demonstrate competence with existing ones. By the time training is mature, all 23 actions are available.

## The Brain: A Brainstem

The neural network is deliberately small. A brainstem isn't supposed to think — it's supposed to react.

### The Reflex Layer (fires every tick)

Every game tick (~100ms), the agent's brain does this:

1. Look up each of the 118 block/item/agent IDs in a shared embedding table (2048 x 4 dimensions). Every block in Minecraft gets a 4-dimensional vector representation. The agent learns these embeddings — cake and bread end up near each other, while stone and dirt cluster separately.

2. Concatenate the 472 embedded floats + 85 raw floats = 557 input values.

3. Feed through one hidden layer of 32 ReLU nodes.

4. Output 23 action logits, softmax to probabilities, sample an action.

That's it. 557 -> 32 -> 23. About 25,000 parameters. The hidden layer runs in NumPy for speed (no PyTorch overhead per tick), and we only use PyTorch for the gradient update at the end of each episode.

### The Context Layer (fires every 5 ticks)

Pure reflex has a problem: it only sees the current moment. It doesn't know "I've been eating for 4 ticks, keep holding the button" or "I turned right twice and still no food, keep turning." So I added a slower context layer.

Every 5 ticks, it reads:
- The last 5 reflex hidden states (what the brain perceived each tick)
- The last 5 sets of action flags and health/food (what was happening)
- The current hotbar item embeddings (what's available)

That's 241 inputs -> 64 hidden nodes -> 23 action logits. These context logits get added to the reflex logits before the final softmax. The context layer learns at a fraction of the reflex learning rate — it grows slowly so it doesn't destabilize what the reflex already knows.

The biological analogy is real: your brainstem fires every millisecond (heartbeat, breathing, reflexes). Higher brain regions fire slower and modulate the brainstem's behavior. The reflex says "eat NOW." The context says "...but maybe not that one."

### No Shortcuts

The design philosophy is aggressive minimalism:

- **Only reward is survival.** +1 per tick alive, -10,000 on death. No shaping rewards like "+5 for eating food" or "-1 for touching lava." The agent has to figure out that eating prevents starvation, not because I told it eating is good, but because agents that eat survive longer.

- **No hand-crafted features.** The network sees raw IDs and learns what they mean. I don't tell it "cake is food" — it discovers that block 23 in the vision grid correlates with the "use" action correlating with the food bar going up correlating with not dying.

- **Shared embeddings across everything.** The same 4-dimensional vector represents "cake" whether it appears in the vision grid, the hotbar, or as a dropped item. The network learns one concept per block type, not three.

- **No curriculum engineering beyond masking.** I don't craft reward schedules or engineer scenarios. The world is the world. Lava appears randomly. Poison appears randomly. Other agents compete for food. The gradient signal comes from survival, nothing else.

## Training: REINFORCE the Hard Way

The training algorithm is vanilla REINFORCE — the simplest policy gradient method. At the end of each episode (when everyone dies or time runs out), we replay all the observations through PyTorch, compute discounted returns (gamma=0.97, meaning events ~130 ticks before death get punished), and update the weights.

The gamma of 0.97 is important. It means if you die at tick 200, tick 70 gets almost no blame. But tick 190 gets heavy blame. This forces the network to learn short-term survival reflexes, which is exactly right for a brainstem.

Training speed was a problem early on. I started with PyTorch GPU (RTX 4060) for the forward pass, but the tensor transfer overhead for such a tiny network was enormous — GPU was slower than CPU. Switched to a NumPy forward pass for the per-tick inference (fast, no autograd), with PyTorch only for the end-of-episode gradient update. This got us to ~4,000 ticks per second.

Another Windows gotcha: `time.sleep(0.001)` actually sleeps for 15ms on Windows. At 4,000 ticks/sec, that's catastrophic. Removed all sleeps.

## The Debugging Grind

Nothing worked the first time.

**Eating takes 32 ticks.** In Minecraft, eating is not instant — you hold right-click for 32 game ticks (1.6 seconds at normal speed). My agents kept starting to eat, then randomly switching to another action after 1-2 ticks, interrupting the eat. Fixed by making "use" a continuous action — once started, it holds until the agent explicitly chooses something else.

**Pitch accumulated.** The "look up" and "look down" commands were continuous, so the agent's view kept drifting toward staring straight up or straight down and getting stuck. Fixed by making pitch a pulse action: send the command, immediately reset to zero.

**Agents spawned facing outward.** Minecraft's yaw system: 0=South, 90=West, 180=North, 270=East. I had the directions backwards. Agents would spawn facing the fence wall, not the food. A simple number swap, but it wasted a hundred episodes of training.

**`@p` targeted the wrong player.** In multi-agent Malmo, Minecraft commands like `/give @p apple 10` give the apple to the nearest player to... what? The command block? The first spawned agent? It was unpredictable. Fixed by using agent names explicitly: `/give Adam apple 10`.

**Old checkpoints broke with new architectures.** When I added entity awareness (8 new input IDs), the saved weights for a 529-input network couldn't load into a 557-input network. Fixed with backward-compatible padding: new input positions get zero weights, so they have no effect until trained. The old knowledge is perfectly preserved.

**The weight analyzer showed 100% stand_still.** My analysis tool was simulating the network with all-zero vision IDs, which meant 100 EMPTY embeddings flooding the input. Of course the agent stands still when it sees nothing. Fixed by feeding realistic vision data (dirt, grass, cake, air).

## What Emerged: Four Personalities

After about 1,400 episodes, the four agents developed distinctly different strategies. Nobody programmed this. They all started from the same random initialization, trained on the same reward signal, in the same world. The only difference is where they spawned and which random events they encountered.

I built analysis tools that examine the embedding space — how the network represents each block, item, and agent internally. The results are fascinating.

### Adam: The Focused Eater

Adam developed the cleanest eat reflex. 19 of his 32 hidden nodes are STRONG eat drivers. His food-junk embedding distance is large (well-separated categories). His weights are exploding the fastest, but his behavior is stable.

His perception of other agents: Abel is a unique entity in its own space (far from everything). Cain is near POISON. Eve is moderately distinct. Adam has the highest "agent spread" — he differentiates between agents more than anyone else.

### Eve: The Social Generalist

Eve has the most eat-focused network of all (20/32 reflex nodes), but paradoxically, her eat-promoting blocks list includes **other agents**: Abel, Cain, and Adam all trigger her eat response. She eats MORE when other agents are in her vision.

Eve also sees all other agents as nearly the same (lowest agent spread of 0.96). She doesn't distinguish between them — everyone is just "another entity nearby, probably safe to eat."

Her context layer is mostly dead (57/64 nodes inactive), but the 7 that work are interesting: 3 eat suppressors and 4 movement nodes. Her context learned restraint before it learned anything else.

### Cain: The Complex One

Cain is the standout. His reflex layer is the most diverse: 16 eat nodes (lowest), plus 3 turn_left, 3 hotbar_2, 2 hotbar_7 — actual action variety. He's the only agent with a node dedicated to "stop eating when full" (node 10: use_eat=-16.0, activates on high health/food).

His context layer is the most developed: 8 strong nodes, 12 medium, 23 weak, 21 dead. Most importantly, **different context nodes drive different actions** — unlike Adam and Abel who route everything through one or two nodes. Cain has specialized temporal patterns for movement, hotbar selection, and eating.

His embedding space has rotten_flesh mapped to DANGER (not FOOD) — he's the only agent who partially classifies poison correctly. He also has a mutual hostility relationship with Adam: Cain maps Adam to DANGER, and Adam maps Cain to POISON. Competitive dynamics emerging purely from survival pressure.

### Abel: The Confused One

Abel has the most inverted brain. His eat-promoting blocks include flowing_lava, spider_eye, and poisonous_potato. His eat-SUPPRESSING blocks include carrot (actual food) and bone (junk). His food-junk distance was the worst early on (1.45 — practically identical categories), though it improved dramatically to 11.74 by episode 1,950.

Abel maps all other agents to POISON. His context layer is structurally similar to Adam's (32 strong eat nodes), but with 2 eat suppressors instead of 1. He's essentially Adam's twin with worse embeddings.

## The Poison Problem

Here's the thing nobody solved: **every agent classifies all poison as food.**

At episode 1,950, the FOOD-POISON embedding distances are:
- Adam: 0.65 (practically identical)
- Eve: 1.58 (slightly separated)
- Cain: 2.07 (best, but still overlapping)
- Abel: 1.05 (overlapping)

The problem is fundamental to the reward structure. When you eat a spider eye, here's what happens in game time:
- Tick 1-32: holding "use," food bar goes up. Reward = +1 per tick.
- Tick 33: poison effect starts. Health drops slowly.
- Tick 60+: health low enough to threaten death.

From the gradient's perspective, the first 32 ticks of eating poison look identical to eating food. Both get +1 alive. The negative signal comes much later, and with gamma=0.97, it's diluted across dozens of ticks of positive reward.

This is actually what the context layer was supposed to solve — it sees 5 ticks of history, so it could learn "health was dropping after I ate that thing." But in practice, the context layer mostly became another eat amplifier rather than a poison detector. The signal is there but too weak.

Early in training (~1,350 episodes), Adam was actually classifying poison correctly (all 3 items mapped to DANGER). By episode 1,950, that collapsed — poison merged back into the food cluster. The stronger gradient signal from the context layer's 64 eat-focused nodes pushed food and poison together rather than apart. More eating power overwhelmed the subtle poison signal.

This might be the clearest example of why bottom-up learning is hard: the correct behavior (avoid poison) requires temporal reasoning that a reflex-grade network barely has the capacity for. The solution probably has to come from a higher brain module — the hippocampus (memory) or amygdala (learned fear). Which is exactly the next stage.

## The Weight Explosion

The embedding vectors are growing. At episode 1,350, the EMPTY embedding norm was ~19. By episode 1,950, it's ~37. All distances roughly doubled. This isn't better separation — it's inflation.

With 32 reflex nodes + 64 context nodes all pushing "eat," and a learning rate of 0.03, the gradients compound. Every successful eat reinforces the eat pathway, which makes the weights larger, which makes the gradients larger, which makes the weights larger.

This is a known problem with REINFORCE on continuous training (no fixed dataset, just on-policy rollouts). Options: lower learning rate, gradient clipping, weight decay. I haven't intervened yet because the behavior is still functional — the agents eat successfully. But the numbers are getting uncomfortable.

## Architecture Decisions

A few choices that weren't obvious and why I made them:

**Shared embeddings (4 dims).** Every block, item, and agent name shares one 2048x4 embedding table. This forces the network to develop a unified concept of "what is this thing" rather than separate representations for "cake in my vision" vs "cake in my hotbar." 4 dimensions is enough for Stage 1 categories (food/poison/junk/terrain/danger/agent/empty). Higher brain modules will use their own larger embeddings (8D, 16D) initialized from the brainstem's 4D vectors — preserving existing knowledge while adding capacity.

**NumPy forward, PyTorch backward.** The forward pass runs ~4,000 times per second per agent. PyTorch tensor creation overhead dominates at this scale. NumPy with pre-copied weight arrays is 10x faster for a 557->32->23 network. We only use PyTorch for the episode-end gradient update where autograd actually matters.

**Context layer fires every 5 ticks, not every tick.** This isn't just efficiency — it's design. The context layer represents a slower cognitive process. If it fired every tick, it would just be a second hidden layer. By firing every 5 ticks and holding its output steady, it creates two distinct timescales: fast reflexes (tick-by-tick) and slower intentions (5-tick plans). The biological parallel: your brainstem adjusts your heart rate every beat, but your prefrontal cortex plans your next meal over minutes.

**Context gradient flows back to reflex.** Initially I detached the context layer's input from the reflex computation graph, meaning the context couldn't influence how the reflex represents things. This was wrong — it meant the context was building on a foundation it couldn't shape. Removing the detach lets the context say "I need the reflex hidden state to represent cake differently from cobblestone over time," and that pressure reaches the embeddings. The slower learning rate (initially 0.2x, now 1.5x after the initial careful period) prevents the context from destabilizing the reflex.

**Sin/cos direction encoding.** Raw yaw (0-360) is nearly meaningless to a neural network. The values 1 degrees and 359 degrees are numerically far apart but directionally adjacent. Sin/cos encoding makes the circular nature explicit: sin(0) is approximately sin(360), and perpendicular directions naturally map to independent values. Same for relative angles to other entities — "that agent is to my left" becomes a clean signal instead of an angle subtraction problem.

**Random spawns + random pitch.** Agents used to spawn at fixed positions facing inward. This let them memorize "turn left, walk forward, eat." Random position (-7 to +7), random yaw (0-359), random pitch (-45 to +45) forces genuine spatial reasoning. You can't memorize a route when you start in a different place looking a different direction every time.

**No reward shaping. Ever.** This is a hill I'll die on. The moment you add +5 for eating or -10 for touching lava, you've encoded human knowledge about what matters. The agent learns to maximize your reward function, not to survive. If the only reward is staying alive, then everything the agent learns is grounded in actual survival value. Poison avoidance, food seeking, threat awareness — they all have to emerge from the same universal signal. This is slower but what emerges is real.

## What the Agents Actually Learned

The reflex layer alone was enough for Stage 1. After ~1,950 episodes, all four agents learned to:

- **Eat when hungry.** They respond to low health and low food levels by selecting food from their hotbar and holding the use action for the full 32 ticks. This emerged purely from survival pressure — no one told them food exists or what eating does.
- **Build meaningful embeddings.** The shared embedding space cleanly separates food items (cake, bread, beef) from non-food (sticks, stones, dirt) and from other agents. Each category clusters in its own region of the 4D space. The network invented its own ontology from raw integer IDs.
- **Differentiate other agents.** Each agent developed a distinct internal representation of the other three, with varying distances in embedding space reflecting competitive dynamics that emerged from shared survival pressure.

The context layer helped sustain eating actions across ticks, but the core survival behavior lives in the reflex. A 557->32->23 network with 25,000 parameters, trained on nothing but +1 alive and -10,000 dead, learned to keep itself alive. That's what a brainstem is supposed to do.

---

*The project is called Half Stupid because full intelligence was never the goal. A brainstem doesn't need to be smart. It needs to keep you alive long enough for the smart parts to figure things out.*

*[Code on GitHub](https://github.com/hiwafeizi/half_stupid) | Platform: Minecraft 1.11.2 + Project Malmo 0.37.0 | Windows 11*
