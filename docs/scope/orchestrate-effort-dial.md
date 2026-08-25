# Scope — universal effort dial and Claude CLI worker dispatch (#149)

Route: interview mode (a concrete plan exists in the operator's head, untested).

## Decisions

(appended as they settle)

## Open questions

1. Adapter surface — does `claude-worker.py` need `codex-worker.py`'s full lifecycle
   (start/resume/stop/verify, state files, liveness, group-scoped recovery) or a thin
   start/resume?
2. Read-only enforcement for a headless `claude -p` worker — `--permission-mode plan`,
   `--tools`/`--disallowedTools`, or a measured probe before the contract is written.
3. Effort dial shape — a routing-table column (stamped rows change only via benchmark
   replay) or a coordinator override with the current default preserved.
4. Ban breadth — Agent tool only, or Agent + Workflow + background agents; and whether
   the ban binds sub-skills that spawn Claude reviewers (`code-review`, `plan-review`).
5. Sequencing against #144/#145, which queue edits to the same orchestrate files.

## Spawned tasks

(none yet)
