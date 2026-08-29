# ticket-workflow Delta

## ADDED Requirements

### Requirement: Triage mutation authority

Ticket triage MUST confine writes by ownership and purpose. It MAY initialize,
update, and read operator-local state that the installed workflow requires to
execute the selected ticket lifecycle. Repository and tracker writes MUST remain in
the selected ticket's worktree and branch, an ordinary ticket's active change, and
the selected ticket's comment and status, except for the defined Epic-child
parent-plan amendment carried by that child's implementation pull request.

Creating or mutating state for a distinct concern outside that selected lifecycle
MUST require explicit operator authorization to the previously disclosed external
target and exact mutation. Reading a parent, linked ticket, live service, or
repository record for grounding MUST NOT grant authority to create or change a
separate branch, commit, push, pull request, tracker item, or repository artifact
for that external concern. A newly added operator-local workflow mechanism MUST NOT
be misclassified as ancillary solely because an older order did not enumerate it.

The selected-ticket active change allowance MUST apply directly only to an ordinary
ticket. An Epic child MUST create no per-child change record and MUST NOT claim its
parent's active change as its own. A parent-plan amendment required by the selected
child's implementation MAY be committed in that child's worktree and travel with its
implementation pull request under parent ownership; this MUST count as selected-ticket
lifecycle work rather than ancillary work.

An external amendment MUST be treated as a prerequisite only when omitting it would
make the current order contradict a recorded destination, constraint, acceptance
criterion, risk, or sequence in the selected ticket or its governing parent. Triage
MUST cite that clause, name the exact ancillary target and mutation, stop before the
mutation, and accept authorization only from an operator response that explicitly
authorizes the previously disclosed target and exact mutation. Acknowledgment alone
and the original triage invocation MUST NOT count as that authorization.
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
  that previously disclosed target and exact mutation

#### Scenario: Required operator-local workflow state is written

- **WHEN** the installed triage workflow requires a claim, exact-worktree Codebase
  Memory state, reviewer-memory state, or local ref refresh to execute the selected
  lifecycle
- **THEN** that operator-local workflow state proceeds without ancillary-work
  approval and does not authorize a distinct repository or tracker concern

#### Scenario: An Epic child carries a required parent-plan amendment

- **WHEN** the selected ticket is a confirmed Epic child and its implementation
  requires an amendment to the pinned parent plan
- **THEN** triage may commit that amendment in the child worktree for the child's
  implementation pull request, creates no per-child change record, and leaves
  ownership and archive responsibility with the parent
