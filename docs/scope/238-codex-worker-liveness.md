# 238 Codex worker liveness

## Decisions

- Persist the Codex `thread.started` identifier from the exact worker's stdout while
  that process is still running; do not infer identity from the newest rollout file.
  Why: the event is authoritative, worker-bound, and already part of the adapter's
  successful output contract. Disposition: → ADR.
- Keep `session_id: ""` valid while `lifecycle: "running"`, but define that pair as
  indeterminate rather than evidence of pre-session failure. Why: the event may not
  have arrived yet, and current buffering proves silence is not absence. Disposition:
  inline.
- Require a session-ID-matched rollout to be absent or unchanged across the liveness
  observation window before the recorded process group may be stopped. If the state
  has no session ID, the probe cannot satisfy that precondition and must not classify
  the worker as hung. Why: termination destroys valid model work and cannot be based
  on PID presence, parent CPU, empty terminal output, or newest-file guesses.
  Disposition: → ADR.
- Preserve the shared lifecycle seam from ADR 150. The shared module owns concurrent
  stdout/stderr draining and atomic state mutation; the Codex adapter owns recognition
  of its `thread.started` event; Claude's transport and terminal parsing remain
  unchanged. Why: two adapters already make lifecycle ownership a real seam, while
  their output formats remain adapter-specific. Disposition: → ADR.

### Risk contract

- **Must prevent:** terminating a live worker whose matching rollout is progressing;
  secret exposure; irreversible loss of authoritative data; silent incorrect success.
- **Must recover:** a stopped or failed worker remains recoverable only through the
  adapter's existing state-bound `stop` then `verify` path before a successor uses its
  worktree.
- **Accepted failure:** a worker that never exposes a session ID remains indeterminate
  and requires manual investigation rather than automatic termination; the consequence
  is delayed recovery, not destroyed in-flight work.
- **Unsupported:** discovering workers not launched through the adapter, matching a
  rollout by newest-file order, or promising live session capture on the portable
  process-family path where scoped stop/verify is already unsupported.
- **Evidence owed:** a CLI-level buffered-worker regression that observes a non-empty
  session ID before completion and survives the shortened test liveness window; schema
  tests for both empty/indeterminate and populated/running state; exact-rollout progress
  guidance pinned by behavior tests; the full repository gate.

Why: worker termination is destructive to in-flight work, so false-positive safety is
the admission boundary. Disposition: inline.

## Open questions

None.

## Spawned tasks

None.

## Reproduction

`docs/scope/238-probes/buffered-session-id.py --expect empty` launches the public Codex adapter
against a fixture that flushes `thread.started` and then remains active. On the
pre-change implementation it observes `lifecycle: "running"` with an empty
`session_id`, despite the authoritative event already having been emitted.

## Review rounds

- Preflight: fixed two authoring defects before dispatch — the work order now carries
  the risk contract unchanged, and the operational liveness rule has one normative
  home.
- Persona fallback, round 1: three authoring blockers were reproduced. The draft's
  optional observer created a one-caller seam despite the existing shared `parse`
  interface; its fail-first step named no home for a demanded record; and the committed
  probe would fail deliberately after the implementation. The clean revision reuses
  `parse`, asks only that the failure be observed, and makes the probe's pre/post
  expectation explicit.
- Independent cold pass: blocked twice before session start. Each Terra adapter state
  remained `running` with an empty `session_id`; exact worktree/start-window scans found
  no rollout after more than the incident's 76-second boundary; both recorded process
  groups were stopped and verified through the adapter. No order has been posted.
