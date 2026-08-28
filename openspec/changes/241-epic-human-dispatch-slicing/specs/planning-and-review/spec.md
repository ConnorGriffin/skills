## ADDED Requirements

### Requirement: Epic dispatch remains human-operated

An epic coordinator MUST maintain the active OpenSpec plan, record decisions,
file bounded children, and write child work orders without dispatching workers,
running ticket verbs, or opening pull requests. The operator MUST explicitly invoke
each child ticket that proceeds to attended work.

#### Scenario: A child work order is ready

- **WHEN** the epic has settled a child's decisions and written its bounded work order
- **THEN** the coordinator stops for the operator instead of invoking the ticket or a worker adapter

### Requirement: Epic slicing defaults to three or fewer children

An epic MUST default to no more than three child tickets. Before creating a fourth
or later child, the coordinator MUST record a justification in the active change's
`design.md` that explains why fewer, larger independently shippable builds do not fit.

#### Scenario: A proposed epic has four child tickets

- **WHEN** the coordinator cannot consolidate the proposed work into three independently shippable children
- **THEN** it records the capability boundary or dependency that requires the additional child before filing it

### Requirement: Epic planning artifacts ship with implementation

An epic coordinator MUST NOT open a pull request containing only epic planning
artifacts. Applicable proposal, design, tasks, and delta-spec updates MUST travel
with an implementation pull request that realizes them.

#### Scenario: Planning changes are ready but implementation has not run

- **WHEN** the epic's planning artifacts have changed and no child implementation is ready
- **THEN** the coordinator keeps the change active and waits rather than opening a planning-only pull request
