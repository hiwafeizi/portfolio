# No Docs, Just Data: Automating Documentation Across 80 Multilingual Files

**May 2026**

---

## TL;DR

At enterprise scale, data documentation lives across PDFs, Word documents, Excel files, and PowerPoints, in multiple languages, with embedded images and charts. Consolidating that into structured, queryable documentation that audit, business, data analysts, data scientists, and governance can all use is impractical manually at this scale. I built a pipeline that translates, parses, extracts charts, cross-references against the live Snowflake schema, and outputs Excel ready for our internal documentation platform, with AI assumptions clearly separated from verified facts and every claim traceable back to its source. Documentation produced for 70 tables from 80 source files. Same code now powering rollout across 700+ more source tables.

---

## What I Was Working With

80 source documents for a single source system. PDF, Word (.doc and .docx), Excel, PowerPoint. Some contained images. Some contained embedded charts. Three languages (Dutch, French, English) split across the pile rather than mixed inside any one document.

The cardinality was the part most off-the-shelf documentation tools assume away:

- One PowerPoint described 20 tables.
- One table was described across one PowerPoint, one Excel, and one Word file.

There was no 1:1 mapping between documents and tables. Doing this manually meant a person fluent in all three languages, with Snowflake access, with the patience to read charts inside PowerPoints, opening every doc and reconciling it against the live warehouse. Roughly a day per table.

Multiply that by hundreds of tables and the math stops working.

## The Pipeline

### Step 1: Translate, then take inventory

Everything got translated into a single common language up front. Reasoning in three languages is harder, more expensive, and lower quality than translating first and reasoning cleanly afterward.

Alongside the translation pass, the pipeline produced statistics about the document pile itself: file type counts, page lengths, language distribution, average size per format. The point wasn't visualization. The point was visibility before processing: what's in the pile, what's small, what's big, where the long tail of edge cases probably lives.

Each document was also scanned at this stage for embedded images, and the ones containing them got flagged so the next step knew where to spend its image-reading budget.

### Step 2: Read images, structure charts

Some documents, especially PowerPoints, embedded their most important information in images and charts. A diagram showing data flow. A table rendered as an image stuck inside a slide. A bar chart describing source-system breakdown.

Image content went through the OpenAI API. That part was straightforward.

Charts were harder. A chart picked up as a flat image description loses the data behind it. You get "a bar chart showing values across categories" instead of the actual values. So I built a second pass: when a chart was detected, the pipeline asked the model to return its contents as structured JSON: categories, values, axis labels, units. That gave downstream steps actual numbers to work with instead of prose about a picture.

### Step 3: Build a per-table view across sources

After parsing, the pipeline didn't try to reason about tables directly from raw documents. Instead it ran a two-stage consolidation that turned the messy doc-to-table relationship into a clean per-table view.

*Stage A.* For each document, an LLM pass identified every table name in the document and produced a per-table JSON containing whatever the document said about each. A single PowerPoint describing 10 tables contributed 10 separate JSON entries, one per table.

*Stage B.* A Python pass then walked over every per-table JSON across every document and merged them by table name. If three different files (a PowerPoint, an Excel, and a Word document) all referenced the same table, their three JSONs got combined into one consolidated entry for that table.

That's how the cardinality got solved. One PowerPoint describing 20 tables produced 20 entries that each found their way into the right table's combined view. One table described across three different documents ended up with all three contributions stitched into a single record. The pipeline didn't need to know in advance which case it was dealing with; the two-stage structure handled both directions.

### Step 4: Pull Snowflake as the system of record

For each table in scope, the pipeline pulled the live schema from Snowflake via its API: columns, types, sample values. This is the one authoritative source in the system. Everything else is "what some document claimed at some point in the past."

That distinction sets up the rest of the pipeline. Documents are inputs to be interpreted. Snowflake is ground truth.

### Step 5: Match documents to tables

Once each document was translated, parsed, and had its images and charts structured, the pipeline tried to associate it with the right table (or set of tables) by matching column names mentioned in the document against the columns in the Snowflake schema.

When names matched, full comparison ran. When they didn't, the pipeline kept whatever was reconcilable and let the unmatchable parts go. Documents and live schemas drift over time, and that drift is expected at enterprise scale. The job wasn't to force a match. It was to extract what was actually grounded in the live data.

### Step 6: Inferred meaning, kept separate

For each table, the pipeline first pulled every column name from Snowflake, then sent the column list together with the relevant documents to the LLM in a single prompt. The prompt asked for two things at once: a description of the table's purpose, and a description of each column's purpose.

Doing this in one combined prompt-response was the design choice that made the output usable. Column names alone often don't tell you much. Documents alone don't always cover every column. But name plus document together, in the same prompt, let the model use the table's overall context to make sense of individual columns, and let column patterns sharpen the model's understanding of the table.

Concrete (imagined) example: a column called `STAT_CD` in a table whose documents describe the claims lifecycle. The name `STAT_CD` alone could mean almost anything. But in the context of a claims-lifecycle table, the model infers "status code tracking the claim's current phase." That inference then gets tested with a second prompt: the model predicts the likely values of `STAT_CD`, which the pipeline compares against the actual values pulled from Snowflake (`OPEN`, `IN_REVIEW`, `CLOSED`). When the prediction matches the data, the assumption is reinforced. When it doesn't, it's flagged.

Keeping AI assumptions separate from verified facts wasn't a post-processing step. The per-table JSON built in Step 3 already had distinct sections for verified facts and inferred meaning, and Step 6 simply filled the inferred section. The Excel output preserved that separation, with explicit warnings that the inferred section was AI-generated and that the model can be wrong.

## One design decision: JSON at every step

Every step in the pipeline wrote JSON: inputs and outputs of every transformation.

This wasn't elegant, it was just enough. When a claim showed up in the final Excel and someone asked "where did this come from?", the answer was a few JSON hops: claim, then prompt, then source document, then location in the pile. When the pipeline produced something that looked wrong, the failure could be traced top-down to the exact step and source.

This wasn't a step added at the end. It was the backbone the pipeline was designed around. Two-stage table consolidation worked because every prior step's output was structured the same way. Provenance everywhere meant debugging took minutes, not hours.

## Reconciliation with the Live Warehouse

A pattern that emerged across most documents: what the document claimed and what Snowflake actually contained didn't always line up perfectly. Slightly different column counts. Slightly different names. A column that existed in the doc but not in the warehouse, or vice versa.

This is normal. Schemas evolve, documents get written at specific points in time, releases ship, columns get added and renamed. At any large organization the live schema will move faster than any document store can keep up with.

The pipeline didn't try to hide this. Wherever the document and Snowflake agreed, the documentation used the document's wording. Wherever they didn't, Snowflake won and the disagreement was flagged. The output became a snapshot of where the documents and the warehouse currently aligned, not a forced reconciliation that papers over real drift.

## The Output

A single Excel file per source, shaped to match the import format of our internal documentation platform.

Inside each file:

- **Verified facts**, extracted from documents and confirmed against Snowflake.
- **AI assumptions**, in a separate section, explicitly labelled, with warnings.
- **Source references** on every claim, pointing back to the originating document.

The structure was the design. Anyone reading the output knew immediately which entries were grounded in source documents, which were inferred by an LLM, and where to look to verify either.

The final output then went through one more multilingual pass. After the English consolidation, every entry was translated back into Dutch and French, and the three language versions sat side by side in the same Excel: one row per claim, three languages, one consolidated document. The pipeline went in multilingual, normalized to a single working language, and came back out multilingual.

## The Result

Documentation produced for 70 tables, drawing from 80 source documents.

Manual baseline (a person fluent in three languages, with Snowflake access, interpreting embedded charts) was about a day per table. The pipeline did the equivalent work in minutes.

The whole thing was built end-to-end in about 10 days, with Copilot as the day-to-day implementation pair.

More importantly: the same code now powers the rollout to 700+ additional source tables. The first 70 tables weren't the deliverable. They were the proof. The reusable pipeline is the deliverable.

## Governance still owns the final word

The AI assumptions weren't the final word. They were a first pass for governance to verify in person. Every inferred fact came with its source reference and a warning label, making it auditable rather than authoritative. The pipeline reduced the manual load; human review at the end kept the standard where it needed to be.

That's the design that made it work. If the AI output had been treated as final documentation, no one would have trusted it, and they would have been right not to. By framing it as a structured first pass with full traceability, it became something governance could verify efficiently instead of producing from scratch.

## What I Learned

### Next step: documentation lives in the dbt model

Excel is fine as a deliverable. It's not fine as a system. The moment a schema shifts, the Excel goes stale and someone has to rerun the pipeline. The right second iteration of this project is putting the descriptions, owners, and notes directly into the dbt model definitions, so when a column gets added or renamed, the documentation moves with it. The pipeline I built was the bootstrap. dbt is where the docs should actually live.

### I love JSON

I underestimated how much I'd come to love JSON in this project. Every step writes JSON and reads JSON. When something looks wrong in the final Excel, I open one file and the answer is right there. When I wanted to rewire two steps, the only thing that mattered was that the JSON shape held. For a pipeline like this, JSON is the format that just keeps paying off: easy to write, easy to read, easy to debug.

---

*Tags: Python · OpenAI API · Document parsing · Multilingual · Translation · Computer vision · Snowflake · Snowflake API · Data governance · Data quality · Automation · AI-assisted development · Prompt engineering · LLM API chaining · JSON · Excel*
