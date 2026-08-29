## ADDED Requirements

### Requirement: Epic dispatch remains human-operated

An epic coordinator MUST maintain the active OpenSpec plan, record decisions,
file bounded children, and write a draft order into each child issue without
dispatching workers, running ticket verbs, posting the executable work-order lock,
or opening pull requests. The operator MUST invoke ticket triage to ground and
independently review the draft before it becomes the fenced lock, and MUST explicitly
invoke each later child ticket phase that proceeds to attended work.

#### Scenario: A child work order is ready

- **WHEN** the epic has settled a child's decisions and written its draft order in the issue
- **THEN** the coordinator stops for the operator to invoke ticket triage instead of posting the lock or invoking a worker adapter

### Requirement: Epic slicing defaults to three or fewer children

An epic MUST default to no more than three child tickets. Before creating a fourth
or later child, the coordinator MUST record a justification in the active change's
`design.md` that explains why fewer, larger independently shippable builds do not fit.

#### Scenario: A proposed epic has four child tickets

- **WHEN** the coordinator cannot consolidate the proposed work into three independently shippable children
- **THEN** it records the capability boundary or dependency that requires the additional child before filing it

### Requirement: Epic planning artifacts ship with implementation

An epic coordinator MUST NOT open a pull request containing only epic planning
artifacts. When ticket triage requires a parent-plan amendment, it MUST commit that
amendment in the child's ticket worktree and the resulting planning updates MUST
travel with the implementation pull request that realizes them.

#### Scenario: Planning changes are ready but implementation has not run

- **WHEN** the epic's planning artifacts have changed and no child implementation is ready
- **THEN** the coordinator keeps the change active and waits rather than opening a planning-only pull request
