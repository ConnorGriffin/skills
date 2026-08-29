# Planning and review routing — deltas

## MODIFIED Requirements

### Requirement: Orchestration authorization and isolation

Literal `/orchestrate` invocation MUST authorize only the work order or task
prompt plus the repository code and documentation needed for mandatory dispatches,
including review and orchestration. Automatic activation outside an invoked parent
MUST ask once before dispatch, and every dispatch MUST continue to use pack-owned
isolated adapters while excluding credentials, secrets, patient data, `.env`, and
real database contents. The coordinator MUST own every mandatory reviewer dispatch
reached by delegated work. Its delegation prompt MUST identify the mandatory-review
handoff, and the worker MUST return or write its review-ready result through the
coordinator-recorded durable result locator at that boundary. The coordinator MUST
collect that result and resume the same worker with verified findings for correction
or a verified clean verdict to finish. Unavailable review evidence MUST block the
workflow from advancing as reviewed. Direct adapter dispatch from inside a sandboxed
worker is unsupported.

#### Scenario: Orchestration activates implicitly

- **WHEN** a workflow reaches orchestration without a literal invocation or an
  invoked parent that already grants bounded dispatch consent
- **THEN** it asks once with the payload, destination, and exclusions and stops if
  consent is denied

#### Scenario: Delegated work reaches mandatory review

- **WHEN** an Orchestrate worker returns work whose governing workflow requires independent review
- **THEN** the coordinator dispatches that reviewer through the existing adapter and resumes the same worker with actionable findings or a verified clean verdict instead of asking the worker to launch a nested reviewer

#### Scenario: Delegated review evidence is unavailable

- **WHEN** the mandatory reviewer has a failed launch, nonzero exit, missing result artifact, or missing verdict
- **THEN** the coordinator reports the review as unavailable and does not advance the workflow as reviewed
