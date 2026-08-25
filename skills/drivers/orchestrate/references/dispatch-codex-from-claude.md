# Claude Code parent dispatching a Codex worker

Use this reference only when the interactive coordinator is a Claude Code
parent dispatching a **Codex** worker for review. `dispatch-codex.md` remains
Codex-UI-parent-only and is unchanged by this document. This document adds no
route and no gate of its own — it composes the existing Codex headroom gate
in `SKILL.md` with the existing Code review row in `references/routing-table.md`.

## Admission procedure

a. **Run the presence-and-headroom gate first, before any Codex spend.** The
   gate — `command -v codex`, then a fresh Luna probe, dropping every Codex
   route on absent / unknown / ≤5% / rate-limited — is defined once in
   `SKILL.md`'s "Codex headroom gate" section. Cite it here; this document does
   not restate its thresholds as independent prose.
b. **With usable headroom, dispatch routine code review as Luna**
   (`gpt-5.6-luna`) with `--sandbox read-only` through `codex-worker.py start`,
   persisting one state file for that worker. Review is a read task, so
   `workspace-write` is never correct for it — that is a rule, not an example.
c. **Retry a failed routine review once in the same worker session** via
   `codex-worker.py resume` against that state file, carrying the specific
   finding. State is preserved for the retry; do not start a second worker for
   it. When that retry also fails, escalate one tier per the Code review row's
   escalation column (Luna → Sonnet → Opus) — SKILL.md's "Verification and
   escalation" item 2 for a Claude parent. Item 3's `NO_VALIDATED_ROUTE` stop
   and its "never escalate Terra, Luna, or Sol to Sonnet or Opus" ban are
   Codex-UI-parent rules and do not apply here.
d. **Route load-bearing or safety review to Claude Opus directly**, per the
   Code review row. It is never a Codex worker on this path, and Opus is top
   of ladder — there is nothing above it to escalate to.
e. **On Codex absent, unknown headroom, headroom at or below 5%, or a
   rate-limited probe or delegation, enter the Claude-only branch SKILL.md
   already defines:** routine review begins at Sonnet and escalates to Opus;
   load-bearing review stays Opus. Make no second Codex attempt for the rest
   of the session.

## Infrastructure failure vs. model-quality failure

A worker that failed to launch, hung before session start, lost its rollout,
or was refused for headroom is a dispatch failure, matching the rule
`dispatch-codex.md` already states. It is not evidence that Luna reviewed
badly, so it consumes neither the one same-session retry in step c above nor
an escalation rung. See `dispatch-codex.md`'s "Worker liveness" and
"Interrupted workers" sections for the shared mechanics — they are not
duplicated here. The launching coordinator owns stop-then-verify before any
successor touches the worktree.

## Boundary

This document does not cover dispatching a **Claude** worker; use
[`dispatch-claude.md`](dispatch-claude.md) for that adapter.
