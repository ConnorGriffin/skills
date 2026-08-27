# Design

## ADR 214 — Epic's tracker seam mirrors ticket's, not a new shape

Epic's GitHub mechanics were a single reference page with no rebind point.
Rather than invent a different binding shape for epic, the seam mirrors
`ticket`'s layout exactly: a `references/tracker-contract.md` enumerating the
operations epic's verbs perform today, and `bindings/github-issues.md` as the
shipped default binding.

The contract's operation list is derived from what `epic/SKILL.md` already
does (create a native child, apply the four protocol labels, read children with
state/type/deferred/closing-PR merge state, file a review follow-up as a
native child), not expanded or spread. GitHub Issues stays the only binding
shipped; no binding-selection config is added, since epic has exactly one
consumer of the seam today (a future Jira binding, out of scope here).

### Consequences

* A future non-GitHub binding for epic has the same shape as a ticket binding
  and the same four-operation contract discipline.
* `ticket/references/review-actions.md`'s epic-child follow-up path now reads
  through the contract, so it does not need to change again if a second
  binding ships later.
* No behavior changes for the shipped default: same labels, same native
  structure, same completion checks.
