# Design

## ADR 239 — Triage writes stay inside the selected ticket

`/ticket triage <id>` may read the selected ticket's parent, linked work, live
state, and repository records to ground a correct order. Without explicit operator
authorization, its repository and tracker mutations are limited to the selected
ticket's branch and worktree, its active change record, and its tracker comment and
status. This boundary does not suppress ticket-scoped lifecycle telemetry or local
tooling state required by the workflow, including the session claim and the exact
Codebase Memory worktree index.

The active-change allowance applies only to an ordinary ticket. An Epic child keeps
the existing work-order-only exception: its parent owns the active change, and the
child neither writes nor treats that parent record as its selected-ticket change.

An inferred prerequisite in another ticket or planning record does not itself
grant authority to create a branch, commit, push, pull request, or tracker item for
that prerequisite. An external correction is genuinely prerequisite only when a
work order without it would contradict a recorded destination, constraint,
acceptance criterion, risk, or sequence in the selected ticket or its governing
parent. Triage cites that conflicting clause, names the exact ancillary target and
mutation, and stops before mutation. Only the operator's response to that disclosure
authorizes the ancillary work; invoking triage on the selected ticket does not.

When no such contradiction exists, the current ticket can carry the implementation
decision: triage continues and records it in the current work order instead of
manufacturing a prerequisite.

### Consequences

Epic parents remain the durable planning authority and child branches still carry
no parent planning artifact. The workflow loses its automatic "land a separate
docs-only pull request" path; cross-ticket repair becomes an explicit scope expansion
rather than an implementation detail of triage.

This is a prose-contract boundary, not a parser or runtime policy engine. Regression
tests exercise the installed skill text as the ticket driver's public interface and
preserve its existing telemetry and Codebase Memory lifecycle.
