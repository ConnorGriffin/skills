# Scope — universal effort dial and Claude CLI worker dispatch (#149)

Route: interview mode (a concrete plan exists in the operator's head, untested).

## Decisions

* **Adapter surface: full parity.** `claude-worker.py` gets start/resume/stop/verify,
  one state file per worker, liveness, and group-scoped recovery, matching
  `codex-worker.py`. Why: the coordinator's recovery ownership rule in SKILL.md is
  written parent-agnostic, so a thin adapter would leave half the workers outside it.
  → issue

* **Read-only enforcement is measured, not assumed.** The contract is written around a
  mechanism proven to refuse a write in a probe run, not around a flag that reads
  right. Why: a benchmark run was already invalidated by a read-agent that wrote.
  → issue

* **Effort is a dial on both adapters.** `codex-worker.py` hard-codes
  `model_reasoning_effort=medium` today with no flag; both adapters take `--effort`.
  → issue

* **Effort defaults are per model, operator-set:** Opus medium, Sol medium, Terra high,
  Luna max. Why: operator ruling, 2026-08-24. These are not benchmark-derived — the
  2026-08-03 replay scored every Codex run at medium — so the table's provenance stamp
  must mark them operator-set and unbenchmarked. → ADR

* **All model dispatch defined by this pack's skills goes through this pack's
  adapters.** Not orchestrate-only: any skill that dispatches a model (code-review,
  plan-review, persona-review, ticket chunk agents, epic) dispatches through the
  adapters, never the built-in Agent tool, Workflow tool, or background agents.
  Why: operator ruling, 2026-08-24, superseding the narrower orchestrate-only option.
  → ADR

## Measured facts (this session, live)

* `claude` exposes `--effort low|medium|high|xhigh|max`, `--model`, `-p`,
  `--session-id`, `--resume`, `--permission-mode`, `--tools`, `--disallowedTools`,
  `--add-dir`, `--output-format json|stream-json`, `--max-budget-usd`.
* `--tools` and `--disallowedTools` are variadic: a trailing prompt argument is
  swallowed as a tool name. A worker adapter must pass the prompt on stdin or place it
  before those flags.
* `--permission-mode acceptEdits` still refused a new-file Write in `-p` mode.
* `--permission-mode plan` refused the write and wrote a plan file into
  `~/.claude/plans/` — a side effect outside the worker's cwd.
* Under `--permission-mode bypassPermissions`, a Haiku worker replied `DONE` while
  creating no file: a live instance of the SKILL.md warning to demand command output
  rather than trusting a reported success.

## Open questions

1. Effort defaults for the models not named in the ruling: Sonnet, Haiku, Spark, and
   the light-tier alternates.
2. Whether `--tools` / `--disallowedTools` survive a permissive `--permission-mode`
   (the read-only guarantee for write-capable dispatch) — probe blocked pending
   operator approval to run `bypassPermissions` locally.
3. Sequencing against #144 and #145, which queue edits to the same orchestrate files.
4. Shape: one flat order or chunked (adapter + tests, doc/ban rewrite, ADR).

## Spawned tasks

(none yet)
