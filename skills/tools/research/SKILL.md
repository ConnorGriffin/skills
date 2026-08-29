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

Use the provider-neutral hosted-source capability defined by the selected
adapter's dispatch reference on every read-only research `start`, with one
coordinator-owned state file under the coordinator's session-scratch directory.
The selected adapter's `resume`, `stop`, and `verify` surfaces retain lifecycle
ownership. Do not restate provider argv here.

After selection, this interface does not reclassify research work or choose a
model or effort. Preserve adapter-owned state and coordinator-owned recovery
through the orchestrate adapter contract; do not restate its command or
lifecycle mechanics here.

Before dispatch, the coordinator writes the exact complete research-task prompt
bytes to an immutable session-scratch file and passes that file's contents as
the selected adapter's positional prompt. The worker receives no chat transcript
or other coordinator-session material. The prompt requires the worker to return
a final message beginning `SOURCE_ACCESS_UNAVAILABLE:` when hosted search or
fetch is refused, and to write no findings document in that case.

Only when that start completed with a terminal, resumable session and its final
message begins with the exact `SOURCE_ACCESS_UNAVAILABLE:` prefix may the
coordinator fetch the required public sources. Create a unique
`.research-sources.*` directory under the worker cwd, store only fetched public
unauthenticated source files plus `manifest.md` mapping each file to its source
URL, and resume the same worker with the manifest's absolute path. This bounded
handoff is the sole narrow exception to the original-prompt-only rule and takes
precedence over it. The directory is removed after completion.

If the adapter leaves no resumable session or the coordinator cannot obtain the
required primary sources, stop explicitly and write no successful findings
document. Never put transcripts, credentials, secrets, `.env`, patient data,
authenticated or private source material, or unrelated coordinator-session
content in the handoff.

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
