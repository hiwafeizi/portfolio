# How a Recursive Function Unblocked 10+ Developers at Allianz

**May 2026**

---

There were thousands of SAS scripts in production. 10+ developers needed to read them. The official viewer was clunky, getting access took weeks, and grep didn't exist.

A recursive function fixed it.

## Thousands of scripts, ten developers, one viewer

I work as a data engineer at Allianz. We've been migrating a large SAS-based reporting system to dbt and Snowflake. Part of the migration is reading the existing SAS programs to understand what they do, so the new dbt models can produce equivalent output.

Thousands of `.sas` files across deeply nested folders. 10+ developers needed to read them.

## Permissions, then a viewer with no search

Reading those scripts wasn't as simple as opening a file.

The scripts lived in production folders that required individual permission grants. Every developer had to file an access request, get approved, and wait. Multiply by 10+ developers and that's weeks of slow approval cycles before anyone can read anything.

Once the permissions came through, developers couldn't open the files in their normal IDE. They had to use a special viewer program. The viewer was clunky. No search. Limited copy. No way to grep across files.

So even after permissions cleared, every "let me check how this SAS program handles X" took several minutes of friction. For 10+ developers checking dozens of scripts each per week, the productivity tax was real.

## The bottleneck wasn't technical

The files existed. The filesystem was reachable from within Allianz's network with the access I had. **The friction was institutional** — the permissions process for the official viewer, the limitations of the viewer itself, the fact that engineers had to use a tool that wasn't their normal environment.

So the right move wasn't to fight the permissions process. It was to read the files once, extract them into our team's space, and give everyone instant access through tools they already used.

## Walk the tree, dump the JSON, rebuild the structure

I had Claude write a small Python script. Two parts.

Part one walks the folder tree and extracts every `.sas` file with its path. Simplified:

```python
import os
import json

def crawl(directory):
    results = []
    for entry in os.scandir(directory):
        if entry.is_file() and entry.name.endswith('.sas'):
            with open(entry.path, 'r', encoding='latin-1') as f:
                results.append({
                    'path': entry.path,
                    'content': f.read()
                })
        elif entry.is_dir():
            results.extend(crawl(entry.path))
    return results

scripts = crawl('/path/to/sas/root')

with open('sas_scripts.json', 'w') as f:
    json.dump(scripts, f, indent=2)
```

The conceptual core is just recursion. Open a folder. Read the SAS files. Found another folder inside? Do the same thing. Keep going until there's nothing left.

Part two reads the JSON and rebuilds the same folder structure inside our team's Git repo, dropping each `.sas` file at its corresponding path. Now every script lives in our repo at the same logical location it has in production, but as a plain `.sas` file in a normal directory.

## VS Code, Git, no tickets

10+ developers reading SAS scripts in VS Code. Full search. Full Git history. No permission tickets. No clunky viewer.

**Productivity tax: gone.** The whole thing took a few hours. Recursion is the tool everyone learns in week one and forgets they have.
