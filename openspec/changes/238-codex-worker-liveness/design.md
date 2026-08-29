# Design

## ADR 238 — Stream authoritative Codex session identity into shared worker state

Codex session identity comes from the exact launched worker's `thread.started` JSONL
event, observed while stdout and stderr are drained without waiting for process exit.
The shared lifecycle module owns safe concurrent draining and atomic mutation of the
existing state file. It reuses the existing adapter-supplied `parse` interface against
complete accumulated stdout records: Codex's parser already returns its recognized ID
alongside the expected partial-output error, while Claude's parser returns no ID until
its one terminal object is complete. No new callback seam, state field, or state-version
bump is needed: `session_id` changes from empty to the captured ID while lifecycle
remains `running`, and terminal parsing/emission continues to validate the complete
buffered output at exit.

This preserves ADR 150's seam. Claude continues to use the same shared lifecycle with
no live-event recognizer, and adapter-specific output parsing remains outside the shared
module. The portable path remains terminal-only because it deliberately has no
recoverable process-family claim.

Coordinator liveness is fail-safe: `running` plus an empty `session_id` is
indeterminate. A non-empty ID selects a rollout only by matching
`session_meta.payload.session_id`; newest-file ordering, terminal silence, PID
presence, and low parent CPU are not identity or hang evidence. The recorded process
group may be stopped only after the matching rollout is absent or fails to progress
across the documented observation window. An empty ID cannot satisfy that precondition.
