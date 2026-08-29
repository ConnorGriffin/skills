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

- Constrain triage writes to the current ticket's worktree and tracker state.
- Require explicit operator authorization before triage creates or requires an
  ancillary branch, commit, push, pull request, or tracker item.
- When a parent amendment is genuinely prerequisite, stop before mutation and
  present the proposed amendment for authorization; otherwise keep triaging and
  carry compatible decisions in the current ticket's work order.
- Pin the authority boundary through the ticket skill's public prose contract and
  behavior tests.

## Capabilities

### Modified capabilities

- `ticket-workflow`: triage gains an explicit ancillary-mutation authority boundary.

## Impact

The change affects the ticket driver's shared pipeline, triage procedure, and
contract tests. It does not alter Epic ownership of parent planning artifacts,
OpenSpec adoption for repositories that lack OpenSpec, or cleanup of PR #237's
closed branch.
