# Design

## ADR 239 — Triage writes stay inside the selected ticket

`/ticket triage <id>` may read the selected ticket's parent, linked work, live
state, and repository records to ground a correct order. Without explicit operator
authorization, its mutations are limited to the selected ticket's branch and
worktree, its active change record, and its tracker comment and status.

An inferred prerequisite in another ticket or planning record does not itself
grant authority to create a branch, commit, push, pull request, tracker item, or
other durable state for that prerequisite. If the correction is genuinely required
before a safe work order can be stamped, triage stops before mutation and asks the
operator to authorize the proposed ancillary work. If the current ticket can carry
the implementation decision safely, triage continues and records that decision in
the current work order instead of manufacturing a prerequisite.

### Consequences

Epic parents remain the durable planning authority and child branches still carry
no parent planning artifact. The workflow loses its automatic "land a separate
docs-only pull request" path; cross-ticket repair becomes an explicit scope expansion
rather than an implementation detail of triage.

This is a prose-contract boundary, not a parser or runtime policy engine. Regression
tests exercise the installed skill text as the ticket driver's public interface.
