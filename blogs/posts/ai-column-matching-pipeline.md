# How I Automated SAS-to-Snowflake Column Matching with AI

**April 2026 — Allianz Data Office**

---

## TL;DR

Hundreds of tables needed column-level matching between SAS and Snowflake — different names, different content, extra columns on both sides. Senior developers were spending over a day per table doing this manually. I built a pipeline that chains AI calls with deterministic data engineering to automate the whole process. Per-table effort went from days to minutes, with 93% match accuracy. Built in under two weeks, mostly with Claude.

---

## The Problem

We were in the middle of a large-scale migration. Hundreds of tables lived on both SAS and Snowflake, but there was no shared schema, no documentation, and no column mapping between them.

The column names were different on each side. The content could be different. Both sides had extra columns that didn't exist on the other. There was no 1:1 relationship you could just look up.

The way this was being done before: senior SAS developers who also had Snowflake experience would sit down and manually compare columns, write SQL, check values, and try to figure out which columns matched. This took more than a day per table. And it had to be done for every single table in the migration.

The problem was given to me with this much information. No suggested approach, no template — just "these tables need to be matched." I had to figure out a solution from scratch.

### What made this hard

It's tempting to think this is a simple comparison problem. It's not. Here's why:

- **No direct access to the data.** The data was stored in mainframe format. You can't just open it and read the columns. You need the encoding information from the SAS source code to read it correctly.
- **Column names are meaningless for matching.** A column called `BEDRAG_BRUTO` on SAS might be `GROSS_AMOUNT` on Snowflake. Or it might be `PREMIUM_GROSS`. Or something else entirely. Name similarity gets you started but it doesn't get you there.
- **High column similarity.** Many columns had very similar data — think multiple date columns, multiple amount columns, multiple status codes. Any approach that relies on surface-level pattern matching would produce false positives constantly.
- **Scale.** This wasn't a one-time thing for a single table. It had to work across hundreds of tables with varying structures.

---

## The Approach

### Step 1: Getting the SAS Code

Before I could do anything, I needed to actually read the data. It was stored in mainframe format, and reading it correctly requires knowing the encoding — which is defined in the SAS source code.

Problem: we didn't have the SAS code easily accessible.

So the very first thing I built was a SAS crawler. It went through the server directories, followed the path structures, and extracted the source code from over 1,000 SAS files. This gave me the encoding information and table definitions I needed to read the mainframe data correctly.

### Step 2: Extracting Metadata with AI

SAS code is not the friendliest thing to parse programmatically. The encoding definitions, column formats, data step logic — it's all embedded in a proprietary syntax that varies across files.

Instead of writing a brittle SAS parser, I used a GPT-4.1 API call. I fed each SAS source file to the model and asked it to extract the specific metadata I needed: encoding, column names, data types, formats. The model was genuinely good at this — parsing structured-but-messy code and pulling out the relevant pieces is a sweet spot for LLMs.

With that metadata in hand, I could finally read the mainframe data correctly.

### Step 3: Sampling — Why 100 Rows

I extracted 100 rows from each SAS table. Not 10, not 1,000 — 100.

The reasoning: you need enough rows that each column has diverse values. If you only take 10 rows, you might get a column where every value is the same (think a status column that's all "OPEN" in a small sample). That makes matching impossible — you can't distinguish columns when they all look identical.

But you also can't take too many. Every row means more processing time, more API cost, more data to move around. At 100 rows, you get enough diversity to tell columns apart without making the pipeline slow.

I sampled across the full history of the data, not just the first 100 rows. Early rows tend to have patterns that don't represent the full dataset — defaults, test data, initialization values.

### Step 4: AI-Assisted Column Candidate Detection

This is where the AI came in for the matching itself — but with clear boundaries.

I took 10 rows from SAS and 10 rows from Snowflake and used another GPT-4.1 call to detect the most likely column matches. The model looked at column names and sample values together and produced a ranked list of candidates.

**Why only 10 rows for this step?** Because I was sending this to an API. Token costs and context limits matter. 10 rows is enough for the AI to get the general pattern without blowing up the request.

**Why not use AI for the full matching?** Because we had a lot of columns with high similarity. Multiple amount columns, multiple date columns, multiple ID columns. The AI would get confused — it would match `RESERVE_AMT` to `GROSS_AMOUNT` because they're both numeric with similar ranges. For columns like these, you need exact value-level comparison, not pattern recognition.

So the use case of AI was limited to the part where it was reasonable: getting a first round of likely candidates. The heavy lifting came after.

### Step 5: Finding Exact Rows on Snowflake

This was the key step that made everything else work.

With the candidate column matches from the AI, I now had a rough idea of which SAS columns mapped to which Snowflake columns. Using those candidate mappings, I could construct a Snowflake query that searched for the exact row matching the SAS data.

Think of it like this: if the AI suggested that SAS column `POLNR` matches Snowflake column `POLICY_NUMBER`, and SAS column `SCHADE_DT` matches Snowflake column `DAMAGE_DATE`, I could write:

```sql
SELECT *
FROM snowflake_table
WHERE POLICY_NUMBER = 'NL-2019-44821'
  AND DAMAGE_DATE = '2019-03-15'
```

If that query returns a row, I now have the exact same record on both sides. No ambiguity. No guessing. I can compare every single column value directly.

I did this for all 100 sampled SAS rows, pulling their exact matches from Snowflake. Now I had 100 aligned row pairs — same record, both systems.

### Step 6: The Matching Algorithm

With 100 aligned rows from both sides, the matching became a straightforward data engineering problem.

For each SAS column, compare its 100 values against every Snowflake column's 100 values. If the values match consistently (accounting for type differences, rounding, and encoding), that's your match.

This is where the 100-row sample paid off. With enough rows, the false positive rate drops to nearly zero. Two columns might accidentally match on 5 rows, but they won't match on 90+ out of 100 unless they're actually the same data.

The algorithm scored each potential pair and applied thresholds — a high-confidence match needed 95%+ row agreement. Anything below that got flagged for human review rather than auto-confirmed.

### Step 7: Output

The pipeline generated an Excel file for each table containing:

- **Matched columns** — SAS column, Snowflake column, match confidence, number of matching rows
- **Extra SAS columns** — columns that exist on SAS but have no match on Snowflake
- **Extra Snowflake columns** — the reverse
- **Sample data from both sides** — the actual values used for matching, so anyone reviewing the output could verify the logic themselves

This was important. The output wasn't just "column A = column B, trust me." It showed the evidence. That made it easy for the team to review, challenge, and build confidence in the results.

---

## The Result

The pipeline automated the entire manual process. What used to take a senior developer **more than a day per table** now ran in **minutes**.

The overall column match accuracy was around **93%**. Several tables hit 100%. The remaining ~7% of mismatches weren't pipeline errors — they were upstream data quality issues. Values that were supposed to be the same across systems but weren't. Columns where the SAS data had been transformed in ways that weren't documented anywhere.

The pipeline actually surfaced these issues correctly. When it couldn't match a column, it flagged it with a low confidence score instead of forcing a wrong match. That's exactly what you want — the tool should tell you where the problems are, not hide them.

The whole thing was built in **less than two weeks**. Most of the code was written with Claude. The architecture design — figuring out the step-by-step approach and where each tool fits — took about a day. The rest was implementation and iteration.

---

## What I Learned

### Know where AI helps and where it doesn't

This project could have been a disaster if I'd tried to make AI do everything. The instinct is "throw it at GPT and see what comes out." That works for a demo. It doesn't work when you have 50 columns with similar numeric values and need to tell them apart.

AI was genuinely great at two things here: parsing messy SAS code to extract metadata, and making initial column guesses from names and small samples. It was bad at precise column matching across highly similar data. So I used it where it was strong and wrote deterministic code where it wasn't.

That boundary — knowing when to use AI and when to use regular engineering — is the actual skill. Not prompt engineering. Not API chaining. The judgment of where each tool belongs.

### Architecture beats code

I didn't write much code that was individually impressive. A crawler, some API calls, a SQL query builder, a matching algorithm, an Excel exporter. Each piece was simple.

What made the pipeline work was the architecture — the decision to chain these steps in this specific order, where each step's output is exactly what the next step needs as input. Getting that design right took one day. Writing the code took the rest of the two weeks. But the one day of design is what made the two weeks productive instead of wasted.

### 100 rows is a magic number (for this problem)

I didn't start with 100. I tried 10 first — too many false positives, columns that looked like matches but weren't. I tried 500 — too slow, and didn't meaningfully improve accuracy over 100. The sweet spot was obvious once I tested it, but I wouldn't have found it without testing.

The general lesson: sample sizes for data comparison aren't something you reason about in the abstract. You test them. The right number depends on the data diversity and the column similarity in your specific dataset.

### The 93% was more interesting than 100% would have been

If the pipeline had returned 100% match accuracy, I would have been suspicious. Real data has real problems. The fact that 7% of columns didn't match — and that this turned out to be genuine data quality issues — actually validated the approach.

A tool that always says "everything is fine" is useless. A tool that says "here's what matches, here's what doesn't, and here's the evidence" — that's useful. The flagged mismatches led to investigations that uncovered real upstream issues that would have caused problems later in the migration anyway.

### Build with AI, not around AI

Most of the code was written with Claude. Not because I couldn't write it myself, but because the implementation speed let me iterate on the architecture faster. I could test an approach, see it fail, redesign, and rebuild in hours instead of days.

This changed how I think about engineering. The bottleneck isn't writing code anymore. It's designing the right system. When implementation is fast, you can afford to experiment with the architecture — try things, throw them away, try something else. That's a fundamentally different way of working.

---

*Tags: LLM API chaining · SAS · Snowflake · Data validation · Python · Automation · AI-assisted development · Prompt engineering · OpenAI API · Parity testing*
