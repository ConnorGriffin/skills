---
name: wayfinder
description: Chart and resolve a large, foggy effort as a GitHub map of decision tickets, then hand clear independent subtrees to your implementation workflow as ordinary build issues. Use when an idea is too large or uncertain for one session, when the user invokes wayfinder or supplies a wayfinder map, or when planning must settle research, UI, domain, and scope decisions before implementation begins.
---

# Wayfinder

Find the way to a destination across multiple sessions. Maintain one `wayfinder:map`
issue with child decision tickets, resolve one decision per session, and file build
issues only when no open decision can invalidate their subtree.

## Operating rules

- **Plan, do not build.** Resolve decisions and create planning artifacts. The pull to
  implement is normally the signal to hand a clear subtree to whatever process builds
  your work.
- **Refer by name.** In human-facing text, wrap issue links in their titles. Never make
  people decode a wall of bare issue numbers.
- **Keep one source for each answer.** The resolution lives in its ticket comment. The map
  keeps only a one-line gist and link. An ADR keeps only the lasting ruling.
- **Work one decision per session.** Parallel AFK research tickets are the sole exception.
- **Ground structural decisions in the project's standards.** When a decision ticket
  settles module or interface shape, judge it by the project's engineering standards
  document (charter, architecture guide) when one exists, and load `/codebase-design`
  for the vocabulary when it is available. Interface shape is a decision the map
  resolves, never one left implicit for the build session.
- **Use GitHub's native structure.** Read
  [references/github-tracker.md](references/github-tracker.md) before any tracker action.
  Do not replace child issues, blocking relationships, or label claims with body text.

## The map

The map is a GitHub issue labelled `wayfinder:map`. Its decision tickets are native child
issues. The map body is the low-resolution view loaded at the start of every session:

```markdown
## Destination

<One or two lines describing what this effort is finding its way to.>

## Notes

<Domain, standing preferences, and skills every session must consult.>

## Decisions so far

- [<closed ticket title>](https://github.com/<org>/<repo>/issues/<n>) — <one-line gist>

## Awaiting disposition

- [<open research ticket title>](https://github.com/<org>/<repo>/issues/<n>) — <findings are complete; build candidates need rulings>

## Not yet specified

<In-scope fog that cannot yet be phrased as a precise question.>

## Handoffs

- [<build issue title>](https://github.com/<org>/<repo>/issues/<n>) — <independent subtree handed off>

## Out of scope

<Work consciously ruled beyond the destination, with reasons.>
```

The map is an index, not a duplicate store. Discover live work from its open child issues,
not by maintaining another ticket list in the body.

## Decision tickets

Each ticket is sized to one agent session and has this body:

```markdown
## Question

<The precise decision or investigation this ticket resolves.>
```

Apply exactly one ticket-type label:

- **`wayfinder:research` (AFK-able):** Any investigation an unattended agent session can
  finish alone — an internal repository audit as much as an outward read. Invoke `/research`
  when the answer depends on documentation, third-party systems, or sources outside the
  repository; ground directly in the repo when it doesn't. Record findings, sources, and
  the decision they support. Treat `/research` as a required dependency for outward reads:
  if it is unavailable, leave the ticket unclaimed and tell the human rather than
  substituting a generic search pass. The label is a promise of AFK-ability — an unattended
  session may be dispatched for an unclaimed research ticket, so apply it honestly.
- **`wayfinder:prototype` (HITL):** Invoke `/ui-craft`. Produce repository-grounded
  variants, iterate with the human, and finish with a locked visual spec linked from the
  ticket. That artifact also satisfies any later review gate that demands a locked design.
- **`wayfinder:grilling` (HITL):** Invoke `/grilling`, plus a domain-modelling skill when
  one is available; ask one question at a time. Never answer the human's side of the
  exchange.
- **`wayfinder:task` (HITL):** A prerequisite that genuinely needs the human in the loop.
  It earns a place only by unblocking a decision, not by delivering the destination — and
  it is never an execution errand: a prerequisite that must *change the world* before a
  decision can be made is handed off as an ordinary build issue, and its landed result
  feeds back into the map as a decision input.

`wayfinder:awaiting-disposition` is durable state, not a ticket type or a claim. A research
ticket in that state remains open, keeps its one `wayfinder:research` ticket-type label, and
may temporarily also carry the distinct `wayfinder:resolving` claim while a human reconciles
its findings.

The claim is the `wayfinder:resolving` label, shared by human sessions and unattended
workers. Assignment is not the claim: an unattended worker may run under the operator's own
GitHub identity, so assignment cannot tell the two apart. Set the label before work, remove
it on completion or when giving up, and skip open tickets already claimed. Native issue
dependencies define order. The **frontier** is the map's child tickets that are open,
unblocked, unclaimed, and not carrying `wayfinder:awaiting-disposition`.

The session that launches a worker owns claim recovery. A successful spawn is not a
durable outcome: supervise the worker until the ticket is resolved or the worker fails. On
failure or interruption, remove its `wayfinder:resolving` claim before reporting the ticket
available again. Never leave a claimed ticket behind with no live worker. If your
environment has its own dispatcher that runs unclaimed research tickets unattended, that
dispatcher owns them instead and charting does not spawn workers itself.

## Fog and scope

Put a question in a ticket when it can be stated precisely now, even if blocked. Keep it in
`Not yet specified` when the question itself is still vague. Do not pre-slice fog: one patch
may later become several tickets or none.

Keep decided work, live tickets, and out-of-scope work out of the fog. When a ticket proves
to be beyond the destination, close it, link it under `Out of scope` with the reason, and do
not add it to `Decisions so far`.

## Chart a map

When the user brings a loose idea:

1. Run `/grilling`, and a domain-modelling skill when one is available, to name the
   destination. The destination fixes scope, so settle it first.
2. Grill breadth-first across the effort. Surface precise decisions, dependency order, and
   coarse fog without resolving any ticket.
3. If the route is already clear and fits one session, stop and tell the user a map would
   add no leverage.
4. Ensure the six persistent `wayfinder:*` labels exist, then create the map with its destination,
   notes, fog, and scope boundary.
5. Create every currently precise decision ticket as a child of the map. Create all issues
   first, then add native blocking relationships in a second pass.
6. Verify `/research` is available and the environment can both launch and supervise
   background workers. If either capability is unavailable, leave research tickets
   unclaimed and report the missing prerequisite.
7. For each research ticket already on the frontier, launch one separate AFK worker with
   `/research` and the complete ticket-resolution task attached. Tell it explicitly that it
   is already the background worker: it must research directly, never delegate again. Each
   worker verifies eligibility, claims, researches, comments, and updates only its ticket
   and the map. Its terminal findings comment must end with the structured candidate list
   defined under **Reconcile completed research**. If that list contains any
   `handoff_required` candidates, it adds `wayfinder:awaiting-disposition`, adds the ticket
   under `Awaiting disposition`, releases its claim, and leaves the ticket open. Otherwise it
   records the final gist under `Decisions so far`, closes the ticket, and releases its claim.
8. Record every worker ID and supervise all workers to terminal completion. Spawn success
   alone does not mean "research running." Before reporting success, verify the findings
   comment and map update, then verify either an open, unclaimed awaiting-disposition ticket
   or a closed ticket with no undisposed candidates. If a worker fails or is interrupted,
   release its `wayfinder:resolving` claim and report the failure. If the user replaces the
   task, reconcile or cancel every worker and release failed claims before switching work.
9. Stop after every launch has reached a durable outcome. Charting creates the map; the
   root session does not hand-resolve a research ticket while its worker runs.

## Work through a map

When the user supplies a map, optionally with a ticket:

1. Load the map body, not every child body.
2. Before selecting ordinary frontier work, inspect the map's open research children and
   reconcile every one carrying `wayfinder:awaiting-disposition` by following **Reconcile
   completed research** below. Restore a missing `Awaiting disposition` entry before
   reconciling. Skip an awaiting child another session already claims with
   `wayfinder:resolving`; that session owns finishing it. Re-read the map after each ticket;
   do not begin frontier work while any unclaimed awaiting child or entry remains.
3. If the user named a ticket, verify it is open and unblocked. Otherwise choose the first
   frontier ticket in tracker order. Claim it before reading deeply or invoking another
   skill.
4. Resolve that one question. Load related tickets only as needed and invoke every skill in
   the map's `Notes`.
5. Post a resolution comment with the answer, supporting evidence or artifact links, and
   the important alternatives rejected. Keep the full reasoning here.
6. Decide whether the ruling is load-bearing. Create or update an ADR before closing when
   the decision constrains multiple builds, is costly to reverse, settles architecture or
   domain language, or must be enforced downstream. Follow the repository's ADR format and
   index. Link the ADR from the resolution; keep reasoning in the ticket and the concise
   ruling plus consequences in the ADR.
7. Close the ticket and append its titled link plus one-line gist to `Decisions so far`.
8. Create and wire newly precise tickets, graduate cleared fog, and remove invalidated or
   out-of-scope tickets. Expect concurrent sessions and re-read tracker state before edits.
9. Evaluate handoff eligibility for every affected independent subtree.

## Reconcile completed research

Completed unattended research with structured `handoff_required` candidates is not resolved
until a human disposes every candidate. Keep the research ticket open, keep
`wayfinder:awaiting-disposition`, and keep its titled link under the map's
`Awaiting disposition` section throughout reconciliation.

Claim the research ticket with `wayfinder:resolving`, then read its terminal findings comment.
The worker writes every candidate in a final fenced YAML block using this envelope; an empty
`candidates` list explicitly proves that no build disposition is pending:

```yaml
wayfinder_findings:
  candidates:
    - id: <stable identity unique within this research ticket>
      disposition: handoff_required
      title: <independently shippable outcome>
      outcome: <observable result the build must produce>
```

Keep `id` byte-for-byte unchanged in every build issue or disposition comment. Candidate IDs,
not titles or list position, are the replay identity. A missing or malformed envelope is not a
completed research result: repair the findings comment before closing or reconciling the ticket.
The operator may select zero or more candidates. For each independently shippable selected
candidate, file one ordinary standalone build issue using **Hand clear work to implementation**;
never combine independent candidates into an umbrella issue. Copy the candidate's exact
structured identity into that issue's `Wayfinder candidate:` marker so replay can match the
issue back to one candidate. For every unselected candidate, record that same identity in a
disposition comment on the research ticket:

- **No-build:** name the reason, the observable trigger that would invalidate the ruling, and
  the condition that verifies no build is needed.
- **Deferred:** name the observable trigger that reopens consideration and the condition that
  will verify the later build is complete.

A selected candidate is durably disposed only when all three handoff facts agree:

1. the map's `Handoffs` entry links the build issue;
2. the build issue body contains the exact marker `Wayfinder handoff: #<map>`; and
3. the build issue has a native `blockedBy` edge to this terminal research child.

A map link alone never counts as a handoff. Before filing anything, and again after every
GitHub mutation, re-read the map, research comments and labels, candidate build issue bodies,
and native dependencies. Derive completed work from GitHub: match existing map entries and
ordinary issues carrying the exact marker and research dependency back to each structured
candidate by its copied identity. Repair a partial three-fact handoff in place; never create a
duplicate build issue, map line, or disposition comment. The tracker reference gives the
mutation order and replay procedure.

After every candidate has exactly one durable selected, no-build, or deferred disposition,
finalize in order: remove the ticket's `Awaiting disposition` map entry, remove
`wayfinder:awaiting-disposition`, append its titled link and explicit final gist under
`Decisions so far`, then close the research ticket and release its claim.
Close research only after every candidate has a durable disposition; never close it with an
undisposed candidate.

Maintainer invariant: closed research always has a durable disposition. No hidden
issues-to-file list exists outside GitHub.

## Hand clear work to implementation

Hand off a subtree as soon as all of these are true:

- its fog is empty;
- no open decision anywhere on the map could invalidate its outcome, constraints, or
  acceptance criteria;
- every relevant load-bearing ruling is in an ADR;
- any user-facing surface has a locked `/ui-craft` spec.

File a new ordinary GitHub issue in the repository that will build it. Do **not** make it a
child decision ticket, and do **not** add any `wayfinder:*` label. Whatever intake your
implementation workflow uses owns its own routing labels, briefs, and effort dials —
wayfinder never sets them.

Make the issue stand alone. Whoever picks it up grounds from the repository and will not
chase the map's links to reconstruct context. Use the repository's domain terms and inline
every relevant ruling:

```markdown
## Outcome

<Observable result this build should deliver.>

## Decided constraints

- <Decision title>: <ruling stated inline, with ADR link when one exists>

## Scope

<What this ticket includes.>

## Acceptance criteria

- <Observable criterion>

## Evidence and locked artifacts

- <Research evidence or locked visual spec, with the operative conclusion repeated here>

## Not part of this ticket

- <Nearby work deliberately excluded>

Wayfinder handoff: #<map>
Wayfinder candidate: <candidate id — only when this issue came from a research disposition>
```

Before filing, reconcile existing handoff facts in GitHub. The two trailing marker lines are
the issue's durable identity: keep `Wayfinder handoff: #<map>` byte-for-byte, and carry
`Wayfinder candidate:` only when a research disposition produced this issue, repeating that
candidate's `id` unchanged. Then add a native `blockedBy` edge from the build issue to at
least one terminal decision child that cleared the work, and link the filed issue under the
map's `Handoffs`. During research disposition, that dependency is the terminal research
child. All three facts must agree before the handoff counts. If intake sends the issue back
for more scoping or clarification, treat that as evidence the map was incomplete: create a
new decision ticket for the gap, link the held build issue, and stop handing off dependent
work until the gap is resolved.

The map is complete when nothing remains in fog, no decision ticket is open, and every
buildable subtree has been handed off (or the destination explicitly requires no build).
