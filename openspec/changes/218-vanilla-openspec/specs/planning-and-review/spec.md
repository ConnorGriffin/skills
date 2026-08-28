# Planning and review routing — deltas

## REMOVED Requirements

### Requirement: Epic authority and labels

**Reason**: Replaced by `Epic OpenSpec authority`. The derived ledger this
requirement reconciled against live tracker state no longer exists, so its
ledger-disagreement scenario has no subject.

### Requirement: Epic planning lifecycle

**Reason**: Replaced by `Epic lifecycle without a ledger`. The sole-ledger-writer
duty, standing draft planning pull request, and ledger-based close-out were
removed with the ledger.

## ADDED Requirements

### Requirement: Epic OpenSpec authority

An Epic MUST use its OpenSpec proposal, design, and tasks as the durable
destination, scope, risk, decision, and implementation-sequence authority:
`tasks.md` links every tracker child issue in checked implementation order.
Native tracker children remain its work units under the independent `epic`,
`spike`, `build`, and `deferred` type labels, and live tracker state MUST be
authoritative for child type, status, dependencies, deferral, and closing pull
requests. The Epic MUST NOT maintain a derived ledger or other parallel index
of tracker state.

#### Scenario: Planning state is read in a fresh session

- **WHEN** an Epic home session resumes and needs current planning and child
  state
- **THEN** it reads the active change's proposal, design, and tasks for durable
  planning and live tracker state for child work state, with no derived ledger
  to reconcile

### Requirement: Epic lifecycle without a ledger

The Epic home session MUST keep the active change coherent from planning
altitude without a dedicated planning worktree or standing planning pull
request. Imprecise concerns MUST be kept as named open questions in the
change's `design.md`, cleared only by recording a decision there or promoting
the question to a tracker spike, and a build MUST NOT be admitted while an open
spike or named open question can invalidate its outcome, constraints, or
acceptance criteria. Completion MUST be verified from live child and merge
state, after which close-out follows the repository's archive guidance for the
active change.

#### Scenario: An imprecise concern arrives during planning

- **WHEN** the home session captures a concern too imprecise to ticket
- **THEN** it records a named open question in `design.md` and clears it only
  through a recorded decision or a promoted spike, never by silent deletion

#### Scenario: An Epic is ready for close-out

- **WHEN** no spike child is open, every build child is merged or closed not
  planned, and no open deferred child remains
- **THEN** the home session verifies those predicates from live tracker state,
  follows the repository's archive guidance for the active change after the
  human-merged work is verified, and closes the Epic issue
