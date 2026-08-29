# Ticket workflow — deltas

## MODIFIED Requirements

### Requirement: Bounded worker-egress consent

A literal invocation of ticket `triage`, `start`, or `revise` MUST authorize the
work order or task prompt plus only the repository code and documentation needed
for every mandatory dispatch that verb routes, including review and orchestration.
Automatic activation outside an invoked parent MUST ask once on the same terms,
while `finalize` MUST grant no worker-egress consent. This declaration MUST NOT
override platform approval policy, adapter isolation, or prompt handling. When a
coordinator delegates ticket work, its prompt MUST identify the mandatory-review
handoff. The worker MUST return or write its review-ready result through the
coordinator-recorded durable result locator at that boundary. The coordinator MUST
collect that result, dispatch every mandatory reviewer, and resume that same worker
with either verified findings for correction or a verified clean verdict to finish.
Unavailable review evidence MUST block the workflow from advancing as reviewed. The
worker MUST NOT launch a nested reviewer.

#### Scenario: Start reaches mandatory independent review

- **WHEN** a user literally invokes `/ticket start` and the order reaches its
  required review step
- **THEN** the workflow may dispatch the bounded review through the pack adapter
  without asking again solely for worker-egress consent

#### Scenario: Delegated start reaches mandatory independent review

- **WHEN** a delegated `/ticket start` worker returns implementation ready for its required review
- **THEN** its coordinator dispatches the bounded review through the pack adapter and resumes the same worker with actionable findings or a verified clean verdict

#### Scenario: Delegated review evidence is unavailable

- **WHEN** a delegated ticket review has a failed launch, nonzero exit, missing result artifact, or missing verdict
- **THEN** the coordinator reports the review as unavailable and does not advance the workflow as reviewed
