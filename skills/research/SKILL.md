---
name: research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
---

Use exactly one research worker; never create a chain of workers.

- **Root or interactive agent:** Spawn one background agent with this skill and the
  complete research task attached. You may keep working while it reads, but supervise it
  to completion before ending the turn or reporting the research complete.
- **Already a spawned, background, or subagent worker:** Perform the research directly.
  Never spawn another background agent or nested worker.
- If the worker fails or is interrupted, report the failure explicitly. Do not describe a
  successful spawn as completed research.

The research worker's job:

1. Investigate the question against **primary sources** — official docs, source code,
   specs, first-party APIs — not a secondary write-up of them. Follow every claim back to
   the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it where the repo already keeps such notes; match the existing convention, and if
   there is none, put it somewhere sensible and say where.
