# Design

## A ticket stays whole however many pull requests land it

**Context.** Triage's slicing rule filed child issues whenever two slicing traits
fired, and `multiple targets` plus `multiple deliverables` fire on almost any
cross-repo change. UI Craft separately required a build ticket after every lock.
The operator rejected the split each time, and agents worked around it by posting
one lock per pull request on the original ticket.

**Decision.** The workaround becomes the rule. Work that needs more than one pull
request gets a pieces checklist on its ticket and a lock for every piece, each
bounded by its own `Expected diff`. The slicing traits still decide
when work needs sequencing and are still recorded for finalize's cost record.
Child issues are filed only on the operator's request.

**Consequences.** `start` and `revise` still build one lock to one pull request.
Finalize runs once per piece and closes the ticket only after the last box is
checked. The tracker shows one ticket per unit of work, with its pull
requests listed on it.

## Triage locks every piece in one pass

**Context.** Locking only the first piece left the operator facing a fresh triage
and approval round after every merge, and left later pieces unplanned while the
context that shaped them was in hand.

**Decision.** Triage grounds, drafts, reviews, and posts an order for every piece in
one pass, approved once. Each order carries `Piece:` and `Waits on:`. Each piece gets
its own branch and, in an OpenSpec repo, its own change. Start takes the first
unchecked piece, refuses it while what it waits on is unmerged, and merges the
default branch into the piece branch (never rebases) so the pin stays an ancestor.
A piece whose outcome waits on a spike is the one order deferred.

**Consequences.** Locate returns every order and the verb picks by piece. An earlier
piece's merge can stale a later order; start refuses it and triage re-pins it
without a new approval when only the pin moved. Triage cuts one worktree per piece
up front.
