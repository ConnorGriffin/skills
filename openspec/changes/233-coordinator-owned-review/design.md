# Design

## ADR 233 — Coordinators own mandatory reviewer dispatch

### Context

Ticket and Orchestrate authorize mandatory review and route every model dispatch
through the pack adapters. Their prose currently treats nested review as something
a delegated workflow worker can dispatch itself. Live reproduction showed that the
nested Codex CLI inherits the worker's restricted sandbox: it could not write the
Codex state database and failed app-server initialization before creating a session.
The coordinator launched the same adapter successfully from the same checkout.

### Decision

The coordinator that delegates work owns every mandatory reviewer dispatch. A
delegated worker returns a durable draft or implementation result; the coordinator
dispatches the reviewer through the existing adapter, verifies the returned verdict,
and resumes the same worker with actionable findings when correction is required.
A reviewer failure or missing result is reported as unavailable and never interpreted
as an empty finding list.

Direct adapter dispatch from inside a sandboxed worker is unsupported. The pack will
not add a nested-dispatch broker, change adapter privileges, or add cleanup enforcement
for this decision.

### Consequences

* Ticket triage, start, and revise remain delegable, but their coordinator owns the
  mandatory plan or code review between worker turns.
* Orchestrate's existing coordinator role now explicitly includes mandatory reviews
  reached by delegated workflow work.
* Review skills and worker adapters keep their current interfaces and behavior.
* The existing bounded-egress consent still covers the coordinator's mandatory
  reviewer dispatch; only dispatch ownership changes.
