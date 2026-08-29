# Planning and review routing delta

## ADDED Requirements

### Requirement: Coordinator wait narration follows state changes

A coordinator governed by the shared communication contract MUST emit no update
for re-polled unchanged external state, result locators or files, result sets, or
elapsed time alone, including after three no-news batches. It MUST report worker
completion, worker failure, an abandoned wait, an operator-relevant external-state
or coordinator decision/action milestone declared before the wait, and any state
change the coordinator itself caused. A time interval alone MUST NOT qualify as a
milestone.

#### Scenario: A worker remains active across polls

- **WHEN** repeated checks find the same running state, result locator or files,
  or result set and no operator-relevant external-state or decision/action
  milestone has been crossed
- **THEN** the coordinator continues waiting without emitting a status update

#### Scenario: A wait reaches an outcome

- **WHEN** the worker completes or fails, or the coordinator abandons the wait
- **THEN** the coordinator reports that outcome immediately
