# Proposal

## Why

Ticket triage can currently infer that an Epic parent needs a specification
amendment, create a separate branch and pull request for that amendment, and stop
the ticket it was asked to triage. Issue #239 records that behavior through closed
PR #237: the operator did not authorize the ancillary pull request, and issue #228
could carry the relevant decisions in its own work order without that prerequisite.

Triage needs an explicit mutation boundary so repository-wide grounding remains
broad while writes stay confined to the ticket the operator selected.

## What changes

- Constrain ancillary repository and tracker writes to the current ticket's
  lifecycle while preserving required local telemetry and tooling state.
- Require explicit operator authorization before triage creates or requires an
  ancillary branch, commit, push, pull request, or tracker item.
- Treat an external amendment as a prerequisite only when the current order would
  contradict a recorded destination, constraint, acceptance criterion, risk, or
  sequence; otherwise keep triaging and carry compatible decisions in the current
  ticket's work order.
- Require authorization to follow disclosure of the exact ancillary target and
  mutation; the original triage invocation does not authorize it.
- Pin the authority boundary through the ticket skill's public prose contract and
  behavior tests.

## Capabilities

### Modified capabilities

- `ticket-workflow`: triage gains an explicit ancillary-mutation authority boundary.

## Impact

The change affects the ticket driver's shared pipeline, triage procedure, and
contract tests. It does not alter Epic ownership of parent planning artifacts,
ticket session claims, Codebase Memory indexing, OpenSpec adoption for repositories
that lack OpenSpec, or cleanup of PR #237's closed branch.
