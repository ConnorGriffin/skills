## REMOVED Requirements

### Requirement: Bounded worker-egress consent

**Reason**: Reversed by ADR 275. Codex worker sessions read the consent
declaration and stopped mid-workflow to re-ask permission for a review the
operator had already ordered, and rewording the declaration did not stop it.
The pack now carries no worker-egress consent declaration; the coordinator-
owned mandatory-review handoff this requirement also stated survives under
`Coordinator-owned review handoff`.

## ADDED Requirements

### Requirement: Coordinator-owned review handoff

When a coordinator delegates ticket work, its prompt MUST identify the
mandatory-review handoff. The worker MUST return or write its review-ready
result through the coordinator-recorded durable result locator at that
boundary. The coordinator MUST collect that result, dispatch every mandatory
reviewer, and resume that same worker with either verified findings for
correction or a verified clean verdict to finish. Unavailable review evidence
MUST block the workflow from advancing as reviewed. The worker MUST NOT
launch a nested reviewer.

#### Scenario: Delegated start reaches mandatory independent review

- **WHEN** a delegated `/ticket start` worker returns implementation ready for its required review
- **THEN** its coordinator dispatches the bounded review through the pack adapter and resumes the same worker with actionable findings or a verified clean verdict

#### Scenario: Delegated review evidence is unavailable

- **WHEN** a delegated ticket review has a failed launch, nonzero exit, missing result artifact, or missing verdict
- **THEN** the coordinator reports the review as unavailable and does not advance the workflow as reviewed
