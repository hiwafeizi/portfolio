# We Migrated 600+ Tables to dbt. Here's How I Made Sure Nothing Broke.

**April 2026**

---

## TL;DR

We were migrating 600+ production tables to dbt and needed to prove every single one produced the same data as the original code. I built a dbt macro that runs automatically at the end of every pipeline execution, compares migrated models against their originals by source, and tells you exactly which rows differ and where they came from. Debugging went from hours to minutes.

---

## The Problem

When you migrate production pipelines to dbt, the hardest question isn't whether the models run. dbt will tell you that. The real question is whether they produce the same data as the original code.

At 600+ tables you can't manually verify each one. Spot checking gives you confidence in a sample, not in the system. And "it looks right" isn't an answer when the data feeds downstream reporting at a financial institution.

We needed something systematic. Automatic. Precise enough to tell us not just that something was wrong, but exactly which rows, from exactly which source.

So I built a dbt macro that runs automatically at the end of every pipeline execution and validates migrated models against their original counterparts without anyone having to think about it.

---

## The Approach

### Why not dbt audit_helper

audit_helper is a strong tool for interactive debugging. You suspect a specific model has an issue, you trigger it manually, you inspect the diff. It's a diagnostic instrument designed for targeted use.

It's not designed for systematic validation across hundreds of tables after every run. At our scale that would require a developer to manually trigger comparisons on every model they wanted to check. That's not a workflow, it's a full time job.

I needed validation embedded in pipeline execution itself. On run end, automatic, zero manual intervention required.

### The filtering layer

Before any comparison runs, the macro filters aggressively. It only validates models that:

**Completed successfully.** A failed model already has a known problem. Validating it adds noise, not signal.

**Produced at least one row.** A model that succeeded but returned zero rows is a different category of problem. Comparing zero against production gives you either a false match or a false alarm.

**Belong to a source that produced new data in this run.** If a source didn't deliver new data, there's nothing new to validate. More on this below.

Each filter is an early exit. The macro only reaches the expensive comparison logic when there's actual data worth validating.

### Stage 1: Row count

A `COUNT(*)` is cheap. If the migrated model and the original produce the same number of rows, I move to hashing. If not, I already know something is wrong and flag it immediately.

### Stage 2: Hash of hashes

Rather than comparing every row individually, I hash each row then compare an aggregate of those hashes. If the aggregates match, the tables are identical. No further work needed.

Only when the aggregate differs do I go deeper to identify the specific rows that differ on each side. This means for the majority of tables (the ones that are correct) the validation cost is a count and a hash comparison. The expensive row level diffing only happens when there's actually something wrong.

### Source level separation

This is the decision that made debugging actually fast.

Many of our tables are fed by multiple raw sources. Testing the whole table at once tells you something is wrong somewhere. That's not enough information to debug efficiently.

By separating validation by raw source, a failure immediately tells you which incoming data caused the discrepancy. You don't investigate the entire table's history. You investigate the specific source that produced the anomaly.

It also keeps compute proportional to what actually ran. If 10 sources feed a table but only 3 produced new data in this run, I validate 3. The other 7 haven't changed so there's nothing to check.

---

## The Result

Results land in two tables:

**A summary table.** One row per model per run. Green or not green. This is what you check routinely to confirm everything migrated correctly.

**A detail table.** The specific rows that exist in one side but not the other, for both directions. This is what you open when something fails. The debugging starts at the exact row, from the exact source, in seconds rather than hours.

Before this existed: "something is wrong with this table, begin investigation."

After: "source X produced these specific rows differently from the original. Here they are."

That's the difference between debugging that takes hours and debugging that takes minutes. At 600+ tables migrating incrementally, that compression of debugging time is what made the migration actually tractable.

The macro runs automatically. Nobody has to remember to check anything. Every successful run either produces a clean validation or tells you exactly what to fix.

---

## What I Learned

### Validation that requires human action doesn't scale

It sounds obvious. But the temptation to lean on tools like audit_helper, where a developer manually runs a check when they suspect something, is real. When you have a handful of tables, manual checks feel fine. At 600+ tables with daily runs, anything that requires someone to remember to do something is a reliability gap. The validation system itself has to be as automatic as the pipeline it validates.

### Filtering is not optimization, it's correctness

The filtering layer wasn't about performance. It was about making the results meaningful. Without it, you get noise. Failed models flagged as mismatches. Empty tables producing false alarms. Sources that didn't run generating irrelevant comparisons. Every false signal erodes trust in the system. People stop looking at the results. The filters ensured that every flag in the output represented a real discrepancy worth investigating.

### Source level granularity changes the debugging workflow

When a table has 20 sources and something is wrong, you can spend an afternoon narrowing it down. When the system tells you "source 7 has 14 rows that differ," you start your investigation at the answer instead of the question. This wasn't a nice to have. It was the difference between a migration that moves at the speed of debugging and one that moves at the speed of development.

### Two stage comparison is worth the engineering

It would have been simpler to just hash everything and compare. But row counts are nearly free, and they catch a large category of problems (inserts, deletes, filter logic changes) before you spend compute on hashing. The hash of hashes approach then handles the content comparison efficiently. Only the actual failures trigger expensive row level diffing. At 600+ tables running daily, that cost discipline adds up.

### Embed validation in the pipeline, not beside it

A separate validation step that runs after the pipeline, or on a schedule, or when someone remembers, will eventually drift. By running validation in `on-run-end`, it's structurally impossible for a pipeline run to complete without being validated. The validation is not a follow up task. It's part of the pipeline definition. That structural guarantee is worth more than any amount of process documentation.

---

*Tags: dbt · Snowflake · Data validation · Parity testing · SQL · Data quality · Automation · Metadata automation*
