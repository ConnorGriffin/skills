# Live Codex worker identity before completion

## Why

The Codex adapter buffers worker output until exit, so its durable state can report a
running process with no session identifier even after Codex has created a session and
is actively writing a rollout. Current coordinator guidance can therefore mistake live
model work for a pre-session hang and terminate it.

## What changes

- Persist the exact Codex session identifier from the worker's streamed
  `thread.started` event while the worker remains active.
- Define an empty session identifier during `running` as indeterminate and require
  exact-session rollout non-progress evidence before stopping a silent worker.
- Cover the live state transition through the adapter CLI and keep Claude adapter
  behavior unchanged through the shared lifecycle seam.

## Risk contract

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
