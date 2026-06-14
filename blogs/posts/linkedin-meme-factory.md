# 200 Memes a Day, Hands-Off: A LinkedIn Content Pipeline

**February 2026**

---

**TL;DR.** I built a Python pipeline that generates niche-specific meme content with Grok, validates each batch with a second LLM pass, renders 20 PIL meme templates, and posts to LinkedIn on a schedule via GCS and GCP Cloud Tasks. Two execution modes share the same codebase: eager (pre-render locally, then schedule) for one-off batches, and lazy (save only the JSON copy in Postgres, render inside a Cloud Function at post time) for production. Ran it on 3 LinkedIn business pages until LinkedIn capped me from creating more. Code is open at [linkedin-meme-factory](https://github.com/hiwafeizi/linkedin-meme-factory).

---

## Real posts from the run

Same pipeline, two of the three niches: `devhumormeme` and `financebromeme`.

<div class="linkedin-embeds">
<iframe src="https://www.linkedin.com/embed/feed/update/urn:li:activity:7461373147729133568" frameborder="0" allowfullscreen="" title="DevHumor — Turning glitches into gold standards"></iframe>
<iframe src="https://www.linkedin.com/embed/feed/update/urn:li:activity:7460380356593106944" frameborder="0" allowfullscreen="" title="DevHumor — Activity 7460380356593106944"></iframe>
<iframe src="https://www.linkedin.com/embed/feed/update/urn:li:activity:7462114780913373184" frameborder="0" allowfullscreen="" title="FinanceBro — Trusty automation until it isn't"></iframe>
<iframe src="https://www.linkedin.com/embed/feed/update/urn:li:activity:7462044610916282369" frameborder="0" allowfullscreen="" title="FinanceBro — Auditing evolution"></iframe>
</div>

## Why I built it

In early 2026 I wanted to see if you could build organic LinkedIn growth funnels with no human in the loop. Pick 10 professional niches, generate niche-specific meme content at scale, post twice a day per account, see what compounds.

I already had GCP set up for NeoCru, so I reused that project to save infra time. Cloud Tasks for scheduling, Cloud Storage for image hosting, service account auth for the LinkedIn post endpoint. The meme system itself is a standalone codebase, no NeoCru code touched.

3 accounts active. 2 posts per day per account. 100 days set in advance as the success/fail threshold per page: if a page hadn't earned meaningful traction by day 100, the hypothesis was wrong. No manual approval, no human touching the output between "go" and "posted".

## Why Grok

The model choice was deliberate. The use case is humor, not analysis, and Grok's training leans heavily on Twitter, which is the closest thing to a corpus of professional shitposting in the wild. The polished models I'd used elsewhere (OpenAI, Claude) kept softening jokes, making things grammatically correct, adding hedges, smoothing edges. For memes, polish is the enemy. Grok defaulted to the right register.

It was also the cheapest and lightest model for this workload. I used `grok-4-fast-non-reasoning`: a batch call returning 10 variations costs fractions of a cent, and the total Grok spend across the whole run came out to $0.34. The trade-off was reliability: Grok occasionally ignored format constraints or drifted off-template. That's exactly why Stage 2 exists.

## The architecture

The pipeline has 4 stages:

1. **Generate** copy with Grok for each (niche, template) pair.
2. **Validate and fix** every batch with a second LLM call against a humor model.
3. **Render** the validated copy onto template images, using per-slot positioning from a catalog.
4. **Post on a schedule** via GCS + GCP Cloud Tasks.

Each stage is independent. I can re-render without regenerating, re-schedule without re-uploading, swap templates without touching the LLM logic.

The same codebase supports two execution modes: eager (render every meme up front, then schedule the image files) and lazy (save only the JSON copy in a Postgres table, render inside a Cloud Function at post time). Eager was the prototype. Lazy was what actually ran in production.

## Eager vs lazy rendering

The first version of the pipeline rendered every meme locally, uploaded the resulting JPEGs to GCS, then scheduled one Cloud Task per image. Simple. Predictable. Easy to debug because every image existed as a file before any post fired.

It had three problems that compounded once I went past 50 scheduled posts.

**Storage was the wrong shape.** Hundreds of pre-rendered JPEGs sat in GCS for days waiting to be posted. Cheap, but pointless. If the post was cancelled or the copy needed a tweak, the image was already shipped.

**Editing was painful.** Once a meme was rendered and the Cloud Task was queued, changing the text meant cancelling the task, regenerating the image, re-uploading, re-scheduling. The friction was high enough that I stopped editing and just lived with bad batches.

**The render was fast, but the surface area was huge.** Re-rendering one meme is milliseconds of work, but the bundle of templates plus catalog plus fonts plus PIL plus the slot renderer had to exist on whatever machine did the work.

So production flipped it: store only the meme copy (the JSON), schedule by `(template, data, time)`, and render at post time inside a GCP Cloud Function. The bundle gets deployed once into the function. Every scheduled post is a row in Postgres. To cancel a post, I delete the row. To edit, I update the row before its scheduled time. No JPEGs sitting around. No re-upload step.

## Stage 1: Niche-specific prompts as data

The first design decision was that prompts are data, not code.

The `prompts/` folder has 10 JSON files, one per niche: tech, finance, startup, corporate, data, sales, marketing, consultant, product, recruiter. Each file is a dict of `{template_name: prompt_string}`. Adding a new niche means dropping a new JSON file. Adding a new template means appending a key.

A snippet from `tech_prompts.json`:

```json
{
  "Drake Hotline Bling": "You are generating tech memes for developers, DevOps engineers, and IT professionals. Create 'Drake Hotline Bling' memes about tech preferences.\n\nTemplate: Reject proper way. Approve lazy way.\n\nExamples:\n{\"reject\": \"PROPER ERROR HANDLING\", \"approve\": \"LET IT CRASH\"}\n{\"reject\": \"WRITE TESTS\", \"approve\": \"SHIP AND PRAY\"}\n\nKeep concise and punchy (aim for 4-6 words per field)."
}
```

Three things had to be in every prompt:

**Audience framing.** Who reads this and what frustration they share.

**Template usage pattern.** What the meme structure means semantically. "Reject proper way. Approve lazy way" is not a description of pixels, it's a description of the joke.

**Few-shot examples.** Two or three concrete input/output pairs so the model pattern-matches instead of inventing format.

The API call wraps this with a batch instruction:

```python
batch_prompt = f"""{base_prompt}

IMPORTANT: Generate exactly {count} DIFFERENT variations.

Respond with a JSON array containing {count} objects.
Make sure each variation is distinctly different.
Respond ONLY with the JSON array, no other text."""
```

One API call returns 10 variations. Temperature 1 because the prompt is already tight.

## Stage 2: The validate-and-fix pass

This was the part that turned a 30%-usable batch into a 90%-usable batch.

The generator is fast and creative but it cheats. It writes memes that miss the template's humor model. It produces lines too long for the image slot. It writes "level 4" of an Expanding Brain meme as a *more* sophisticated take instead of the absurd punchline the template demands.

So every batch goes through a second LLM call. The validator gets:

- The same template's `usage_pattern`, `text_structure`, and `how_to_write` from a catalog.
- A `humor_model` block explaining *why* the template is funny and *how to reproduce* it.
- The 10 generated memes.

And returns:

```python
{
  "has_issues": bool,
  "evaluation": "short text",
  "issues": [...],
  "corrected_memes": [...] | None,
}
```

The trickiest part of writing the validator prompt was telling it *not* to fix things that didn't need fixing:

```text
IMPORTANT MEME CULTURE CONTEXT:
- ALL CAPS text is NORMAL and EXPECTED - this is NOT an issue
- Mixed case like "ThIs Is FiNe" is mocking sarcasm - CORRECT
- Grammar/spelling mistakes are FINE unless they ruin the joke
- Memes are NOT essays - they're STUPID and FUN jokes
- "Correct" language is NOT the goal - FUNNY is the goal

DO NOT TRY TO MAKE MEMES "CORRECT" OR FORMAL!
```

LLMs default to making text formal. For meme content, that defaulting is actively harmful. Half of this prompt is permission to leave things alone.

## Stage 3: 20 template classes and a 1,000-line catalog

The renderer is a small abstraction over PIL.

`meme_templates.py` has 20 classes, one per template (Drake, Distracted Boyfriend, Boardroom Meeting, Expanding Brain, Ancient Aliens, and so on). Each extends a shared `MemeTemplate` base and implements `render(meme_data)`:

```python
class DrakeHotlineBling(MemeTemplate):
    def __init__(self, output_audience):
        super().__init__("drake_hotline_bling.jpg", "Drake Hotline Bling", output_audience)

    def render(self, meme_data):
        self.img = Image.open(self.template_file)
        self._render_text_to_slot(self.img, meme_data.get("reject", ""), "reject")
        self._render_text_to_slot(self.img, meme_data.get("approve", ""), "approve")
```

The interesting work is in the base class's `_render_text_to_slot`. The constraints that have to hold per slot:

**Bounded box.** Each slot has `x, y, width, height` from a catalog. Text must fit inside.

**Auto-fit font size.** Pick the largest font where the wrapped text still fits the box height, given line spacing.

**Rotation.** Some slots (the boardroom paper, the Change My Mind sign) sit at an angle. The text is drawn into a temporary RGBA canvas, rotated with `Image.rotate(expand=True)`, then pasted back onto the meme with alpha.

**Stroke for legibility.** White fill, black stroke at `font_size / 16`, vertically centered. The stroke is what keeps the text readable on any background.

**Case enforcement.** Most templates force uppercase. One (Mocking Spongebob) is explicitly excluded so the alternating-case mocking from the LLM survives.

A separate `research/meme_catalog.json` holds the slot positions and rotations for every template. The template class only knows it has a `reject` slot and an `approve` slot. The catalog tells the renderer where those slots live in pixels.

### The catalog: where quality actually lived

The slot positions are the part I could measure with a ruler. The catalog had more than that.

Every template has a full spec: pixel boxes, rotation, but also `usage_pattern`, `text_structure`, `where_to_write`, `how_to_write`, and a `humor_model` block. The humor model is what made the difference between an LLM that wrote technically-correct memes and an LLM that wrote funny ones.

Ancient Aliens looked like this:

```json
{
  "template_name": "Ancient Aliens",
  "usage_pattern": "Blaming unexplained outcome on broad catch-all cause.",
  "text_structure": "top setup/question; bottom single-cause answer",
  "how_to_write": "Use faux-explanation style. Single-word or tiny phrase answer works best for punch.",
  "comments": [
    {"slot": "question", "size_constraints_px": {"x": 0, "y": 0, "width": 500, "height": 84}, "rotation": 0},
    {"slot": "answer",   "size_constraints_px": {"x": 0, "y": 350, "width": 500, "height": 87}, "rotation": 0}
  ],
  "humor_model": {
    "why_it_is_funny": "Funny from fake certainty: complex problem, one simplistic answer.",
    "how_to_reproduce": "Top asks why; bottom is one broad cause word/phrase.",
    "example_comments": ["WHY DID THIS INCIDENT HAPPEN?", "LEGACY SYSTEMS"]
  }
}
```

Every field had to be tuned per template. The slot boxes I figured out by measuring screenshots. The `usage_pattern` and `text_structure` I extracted by looking at examples of each meme until I could state the rule. The `humor_model` was the loop that took the longest: generate a batch, look at the output, find the way it was missing the joke, rewrite the `why_it_is_funny` and `how_to_reproduce` lines, regenerate.

Expanding Brain was the hardest. The generator kept writing level 4 as a *more* sophisticated take instead of the absurd punchline. It took five passes through the humor model before the prompt reliably produced the expected stupidity. Mocking Spongebob needed a special case because the LLM kept normalizing the alternating-case output; I had to keep the slot-level uppercase rule but explicitly carve out one template.

Once a template's humor model was right, the prompts for that template across all 10 niches got better at the same time, because the validate-and-fix pass uses the same catalog. One catalog edit fixed quality across 10 prompt files at once.

The orchestration loop ties it together:

```python
for template_name, prompt in templates.items():
    memes = api.generate_memes(prompt, memes_per_template)
    memes = api.validate_and_fix_memes(
        memes, expected_fields, template_name, audience, template_context
    )
    template_class = MEME_TEMPLATES[template_name]
    for idx, meme_data in enumerate(memes, 1):
        meme = template_class(audience)
        meme.render(meme_data)
        meme.save(f"{template_name}_v{idx}")
```

Generate, validate, render, save, next. If one template fails, the others still ship.

## Stage 4: Schedule and post

Production scheduling is decoupled from rendering. A scheduled post is one row in Postgres: `(template, meme_data, caption, scheduled_time, account_id, status='scheduled')`. Nothing is rendered or uploaded yet at that point.

Two Cloud Functions do the work.

**`task-loader`** is the self-perpetuating piece. Every 24 hours it:

1. Reads from Postgres every post with `status = 'scheduled'` and `scheduled_time` within the next ~27 hours.
2. For each one, creates a Cloud Task pointed at `meme-publisher`, with the meme payload as the body and the post's `scheduled_time` as the task's schedule time.
3. Marks the row `status = 'queued'`.
4. Creates one more Cloud Task pointed at itself, scheduled for 02:00 UTC tomorrow.

Set it running once and it keeps queueing forever. No cron, no host I have to keep alive.

**`meme-publisher`** is what each Cloud Task hits at its scheduled time. It:

1. Reads the template name + slot data from the task body.
2. Refreshes the LinkedIn access token from Postgres if it's near expiry (OAuth refresh, written back to DB).
3. Renders the meme with PIL using the same logic as the local pipeline, bundled into the function with templates and fonts.
4. Uploads the rendered image to GCS.
5. Initiates a LinkedIn image upload, PUTs the binary, then creates the LinkedIn post referencing the image URN.
6. Writes back `status='published'`, `linkedin_post_id`, `image_url`, `published_at`.

The local `schedule_linkedin.py` script is the eager-mode equivalent for one-off batches: render locally, upload images, push one Cloud Task per image at a simpler posting handler. Easier to debug, not what kept running for weeks.

Cloud Tasks gave me four things I would have had to build otherwise:

**Per-task scheduling.** No "what to post next" table to read on a loop. The task carries its own scheduled time.

**Built-in retries with backoff.** If LinkedIn rate-limits, Cloud Tasks handles the retry.

**OIDC token auth.** Both functions are `--no-allow-unauthenticated`. Only calls signed by the configured service account get in.

**Burst scheduling.** `task-loader` queues a whole day in a few seconds and walks away.

## What I shipped

Across 3 LinkedIn business accounts: 100 days per account, 2 posts per day, ~600 posts total. Total compute cost was negligible. The Grok API calls totalled $0.34. GCS storage was cents. Cloud Tasks free tier was enough. The expensive part was the writing: the prompts, the humor catalog, the slot positions for the 20 templates.

## What didn't work

After 100 days per account, engagement was effectively zero.

The system did exactly what it was designed to do. Memes were on-brand for each niche, rendered cleanly, posted on schedule. They were also invisible. None of the 3 accounts gained meaningful followers in the window I'd set as the threshold.

The thing the system could not do is the thing that actually matters for LinkedIn organic growth: get the first 20 people to like and comment on every post within the first hour. LinkedIn's distribution is roughly this: if the post earns engagement in the first hour, it goes further. If it sits cold, it dies in the feed and never gets shown again.

A pipeline that generates and posts content does not solve cold start. You need at least one of:

- Pre-existing audience pull
- A pod of accounts engaging on every post
- Paid distribution to seed the first hour
- Genuinely viral content where the meme itself overcomes cold start

I had none of those. The pipeline assumed supply was the bottleneck. Supply was not the bottleneck.

And then LinkedIn capped me at 3 business pages. The plan was 10 niches, one page each, so I could pick whichever started showing signal and double down. LinkedIn's policy doesn't let one personal account spin up more than a small number of business pages, and I hit that ceiling early. The 10-niche fan-out was structurally impossible from one account.

That cap is what made me stop. Even if I'd been willing to push through the cold-start problem on a single page, the 10-niche hypothesis the pipeline was built for couldn't be tested. The architecture assumed I could spin up a page per niche and let the data say which ones grew. The platform said no.

## What I'd do differently

If I rebuilt this with the same constraints, the pipeline architecture would stay. It's the right shape for the problem. What I'd change is what runs through it.

**Stop optimizing for supply.** The bottleneck was distribution, not generation. The same pipeline could power any structured-content stream; it just has to land on a channel where it gets seen.

Code is open at [linkedin-meme-factory](https://github.com/hiwafeizi/linkedin-meme-factory).
