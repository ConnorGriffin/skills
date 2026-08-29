# Quiet unchanged coordinator waits

## Why

The global communication contract requires a new-fact sentence after tool-result
batches, but it does not say that a fresh timestamp or a re-check of unchanged
worker state is still no news. Coordinators therefore narrate every poll while a
worker runs, burying the eventual outcome in status prose the operator does not
use.

## What changes

- Treat elapsed time and re-polled unchanged state as no new fact in every wait
  loop governed by the shared profile.
- Give ticket coordinator mode the same dispatch-specific silence rule while
  preserving immediate reports of completion, failure, abandonment,
  operator-relevant external-state or decision milestones, and
  coordinator-authored state changes. A time interval alone is not a milestone.
- Pin both instruction surfaces with the repository's existing normalized-prose
  test style; add no polling parser or runtime enforcement.

## Risk contract

- **Must prevent:** routine unchanged polls flooding the operator while also
  suppressing a worker failure, completion, abandoned wait, operator-relevant
  external-state or decision milestone, or state change the coordinator caused.
- **Must recover:** none; this is an instruction contract with no runtime state to
  repair.
- **Accepted failure:** an agent may still misread the prose and narrate an
  unchanged poll; the consequence is noisy output and a corrected wait loop.
- **Unsupported:** runtime enforcement, timer or milestone machinery, telemetry
  changes, and inference about worker health from elapsed time.
- **Evidence owed:** normalized prose pins for the global and ticket-specific
  rules, plus the repository's documented verification gate.
