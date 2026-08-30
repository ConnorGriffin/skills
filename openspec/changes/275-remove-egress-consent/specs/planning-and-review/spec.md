## REMOVED Requirements

### Requirement: Orchestration authorization and isolation

**Reason**: Reversed by ADR 275. Codex worker sessions read the consent
declaration and stopped mid-workflow to re-ask permission for a review the
operator had already ordered, and rewording the declaration did not stop it.
The pack now carries no worker-egress consent declaration; adapter isolation
and the coordinator-owned mandatory-review handoff this requirement also
stated survive under `Orchestration isolation and review handoff`.

## ADDED Requirements

### Requirement: Orchestration isolation and review handoff

Every dispatch MUST continue to use pack-owned isolated adapters. The
coordinator MUST own every mandatory reviewer dispatch reached by delegated
work. Its delegation prompt MUST identify the mandatory-review handoff, and
the worker MUST return or write its review-ready result through the
coordinator-recorded durable result locator at that boundary. The coordinator
MUST collect that result and resume the same worker with verified findings
for correction or a verified clean verdict to finish. Unavailable review
evidence MUST block the workflow from advancing as reviewed. Direct adapter
dispatch from inside a sandboxed worker is unsupported.

#### Scenario: Delegated work reaches mandatory review

- **WHEN** an Orchestrate worker returns work whose governing workflow requires independent review
- **THEN** the coordinator dispatches that reviewer through the existing adapter and resumes the same worker with actionable findings or a verified clean verdict instead of asking the worker to launch a nested reviewer

#### Scenario: Delegated review evidence is unavailable

- **WHEN** the mandatory reviewer has a failed launch, nonzero exit, missing result artifact, or missing verdict
- **THEN** the coordinator reports the review as unavailable and does not advance the workflow as reviewed
