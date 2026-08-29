## ADDED Requirements

### Requirement: Epic child triage carries required parent-plan amendments

An epic child's ticket triage MUST treat the issue body's epic-authored order as a
draft, ground and independently review it through the ordinary triage procedure,
fetch the named parent-plan branch as `origin/<branch name>`, and require that branch to resolve to the
full commit pinned in the draft before cutting the child worktree from that branch.
It MUST post the resulting fenced work order as the only execution lock. When the draft
requires an amendment to the parent epic's active OpenSpec change, triage MUST commit
that amendment in the child's ticket worktree and continue; it MUST NOT open or
require a separate planning-only pull request.

#### Scenario: A child draft requires a parent design clarification

- **WHEN** ticket triage verifies that the child cannot execute until the parent design is amended
- **THEN** it commits the amendment in the child worktree, includes it in the independently reviewed lock, and leaves it for the child's implementation pull request

#### Scenario: An epic-authored child draft is ready for locking

- **WHEN** the operator invokes ticket triage on an epic child whose issue contains a draft order and a parent-plan branch/commit pin
- **THEN** triage resolves the unprefixed branch name as `origin/<branch name>`, verifies it resolves to the pinned commit, passes the same unprefixed name to `--base`, and grounds and reviews the draft before posting the only fenced executable work order

#### Scenario: The pinned parent-plan branch advanced

- **WHEN** the fetched remote parent-plan branch no longer resolves to the commit pinned in the child draft
- **THEN** triage posts nothing and returns the stale draft to the attended epic session for refresh

### Requirement: Epic child implementation preserves the parent archive owner

An epic child MAY carry updates to its parent's active OpenSpec change when those
updates are required by that child's implementation. It MUST NOT create a per-child
change record or archive the parent change; the parent epic remains the single change
authority and archive owner.

#### Scenario: A child pull request carries its parent-plan amendment

- **WHEN** the child's implementation is ready after triage amended the parent plan
- **THEN** the pull request includes that parent-plan amendment with the implementation and leaves the active change unarchived
