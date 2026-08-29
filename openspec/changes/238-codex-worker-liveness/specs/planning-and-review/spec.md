## ADDED Requirements

### Requirement: Durable Codex worker liveness identity

The Codex worker adapter MUST persist the exact launched session's authoritative
identifier while that session is running, and orchestration MUST treat a running state
with an empty identifier as indeterminate. A coordinator MUST NOT stop the recorded
worker process group unless an identifier-matched rollout is absent or has failed to
progress across the documented observation window; PID presence, terminal silence,
parent-process CPU, and newest-rollout ordering MUST NOT independently or collectively
substitute for that exact match.

#### Scenario: Buffered worker remains active beyond the liveness window

- **WHEN** Codex emits its session-start event and continues working while terminal
  output remains buffered
- **THEN** the adapter state exposes that exact session identifier before completion
  and the coordinator uses its matching rollout progress as the liveness evidence

#### Scenario: Running state has no session identifier

- **WHEN** a worker state reports `running` with an empty session identifier
- **THEN** orchestration treats the state as indeterminate and does not terminate the
  recorded process group on silence, PID presence, CPU observations, or a guessed
  rollout
