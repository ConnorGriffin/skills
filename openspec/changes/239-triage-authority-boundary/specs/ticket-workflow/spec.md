# ticket-workflow Delta

## ADDED Requirements

### Requirement: Triage mutation authority

Ticket triage MUST confine repository and tracker mutations to the selected
ticket's worktree, branch, active change record, comment, and status unless the
operator explicitly authorizes ancillary work. Reading a parent, linked ticket,
live service, or repository record for grounding MUST NOT grant authority to create
a branch, commit, push, pull request, tracker item, or other durable state for that
external concern. When an external amendment is genuinely required before a safe
work order can be stamped, triage MUST stop before that mutation and request
authorization with the proposed amendment; when the selected ticket can safely
carry the implementation decision, triage MUST continue without manufacturing an
ancillary prerequisite.

#### Scenario: A compatible parent clarification appears during triage

- **WHEN** grounding finds a parent-planning clarification that the selected
  ticket's work order can safely carry
- **THEN** triage records the decision in that order and does not create or require
  a separate branch, commit, push, pull request, or tracker item

#### Scenario: An external amendment is a true prerequisite

- **WHEN** a safe work order depends on changing a parent or other external
  authority first
- **THEN** triage stops before external mutation and asks the operator to authorize
  the proposed ancillary work
