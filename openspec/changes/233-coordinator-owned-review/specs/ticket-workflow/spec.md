# Ticket workflow — deltas

## MODIFIED Requirements

### Requirement: Bounded worker-egress consent

A literal invocation of ticket `triage`, `start`, or `revise` MUST authorize the
work order or task prompt plus only the repository code and documentation needed
for every mandatory dispatch that verb routes, including review and orchestration.
Automatic activation outside an invoked parent MUST ask once on the same terms,
while `finalize` MUST grant no worker-egress consent. This declaration MUST NOT
override platform approval policy, adapter isolation, or prompt handling. When a
coordinator delegates ticket work, the coordinator MUST dispatch every mandatory
reviewer and return verified findings to the same worker; the worker MUST NOT launch
a nested reviewer.

#### Scenario: Start reaches mandatory independent review

- **WHEN** a user literally invokes `/ticket start` and the order reaches its
  required review step
- **THEN** the workflow may dispatch the bounded review through the pack adapter
  without asking again solely for worker-egress consent

#### Scenario: Delegated start reaches mandatory independent review

- **WHEN** a delegated `/ticket start` worker returns implementation ready for its required review
- **THEN** its coordinator dispatches the bounded review through the pack adapter, treats a missing verdict as unavailable rather than clean, and returns actionable findings to the same worker
