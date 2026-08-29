# ticket-workflow Delta

## ADDED Requirements

### Requirement: Triage mutation authority

Ticket triage MUST confine repository and tracker mutations to the selected
ticket's worktree, branch, active change record, comment, and status unless the
operator explicitly authorizes ancillary work. This boundary MUST preserve
ticket-scoped lifecycle telemetry and local tooling state required by the workflow,
including the session claim and the exact Codebase Memory worktree index. Reading a
parent, linked ticket, live service, or repository record for grounding MUST NOT
grant authority to create a branch, commit, push, pull request, or tracker item for
that external concern.

An external amendment MUST be treated as a prerequisite only when omitting it would
make the current order contradict a recorded destination, constraint, acceptance
criterion, risk, or sequence in the selected ticket or its governing parent. Triage
MUST cite that clause, name the exact ancillary target and mutation, stop before the
mutation, and accept authorization only from the operator's response to that
disclosure. The original triage invocation MUST NOT count as that authorization.
When no such contradiction exists, triage MUST continue and carry the implementation
decision in the selected ticket's work order.

#### Scenario: A compatible parent clarification appears during triage

- **WHEN** grounding finds a parent-planning clarification that the selected
  ticket's work order can carry without contradicting a recorded destination,
  constraint, acceptance criterion, risk, or sequence
- **THEN** triage records the decision in that order and does not create or require
  a separate branch, commit, push, pull request, or tracker item

#### Scenario: An external amendment is a true prerequisite

- **WHEN** a safe work order depends on changing a parent or other external
  authority first because the order would otherwise contradict one of its recorded
  destination, constraint, acceptance, risk, or sequencing clauses
- **THEN** triage cites the clause, names the exact target and mutation, stops before
  external mutation, and waits for an operator response that explicitly authorizes
  that disclosed work

#### Scenario: Required local lifecycle state is written

- **WHEN** triage claims its session or binds the ticket worktree's exact Codebase
  Memory identity
- **THEN** those ticket-scoped local writes proceed without ancillary-work approval
