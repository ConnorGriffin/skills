# Claude Code parent dispatching a Codex worker

Use this reference only when the interactive coordinator is a Claude Code
parent dispatching a **Codex** worker for review. `dispatch-codex.md` remains
Codex-UI-parent-only. This document adds no route or reviewer precedence of its
own.

## Review admission

Read [`review-routing.md`](review-routing.md) and apply its four-row matrix for
reviewer classification and initial adapter/model selection. That matrix
composes the selected review skill's area with `routing-table.md` and the Codex
presence/headroom gate in `SKILL.md`; this adapter reference does not duplicate
their precedence.

When the matrix selects Codex, dispatch the review read-only through
`codex-worker.py start` and persist one state file for that worker. Retry a
model-quality failure once through `codex-worker.py resume` against the same
state file, carrying the specific finding; do not start a second worker for the
retry. Review is a read task, so `workspace-write` is never correct for it.

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
