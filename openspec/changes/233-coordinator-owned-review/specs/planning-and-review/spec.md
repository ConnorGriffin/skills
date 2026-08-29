# Planning and review routing — deltas

## MODIFIED Requirements

### Requirement: Orchestration authorization and isolation

Literal `/orchestrate` invocation MUST authorize only the work order or task
prompt plus the repository code and documentation needed for mandatory dispatches,
including review and orchestration. Automatic activation outside an invoked parent
MUST ask once before dispatch, and every dispatch MUST continue to use pack-owned
isolated adapters while excluding credentials, secrets, patient data, `.env`, and
real database contents. The coordinator MUST own every mandatory reviewer dispatch
reached by delegated work, return verified findings to the same worker, and treat a
missing reviewer result as unavailable rather than a clean verdict. Direct adapter
dispatch from inside a sandboxed worker is unsupported.

#### Scenario: Orchestration activates implicitly

- **WHEN** a workflow reaches orchestration without a literal invocation or an
  invoked parent that already grants bounded dispatch consent
- **THEN** it asks once with the payload, destination, and exclusions and stops if
  consent is denied

#### Scenario: Delegated work reaches mandatory review

- **WHEN** an Orchestrate worker returns work whose governing workflow requires independent review
- **THEN** the coordinator dispatches that reviewer through the existing adapter and resumes the same worker with actionable findings instead of asking the worker to launch a nested reviewer
