# Design

## ADR 261 — One durable change specification, one thin execution lock

**Context.** A ticket in this repository accumulates three records of the same
work: the issue body, the change on the ticket branch, and the fenced work order
posted as a tracker comment. The change record is versioned, reviewable, and
already the thing a reviewer reads. The work order is a snapshot of it, written
so that a fresh `start` session with no memory of triage can execute from the
tracker alone.

That self-sufficiency is real and worth keeping: `start` must not have to guess
which plan revision it was authorized to build. But copying prose is only one way
to get it. A copy is self-sufficient at the instant it is posted and silently
wrong after the first amendment, because nothing compares the copy to its source.
The alternative is to make acquisition deterministic instead: name the source and
the exact bytes, and refuse when they cannot be reproduced.

**Decision.** The change record is the single authority for motivation,
requirements, decisions, tasks, exclusions, and observable acceptance. The
tracker comment shrinks to a versioned lock that authorizes execution: which
source at which full commit, which tasks and acceptance anchors are selected,
and the delivery policy — execution shape, session and dispatch fit,
verification and expectation, review depth and profile, the explicit expected
diff, and the stop-at-pull-request ceiling.

The lock is one envelope with three source modes rather than a format per
repository convention. `openspec` and `repository-native` both pin a path at a
full commit OID; `inline` carries today's Context/Do/Done-when payload as its
body, for a repository with no durable change record and for work too small to
warrant one. A consumer parses one grammar and branches on the mode.

Selection is positional — plain task and requirement numbers valid within the
pinned commit — because the pin freezes the bytes those numbers index. Inline
identifier markers would add a second syntax to the change record for the
benefit of a reader who already has the exact tree.

**Consequences.** Drift becomes detectable rather than invisible: a source
amended after the lock was posted no longer matches the pin, and execution
refuses instead of running the wrong plan. Amending a plan mid-flight now costs
a new lock, including during `revise`. That cost is the point — an amendment is
a re-authorization, and a single-operator flow can afford one tracker comment.

The lock cannot be smaller than its delivery policy. Verification, review depth,
expected diff, and chunk ownership are execution facts with no home in a change
record, and deriving the expected diff from the plan would let a plan edit widen
what a worker may touch. They stay explicit in the lock.

## ADR 261 — Execution admission fails closed

**Context.** The harm this redesign must prevent is executing a plan revision
nobody authorized. Every way that can happen is a way the pinned source fails to
resolve to the bytes the lock names: an unrecognized envelope version or source
mode, an abbreviated or unresolvable OID, a path absent at the pinned tree, a
change that has been archived or no longer validates, a selected task or
acceptance anchor that is not there, a ticket branch that does not contain the
pinned commit, or a later amendment with no newer lock.

**Decision.** `start` and `revise` resolve and validate the pinned source before
any implementation or worker dispatch, and every row of that matrix refuses with
a named message that routes to attended re-triage. None of them degrades: the
workflow never substitutes the branch head for the pin, never resolves a short
OID, and never treats a validation failure as a warning. Strict OpenSpec
validation runs at triage and again at `start`, because the checkout `start`
executes in is not the checkout triage authored in.

**Consequences.** A pinned commit must stay reachable, which merged history
gives for free; no expiry handling is built for a failure mode this flow cannot
reach. The accepted cost is a class of clean stops — a legitimate amendment made
without a new lock halts a session that could have guessed the intent. Guessing
is the thing being removed.

## ADR 261 — Legacy work orders never sunset

**Context.** Work orders already posted cannot be retrofitted with a pin: the
commit they were authored against may not correspond to any recorded state, and
rewriting a posted authorization would forge one. Tickets in flight carry them.

**Decision.** The locator recognizes both protocols and the newest recognized
lock wins, with no merging of fields across comments. A legacy `WORK ORDER`
comment continues to execute under today's sufficiency rules with no inferred
pin, indefinitely. Superseding one is done by posting a new-protocol lock, which
wins by being newer.

**Consequences.** Two admission paths coexist permanently, and both are pinned
by tests. The alternative — a migration deadline — would either strand in-flight
tickets or invite the retrofitting the risk contract rules out.

## ADR 261 — Worker payloads copy the lock and read the source

**Context.** An isolated worker receives a prompt and a checkout. The instinct
under a copied-prose order is to make the prompt self-contained by copying more,
which reproduces the drift problem one level down: the worker's snapshot and the
branch's plan are two authorities again.

**Decision.** A worker prompt and `ORDER.md` copy the complete lock or
stand-alone sub-lock, the exact worktree, branch, and graph identity, the
verified source pin, the selected identifiers, the verification command and its
expectation, the expected-diff allowlist and ownership boundaries, and any
ephemeral verified facts. Everything durable — the OpenSpec artifacts,
repository-native plans, UI contracts, and repository rules — is referenced from
the verified checkout and read there. `ORDER.md` is an uncommitted transport
copy and never a second authority. A worker that cannot read the pinned source
stops and reports rather than continuing from memory.

**Consequences.** Worker prompts get shorter and the checkout becomes load
bearing, so a dispatch into a checkout without the pinned source now fails
loudly at first read instead of producing plausible work against a remembered
plan.

## ADR 261 — A ticket owns its whole change; only an epic child selects

**Context.** A lock names which of the pinned source's tasks and acceptance
anchors it authorizes. That selection could default to a subset — the fence
enumerating exactly what this ticket builds — which reads naturally for a small
change carved out of a larger plan.

**Decision.** An ordinary ticket's change belongs to that ticket alone, so its
lock selects the whole change and the selection reads `all`. Only an epic child
selects a subset, because there the change is the parent epic's and several
children draw from it. When an ordinary ticket is chunked, the header lock still
reads `all` and its sub-locks partition that whole selection into disjoint
subsets that together cover it — selection is a property of the ticket, not of
each fence.

**Consequences.** The common case carries no selection bookkeeping and cannot
drift out of step with its own change, which is the failure a per-fence subset
invites: a task added to the plan but never added to the selection is silently
unauthorized. The cost is that carving a genuine subset out of an ordinary
ticket's change is not expressible; that work becomes an epic child, which is
what it already was.

## ADR 261 — The executor ticks the checklist, and that is not an amendment

**Context.** The pinned source's `tasks.md` is a checklist, and something has to
mark an item done. Whoever ticks it writes a commit into the pinned path after
the lock pinned its commit — which is exactly the shape the unauthorized-amendment
row refuses.

**Decision.** The executor ticks each item as it completes, and a checked item
means implemented and verified, not merely attempted. Those checkbox commits are
executor bookkeeping and pass the amendment row. An amendment is an edit to what
the source *authorizes* — its prose, its requirements and scenarios, the text of
a task, or a task added or removed — and that still requires a newer lock.

**Consequences.** The checklist stays a live record of progress rather than a
snapshot frozen at triage, and `revise` can run round after round without the
executor's own bookkeeping refusing the next one. The line between bookkeeping
and amendment is read from what changed, so a reviewer resolving a borderline
case asks whether the authorized work moved, not whether the file did.

## ADR 261 — Investigations get a lock only when they dispatch a worker

**Context.** An investigation produces findings rather than a diff. Requiring the
full authoring-and-pinning ceremony for every one would tax the cheapest tickets
in the flow to authorize work that touches nothing.

**Decision.** An investigation needs no lock when the attended session does the
work itself: the issue plus its posted findings are the record. It gets a lock —
an ordinary one, in whichever source mode fits, whose expected diff names the
findings it may write — only when it dispatches a bounded worker, because that is
the point where something other than the operator acts on the ticket and needs
its authorization written down.

**Consequences.** The ceremony lands where the risk is — delegation — and stays
off the tickets that carry none. An investigation that starts attended and later
decides to delegate acquires its lock at that moment, the same as any other
dispatch.
