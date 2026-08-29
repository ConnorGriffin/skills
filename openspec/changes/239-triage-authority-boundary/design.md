# Design

## ADR 239 — Triage writes stay inside the selected ticket

`/ticket triage <id>` may read the selected ticket's parent, linked work, live
state, and repository records to ground a correct order. Without explicit operator
authorization, its writes are limited by ownership and purpose rather than an
exhaustive list of today's mechanisms. Operator-local state that the installed
workflow requires to execute the selected lifecycle may be initialized, updated,
and read; this includes claims, exact-worktree Codebase Memory state, reviewer
memory, and local remote-tracking refs used to verify the ticket base. Repository
and tracker writes may affect only the selected ticket's branch, worktree, active
change when ordinary, comment, and status, plus the defined Epic-child parent-plan
amendment carried by that child's implementation pull request.

The boundary does not authorize a new independently addressable concern. Creating
or mutating another branch, pull request, issue, ticket, repository artifact outside
the selected branch, or equivalent external work remains ancillary even when
triage believes it would help. This distinction survives additions to the
operator-local workflow without silently broadening repository or tracker authority.

The selected-ticket active-change allowance applies directly only to an ordinary
ticket. An Epic child creates no per-child change record and never claims its
parent's active change as its own. Under the current Epic contract, however, a
required amendment to that parent-owned plan may be committed in the selected
child's worktree and travel with the child's implementation pull request. That is
selected-ticket lifecycle work, not ancillary work in another branch, pull request,
or tracker item.

An inferred prerequisite in another ticket or planning record does not itself
grant authority to create a branch, commit, push, pull request, or tracker item for
that prerequisite. An external correction is genuinely prerequisite only when a
work order without it would contradict a recorded destination, constraint,
acceptance criterion, risk, or sequence in the selected ticket or its governing
parent. Triage cites that conflicting clause, names the exact ancillary target and
mutation, and stops before mutation. Only an operator response that explicitly
authorizes the previously disclosed target and exact mutation authorizes the
ancillary work; invoking triage on the selected ticket or merely acknowledging the
disclosure does not.

When no such contradiction exists, the current ticket can carry the implementation
decision: triage continues and records it in the current work order instead of
manufacturing a prerequisite.

### Consequences

Epic parents remain the durable planning authority, and a child may carry only the
parent-plan amendment required by its selected-ticket implementation. The workflow
loses its automatic "land a separate docs-only pull request" path; unrelated
cross-ticket repair becomes an explicit scope expansion rather than an implementation
detail of triage.

This is a prose-contract boundary, not a parser or runtime policy engine. Regression
tests exercise the installed skill text as the ticket driver's public interface and
preserve its existing telemetry, Codebase Memory, reviewer-memory, and Epic-child
lifecycles.
