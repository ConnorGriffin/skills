# Design

## ADR 241 — Epic coordination ends before execution

An epic coordinator owns the durable plan and writes a draft order into each bounded
child issue. The operator owns the lock and dispatch: `/ticket triage <id>` grounds
and independently reviews that draft before posting the only executable fenced work
order, and each later phase proceeds only when the operator explicitly invokes its
ticket verb. The epic skill therefore has no worker-adapter, delegated-subtree,
fan-out, liveness, retry, or result-collection path, including for research spikes.

This keeps the authority split shallow: OpenSpec owns the epic plan, ticket comments
own executable child orders, GitHub owns live child state, and attended ticket
sessions own implementation and review. Ticket's mandatory independent review is
unchanged because it is part of a child invocation, not an epic-owned dispatch.

### Consequences

- The coordinator writes the draft order in the child issue body, but does not post
  the fenced executable lock or invoke `/ticket triage`, `/ticket start`, `/ticket
  revise`, or a worker adapter.
- Research, prototype, interview, and build children are resumed in attended
  sessions by the operator; the epic records their returned decisions and status.
- Existing dispatch ADRs remain frozen history. The active epic contract no longer
  names `epic` as a dispatching consumer.

## ADR 241 — Prefer three or fewer independently shippable children

An epic defaults to at most three child tickets. Creating a fourth or later child
requires a written `design.md` justification that names the capability boundary or
dependency preventing consolidation into fewer, larger independently shippable
builds. The count is a planning admission check, not an execution-time guard.

## ADR 241 — Planning artifacts ship with implementation

An epic coordinator never opens a pull request. When ticket triage discovers that
the parent plan must change before a child can execute, it amends the parent active
change in that child's existing worktree, commits the amendment there, and continues
triage. The child implementation pull request therefore carries both the required
planning update and the implementation it governs. A pull request containing only
epic planning artifacts is unsupported.

This is not a per-child change record: the parent proposal/design/tasks/spec delta
remains the one authority and archive unit. Ticket finalization still leaves archive
ownership with the parent epic.

The separate one-time `openspec-adopt` workflow is outside this decision: its
documentation-only pull request establishes OpenSpec before an epic exists and is
not an epic planning-only pull request.
