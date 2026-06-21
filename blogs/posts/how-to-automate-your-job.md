# How to automate your job (still employed btw)

**June 2026**

---

**TL;DR.** I automated my own job on purpose. The speed is fine, but the real win is that knowledge which used to live in a few people's heads is now in a prompt anyone on the team can run. Don't bother with full automation, that's usually not worth it. Just replace yourself where the cost makes sense. The next work is more interesting.

---

I've been replacing myself with AI on purpose.

There is always more work to do and the new work is usually more interesting. I learn more that way too. The other thing that happens is the knowledge stops living only in my head. Once it's in a prompt, anyone on the team can run it.

Here's the story of how I did that for one of the most repetitive tasks I had: adding new sources.

If you don't know me yet, I hate doing manual work that can be automated. So I tried to automate this task. Patiently, no jumping straight to writing prompts.

The task had different sub-tasks: checking the CSV, finding the column names, finding the file structure and the format we should use in the model for extracting, writing 3 SQL files (one table, two views) and one YAML with all the descriptions needed for the load. On top of that, `dbt run` and checking the data on Snowflake. Of course, debugging at the end if there was an issue.

The first time I did this task I gave the CSV headers to Copilot and asked it to create the YAML and SQL files. There was some back and forth about the file format, and I got errors for different reasons. Which was actually good, because I learned where my issues were.

So in the instructions I asked the model to retrieve the first 10 rows and extract the information it needed to create the files. The formats we had were all provided with exact names, so no searching for the format name either. Another fix that happened here was processing big files of 20GB or more. If you are not technical enough to use script, finding the format inside those files would be hell.

While creating the SQL and YAML files, I was seeing outputs that didn't match the style I wanted. I noted that down too. (Honestly, I am not a writing person, so style was on my mind.) I was also seeing issues with the path it was saving the files to, another point to fix.

So I added an example of how the files should be structured and proper instructions on how to create them. The file path was also explained, so no future issues there.

I also didn't like writing the dbt commands manually, especially when I was adding 6 sources at once across 2 environments. So I instructed Copilot to give me the right dbt commands.

In our setup, `dbt run` can't parse correctly before a full run, so we needed a `dbt parse` command beforehand. That detail was either known to only a few people or buried in documentation. By baking it into the prompt, everyone on the team could now add new models without running into that issue.

That's the part that actually changed things. Not the speed. The fact that knowledge which used to live in a few people's heads is now in the prompt, and anyone on the team can run it.

The next step, checking the data on Snowflake, got the same treatment. I told Copilot the database, the schema, and how to write the validation queries, so it could produce the queries to run. For debugging, we had different loggings, internal logic, and processes that a new person on the project would have no idea about. All of that went into the instructions: the flow, the debugging approach, and where to look first.

What used to be estimated 8 hours, Copilot could replace most of in a few minutes. The validation was also reduced to minutes, and even when there was an issue I could add the new source in under an hour.

## Could I make it fully automated?

Yes. But sometimes the time you spend automating a task outweighs the time of just doing it. Adding Snowflake API access, extra testing, making sure the API is safe and not misused, would take much more effort than simply checking Snowflake manually.

If full automation was needed, a separate platform designed to handle every task with proper security and tests would be a better option.
