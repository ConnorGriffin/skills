# Design

## ADR 241 — Epic coordination ends before execution

An epic coordinator owns the durable plan and the bounded child work orders. The
operator owns dispatch: each child proceeds only when the operator explicitly runs
the applicable ticket verb. The epic skill therefore has no worker-adapter,
delegated-subtree, fan-out, liveness, retry, or result-collection path, including
for research spikes.

This keeps the authority split shallow: OpenSpec owns the epic plan, ticket comments
own executable child orders, GitHub owns live child state, and attended ticket
sessions own implementation and review. Ticket's mandatory independent review is
unchanged because it is part of a child invocation, not an epic-owned dispatch.

### Consequences

- The coordinator may prepare and post a child work order, but it does not invoke
  `/ticket triage`, `/ticket start`, `/ticket revise`, or a worker adapter.
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

An epic coordinator never opens a pull request. Proposal, design, tasks, and delta
spec changes remain in the active change until an implementation ticket includes
the applicable planning updates in its pull request. A pull request containing only
epic planning artifacts is unsupported.

The separate one-time `openspec-adopt` workflow is outside this decision: its
documentation-only pull request establishes OpenSpec before an epic exists and is
not an epic planning-only pull request.
