# Coordinator-owned mandatory review

## Why

A delegated workflow worker cannot launch the mandatory reviewer that Ticket and
Orchestrate currently promise it can reach. A live nested adapter launch failed
before session creation because the child Codex CLI inherited the worker's
restricted sandbox and could not initialize its local state or app-server. The
same adapter succeeds when the coordinator launches it.

## What changes

* A coordinator owns every mandatory reviewer dispatch for work it delegates.
* A delegated worker returns its draft or implementation result to the coordinator;
  the coordinator runs the required review and returns verified findings to the same
  worker for correction.
* A failed launch, nonzero exit, missing result artifact, or missing verdict is
  unavailable evidence, never a clean verdict.
* Direct adapter dispatch from inside a sandboxed worker is unsupported.
* No adapter, lifecycle, cleanup, sandbox, network, approval, or model-routing
  behavior changes.

## Risk contract

* **Must prevent:** a delegated workflow silently treating a missing mandatory review as a clean verdict.
* **Must recover:** none beyond the adapters' existing coordinator-owned recovery contract.
* **Accepted failure:** a worker may still describe process state incorrectly in prose, costing manual diagnosis; this ticket adds no enforcement for that claim.
* **Unsupported:** direct adapter dispatch from inside a sandboxed worker; workers launching nested reviewers.
* **Evidence owed:** contract tests prove delegated Ticket and Orchestrate work assigns mandatory reviewer dispatch to the coordinator and rejects a missing verdict as unavailable, never clean.

Why: the supported composition path needs truthful review ownership, not stronger process-lifecycle assurance.
Disposition: inline.
