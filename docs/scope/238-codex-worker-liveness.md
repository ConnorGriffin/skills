# 238 Codex worker liveness

## Decision

This is a coordinator-guidance fix, not a worker-lifecycle project.

Codex worker output is buffered. When the adapter is still running but has produced no
terminal output or session ID, wait another minute and check again. Silence alone is
not evidence that the worker is hung, and it does not authorize stopping the process.

No production adapter code, state schema, session discovery, or rollout matching changes
belong in this ticket.

## Evidence

`docs/scope/238-probes/buffered-session-id.py --expect empty` demonstrates the condition:
the fixture has emitted its start event and remains active while the adapter's durable
state still has an empty session ID.

## Acceptance

- The Codex dispatch guidance explicitly tells coordinators to wait another minute when
  a running adapter is quiet.
- A behavior test pins that instruction so an agent cannot silently regress to the old
  hang inference.
- The repository gate passes.

## Review outcome

The initial triage over-scoped the ticket into live session capture and concurrency
machinery. The operator clarified that this is a single-user tool and the required fix
is the tested patience reminder above. That ruling replaces the earlier draft.
