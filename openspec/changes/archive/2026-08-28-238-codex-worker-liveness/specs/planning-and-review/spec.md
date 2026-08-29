## ADDED Requirements

### Requirement: Patient Codex worker liveness checks

When a Codex adapter remains running without terminal output or a session identifier,
the coordinator MUST wait another minute and check again. Silence, an empty session
identifier, PID presence, or low parent-process CPU MUST NOT by itself be treated as a
hang or authority to stop the worker.

The repository MUST contain a behavior test that pins this agent-facing instruction.

#### Scenario: Running adapter is quiet

- **WHEN** the Codex adapter is still running and has not emitted terminal output or a
  session identifier
- **THEN** the coordinator waits another minute before checking again and does not stop
  the worker based on silence alone

#### Scenario: Guidance regresses

- **WHEN** the patience instruction is removed or weakened
- **THEN** the behavior test fails
