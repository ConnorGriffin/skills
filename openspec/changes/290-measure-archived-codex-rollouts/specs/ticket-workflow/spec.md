## ADDED Requirements

### Requirement: Codex rollout discovery includes active and archived sessions

Ticket telemetry MUST resolve an exact claimed Codex session from every distinct
matching rollout under both the active `sessions` root and the completed-task
`archived_sessions` root. `scan` and `record` MUST use the maximum context peak
across all of those matches. A claimed Codex session MUST be unreadable only when
neither root contains an exact matching rollout. This discovery change MUST NOT
alter Claude transcript discovery, session attribution, rollout parsing, or
verdict thresholds.

#### Scenario: A Codex rollout remains active

- **WHEN** a claimed Codex session has an exact matching rollout only under the
  active root
- **THEN** `scan` and `record` measure that rollout as before

#### Scenario: A Codex rollout was archived

- **WHEN** a claimed Codex session has an exact matching rollout only under the
  archived root
- **THEN** `scan` and `record` measure the session instead of reporting it
  unreadable

#### Scenario: A resumed session spans both roots

- **WHEN** distinct exact matching rollouts for one claimed Codex session exist
  under the active and archived roots
- **THEN** discovery returns every distinct rollout and `scan` and `record`
  report the maximum context peak across them

#### Scenario: No matching rollout exists

- **WHEN** neither root contains an exact matching rollout for a claimed Codex
  session
- **THEN** the existing visible unreadable and `unmeasurable` behavior is
  preserved
