---
name: research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a research worker.
---

## Research-worker dispatch

Use exactly one research worker; never create a chain of workers.

The coordinator supplies the selected adapter, explicit research-worker model,
explicit research-worker effort, and the complete research task. Dispatch only
through `skills/drivers/orchestrate/scripts/codex-worker.py` or
`skills/drivers/orchestrate/scripts/claude-worker.py`, using the selected
adapter's read-only surface. Never use the built-in Agent tool, Workflow tool,
or background-agent machinery.

Use the selected adapter's `start` surface with one coordinator-owned state file
under the coordinator's session-scratch directory. The selected adapter's
`resume`, `stop`, and `verify` surfaces retain lifecycle ownership.

After selection, this interface does not reclassify research work or choose a
model or effort. Preserve adapter-owned state and coordinator-owned recovery
through the orchestrate adapter contract; do not restate its command or
lifecycle mechanics here.

Before dispatch, the coordinator writes the exact complete research-task prompt
bytes to an immutable session-scratch file and passes that file's contents as
the selected adapter's positional prompt. The worker receives no chat transcript
or other coordinator-session material.

The worker performs the research directly and returns source-cited findings to
the coordinator. Never spawn another background agent or nested worker. If the
worker fails or is interrupted, report the failure explicitly. Do not describe a
successful dispatch as completed research. The coordinator writes the returned
findings to the single Markdown file required below.

## The research worker's job

1. Investigate the question against **primary sources** — official docs, source code,
   specs, first-party APIs — not a secondary write-up of them. Follow every claim back to
   the source that owns it.
2. Return the findings to the coordinator, citing each claim's source.
3. The coordinator writes the returned findings to a single Markdown file. Save it where
   the repo already keeps such notes; match the existing convention, and if there is none,
   put it somewhere sensible and say where.
