# Nested adapter dispatch

## Decisions

- Route through interview mode because the live reproduction settles the mechanism failure but leaves ownership of mandatory review as a durable workflow-interface decision. Why: direct nested Codex adapter launch inherits the outer worker's restrictions, while coordinator-owned review changes the composition contract across Ticket and Orchestrate. Disposition: `inline`.
- The coordinator dispatches every mandatory reviewer for delegated workflow work and returns verified findings to the same worker; a worker never launches a nested reviewer. Why: coordinator-owned adapter dispatch works under the host's authority, preserves independent review, and avoids a new nested-dispatch mechanism that cannot escape the worker's inherited sandbox. Disposition: `→ ADR`.
- Add no cleanup guard, broker, runtime enforcement, or new recovery policy. Why: coordinator-owned reviewer dispatch removes the nested-worker ownership case, and broader lifecycle hardening is outside this ticket. Disposition: `inline`.

### Risk contract

- **Must prevent:** a delegated workflow silently treating a missing mandatory review as a clean verdict.
- **Must recover:** none beyond the adapters' existing coordinator-owned recovery contract.
- **Accepted failure:** a worker may still describe process state incorrectly in prose, costing manual diagnosis; this ticket adds no enforcement for that claim.
- **Unsupported:** direct adapter dispatch from inside a sandboxed worker; workers launching nested reviewers.
- **Evidence owed:** contract tests prove delegated Ticket and Orchestrate work assigns mandatory reviewer dispatch to the coordinator and rejects a missing verdict as unavailable, never clean.

Why: the supported composition path needs truthful review ownership, not stronger process-lifecycle assurance.
Disposition: `inline`.

## Open questions

- None.

## Spawned tasks

- Luna reproduction worker `01a04ad0-fcb1-72f3-9d9f-141c3fa2263c`; its one nested launch failed before session creation, then scoped `stop` and `verify` both succeeded.
