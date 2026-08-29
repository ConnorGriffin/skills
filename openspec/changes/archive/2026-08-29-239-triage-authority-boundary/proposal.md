# Proposal

## Why

Ticket triage has no explicit boundary separating selected-ticket lifecycle writes
from unrelated repository and tracker mutations. Issue #239 records the resulting
authority failure through closed PR #237: triage created an unrequested ancillary
pull request and stopped issue #228, even though the selected ticket could carry the
relevant decision itself. Current Epic behavior has since replaced that separate
planning-only pull-request path with a parent-owned amendment carried by the
selected child's implementation pull request, but the authority boundary remains
unstated.

Triage needs an explicit mutation boundary so repository-wide grounding remains
broad while writes stay confined to the ticket the operator selected.

## What changes

- Define a stable mutation boundary: required operator-local workflow state and
  selected-ticket lifecycle artifacts remain in scope, while state for a distinct
  external concern requires separate authorization.
- Preserve the current Epic-child lifecycle: an Epic child creates no per-child
  change record, while a required amendment to the parent's active plan may travel
  in the selected child's worktree and implementation pull request under parent
  ownership.
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

The change affects the ticket driver's shared pipeline, triage procedure, active
change record, and contract tests. It does not alter Epic ownership of parent
planning artifacts, the current pinned-parent-plan handoff, ticket session claims,
Codebase Memory indexing, reviewer-memory behavior, OpenSpec adoption for
repositories that lack OpenSpec, or cleanup of PR #237's closed branch.
