## MODIFIED Requirements

### Requirement: Bounded worker-egress consent

A literal invocation of ticket `triage`, `start`, or `revise` MUST authorize the
work order or task prompt plus only the repository code, documentation, and UI
fidelity evidence rendered from manufactured or synthetic fixtures needed for
every mandatory dispatch that verb routes, including review and orchestration.
Evidence rendered from real user, production, or patient data MUST remain outside
the grant, whether or not a capture is tracked in the repository. Every
coordinator reviewer-dispatch step MUST restate that granted payload where the
dispatch decision is made, so the coordinator does not re-ask for consent the
invocation already gave. Automatic activation outside an invoked parent MUST ask
once on the same terms, while `finalize` MUST grant no worker-egress consent. This
declaration MUST NOT override platform approval policy, adapter isolation, or
prompt handling. When a coordinator delegates ticket work, its prompt MUST
identify the mandatory-review handoff. The worker MUST return or write its
review-ready result through the coordinator-recorded durable result locator at
that boundary. The coordinator MUST collect that result, dispatch every mandatory
reviewer, and resume that same worker with either verified findings for correction
or a verified clean verdict to finish. Unavailable review evidence MUST block the
workflow from advancing as reviewed. The worker MUST NOT launch a nested reviewer.

#### Scenario: Start reaches mandatory independent review

- **WHEN** a user literally invokes `/ticket start` and the order reaches its
  required review step
- **THEN** the workflow may dispatch the bounded review through the pack adapter
  without asking again solely for worker-egress consent

#### Scenario: Fidelity screenshots accompany a reviewer dispatch

- **WHEN** a coordinator holds UI fidelity screenshots rendered from manufactured
  or synthetic fixtures and reaches a mandatory reviewer dispatch
- **THEN** it sends them under the invocation's existing grant instead of halting
  to re-ask, and the exclusions stay in force

#### Scenario: Evidence comes from real data

- **WHEN** the evidence a dispatch would carry was rendered from real user,
  production, or patient data
- **THEN** the grant does not cover it and the transfer is not authorized by the
  invocation alone

#### Scenario: Delegated start reaches mandatory independent review

- **WHEN** a delegated `/ticket start` worker returns implementation ready for its required review
- **THEN** its coordinator dispatches the bounded review through the pack adapter and resumes the same worker with actionable findings or a verified clean verdict

#### Scenario: Delegated review evidence is unavailable

- **WHEN** a delegated ticket review has a failed launch, nonzero exit, missing result artifact, or missing verdict
- **THEN** the coordinator reports the review as unavailable and does not advance the workflow as reviewed
