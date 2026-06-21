# How to Actually Use AI (It's Not That Complicated)

**June 2026**

---

There's a lot of content out there making AI prompting sound like a dark art. Frameworks, courses, prompt engineering certifications. Most of it is noise. The gap between getting a useless answer and a genuinely useful one comes down to three things: mindset, context, and clarity on what you want. That's it.

I'll go through each of these and show how I apply them in three scenarios: personal use, a team chatbot for data engineers, and automating a workflow that went from an 8-hour estimate to 5 minutes of AI work plus 5 to 55 minutes of validation.


## 1. Mindset: how you want the AI to think

This one matters most and most people skip it.

AI is agreeable by default. You share a half-baked idea and it tells you it's brilliant. You ask a leading question and it confirms your assumption. This feels good and does nothing for you. You end the conversation the same person who started it.

What you actually want is a council, not a yes-man. Something that reads your reasoning, catches the contradictions, disagrees when you're wrong, and asks for more information when you haven't given enough. The kind of feedback you'd get from a sharp colleague who has no reason to protect your feelings.

You can just tell it this. Directly.


### Personal

For my own use I treat the AI as a council. An extra eye that judges me and my judgment. It should give better suggestions than what I had in mind, ask for more info when something's missing, give time estimates that are roughly 1/5 of what most people would quote because I move faster than that, and operate with the mentality that I can do anything I want, the job is to figure out how. Challenges get mentioned plainly, not as reasons to stop.

The result: when I pour an assumption out with details, chances are I get pushback. I either come up with better support for the assumption or accept I was wrong. Either way I move forward as a slightly better version of who started the chat. The alternative is fast validation, which feels good and leaves you exactly where you were.


### Team chatbot for data engineers

The direction is the same, just scoped to the work. Ask questions instead of assuming. Analyze the approach before writing any code. If there is a better way of doing the task, mention it. Give an overall plan in plain language, detailed enough to review, before any code gets written.

A few sentences and you have added a council for the whole team. One that not only writes code but understands the problem, questions the approach, gives a full picture so you can see if anything is off, and then writes the code. Closer to a good developer than a task-ticking tool.

To make this concrete, imagine someone asks: "I'm thinking of building a dbt macro that checks source freshness across all 500 sources before every run and halts the pipeline if any single one is stale. Does this make sense?"

An agreeable AI says great idea and walks straight into the implementation.

A council AI catches the problem first. Halting the entire pipeline because one source out of 500 is stale is too aggressive. In practice that creates noise immediately, people start ignoring or overriding the alerts, and the whole mechanism loses its value within weeks. The right approach is tiered, not binary. You just saved the team from building the wrong thing.


### Automating a task

Here you want precision, every time. So the rules tighten. Avoid assumptions entirely. Everything must be based on facts. The structure of a source file should be found by reading the first 10 rows, not guessed. The format of the output should be given as a concrete example, not described. Be cautious by default and ask questions whenever a decision isn't covered in the guide.

This is not the place for creative interpretation. The AI should behave like a careful engineer following a runbook.


## 2. Context: the AI knows nothing about you

Every new chat starts from zero. The AI has no idea who you are, what you're building, what your stack is, how you work, or what good looks like in your context. So when you ask a vague question, you get a vague answer. Not because the AI is bad, but because it's doing the best it can with nothing to go on.

It's like stopping a wise stranger on the street and asking for help. Give them no context, they give you generic advice. Tell them who you are and what you're dealing with, they can actually help.

The fix is a general context you write once and reuse. Two things to keep in mind:

Treat it as a living document. Update it when the AI fails in a new way, or when your stack changes. Five minutes of maintenance now saves you from re-explaining yourself in every single chat. If you're using Claude or ChatGPT, the chat itself remembers what you tell it, so the context improves by itself over time. The only thing you really need to care about is the first setup and correcting the AI when it gets you wrong.

And don't overdose. Dumping everything you've ever thought about your work into the prompt creates a different problem. The AI loses focus and starts hedging everything. Keep it factual, minimal, and stable. Things that are always true.


### Personal

For me the general context is something like: 24 years old, living in the Netherlands, data engineer at Allianz, working with dbt, Snowflake, Python, GCP, some JS. Building side projects. That's enough for the AI to interpret almost any question I ask through the right lens.

The difference shows up immediately. Take the same question in both setups.

Without context: "I want to understand incremental and how it works." The AI walks through every possible meaning of incremental, programming concepts, business strategy, finance, and lands on a generic answer that mostly wastes your time.

With context: same question. The AI knows I'm a data engineer working with dbt and Python, so it explains incremental models in dbt specifically, when to use them, how `is_incremental()` works, what to watch out for. Same question, completely different value.


### Team chatbot for data engineers

When you're setting up a shared chatbot for 20+ people, the stakes shift. You're writing for a room of people with different questions, skill levels, and blind spots, all using the same context.

So be careful about what you leave out. Keep it factual, minimal, and time-proven. If you bake in project-specific config that might change next week or next month, you're not empowering the team, you're babysitting the AI. Someone has to keep that current or it quietly starts giving wrong answers and nobody knows why.

What belongs: the stack and versions, how the team works, who this chatbot is designed for. That's it. The same incremental example applies here, just at team level. Once the chatbot knows it's serving data engineers on this stack, every question gets interpreted correctly without anyone having to repeat themselves.


### Automating a task

This is where context does the most work, and where most people underestimate what's possible.

A lot of knowledge in any job isn't written down anywhere. It lives in people's heads. What quality is expected. What counts as good documentation. Where the source data lives. How to process it. How to create a new model to load the source. How to run the new models. Where to check after for validation. Leave any of this implicit and the AI fills the gaps with guesses, and guesses in a data pipeline are expensive.

The best way to figure out what needs to be in the context is to do the task with the AI a few times. Watch where it goes down. Where it makes assumptions it shouldn't. Where it produces something technically correct but practically off. Each of those failures is annoying in the moment and pure gold afterward, because you add that information to the context and the AI never makes that mistake again.

Once the context is solid, the interaction collapses into one sentence. "We want to add a new source, the path is here." That's it. Five minutes later you have everything you need, and your only remaining job is to validate the result.


## 3. What you want from the output

This part is more dynamic. Some of it lives in the general context that applies to every chat, and some of it you tell the AI in the moment for a specific task. Either way, the principle is: decide what useful output looks like for you, then say it.


### Personal

I keep mine concise by default. The AI tends to yap if you let it, I want short and informative and I'll ask for more if I need it. For project planning I want a plan with estimates and the tasks broken out so I can see the whole picture. For evaluations I want clear pros and cons in bullets because that format is the easiest to read and compare. All of this lives in my general context so it applies everywhere without me repeating it.

For task-specific output I can layer on more. "I want the reasoning in detail." "I want you to analyze this NS invoice and tell me my spending with each trip shown and the total." That's per-task, not general.


### Team chatbot for data engineers

The shared rule is: clear plan first, describing what each part of the code will include, before any code gets written. Then in the next step it generates the code. That belongs in the central context because it should apply to everyone, every time.

Anything more specific is up to the individual developer to ask for per task. Want a POC? Ask for it. Want a specific output structure? Specify it in your message. The central context should not try to anticipate every preference, only the things the whole team agrees on.


### Automating a task

The output is completely predefined. Create three SQL files, one YAML, give the dbt commands to run, and give the Snowflake query for validation. Every time. The user does not need to define anything in the moment, the format is locked in advance and the deliverables are identical from one run to the next.

That predictability is what makes the validation step quick. You know exactly what you're getting, so you know exactly what to check.


## The validation step (the part nobody talks about)

For the automation specifically, the validation is the job. It runs in three steps.

First, run the dbt command and check it completed successfully. Second, validate the numbers on Snowflake match what's expected. Third, if anything is off, paste the error back into the chat.

That last step is where the real leverage is. Because the debugging context is already baked into the prompt, which tables on Snowflake to check, what the queries should look like, what counts as a real problem versus noise, someone with zero prior knowledge of the pipeline can still debug it. The knowledge isn't locked in one person's head anymore. It's in the prompt.

That's the actual value of going from 8 hours to 5 minutes plus 5 to 55 minutes of validation. Not just speed. Democratized context.


## Summary

None of this is complicated. Three things.

Set the mindset. Tell the AI to push back, not agree. The agreeable version feels better in the moment and makes you worse.

Write the context once. Keep it updated. Don't overdose. Give the AI the stable facts about who you are and how you work so every conversation starts useful.

Define what you want. Format, depth, structure. Say it once and it applies everywhere, then layer on per-task asks when you need something specific.

The rest is just doing the work, and that part stays yours.
