## ADDED Requirements

### Requirement: Slicing traits are optional record evidence

Finalization MUST be able to record a ticket whose work order fired no slicing
traits without inventing a sentinel trait. The public `record` command MUST emit
an empty `traits` array when no `--trait` flag is supplied. When one or more
`--trait` flags are supplied, it MUST preserve their values and order. Trait
presence MUST NOT alter verdict calculation, session attribution, or
reviewer-memory persistence.

#### Scenario: A flat order fired no slicing traits

- **WHEN** finalization invokes `record` without a `--trait` flag
- **THEN** the command succeeds and emits `"traits": []`

#### Scenario: An order fired multiple slicing traits

- **WHEN** finalization invokes `record` with multiple `--trait` flags
- **THEN** the command emits every supplied trait in the same order
