# ADR 150 — Shared worker lifecycle module

Status: accepted (2026-08-24)

## Context

[ADR 149](adr-149-pack-owned-model-dispatch.md) deliberately shipped the Codex and
Claude worker adapters with duplicated state handling, process-family ownership,
liveness, launch, stop, verify, and control-checkout protection. Two real adapters now
make the lifecycle seam real. Leaving the copies in place would let their durability and
safety rules diverge as more skills adopt pack-owned dispatch.

The adapters differ in three load-bearing ways: each CLI has its own output format, each
adapter emits a different success object, and each adapter owns the prefix on its errors.
Claude also sends its prompt through stdin because its variadic CLI flags can swallow a
positional prompt; Codex takes the prompt as an argument and must keep stdin closed.

## Decision

The shared lifecycle lives beside the adapters in
`skills/drivers/orchestrate/scripts/worker_lifecycle.py`, so it is present in every
installed copy of the skill. Adapters reach moved machinery only through a qualified
`lifecycle.` reference. Re-exporting a moved name, assigning an alias, or forwarding it
through `__getattr__` is forbidden: a test patch could otherwise resolve against an
adapter's copy while the shared implementation continued through a different global,
making the patch intercept nothing.

Tests load the shared module once and register it as `worker_lifecycle` in `sys.modules`
before either adapter is executed. Loading the file separately for tests and adapters
would create two module objects, so a patch applied to one would not protect calls through
the other.

The `start`, `resume`, `stop`, and `verify` entry points remain in each adapter. Shared
preparation and worker-control helpers return errors to those entry points, which report
them through the adapter's own inline `fail()` function. A shared or module-global prefix
would be last-writer-wins when both adapters are loaded in one process.

The four launch functions — `establish_family`, `finish_lifecycle`, `run_portable`, and
`run_lifecycle` — are the exception to return-an-error-string. They take adapter callables,
including `fail`, as keyword-only inputs and continue returning an integer exit code.
Converting their failures to returned strings would change `run_lifecycle`'s pinned integer
contract and break callers that return it directly.

The shared launch interface accepts keyword-only `stdin_text`. A string selects a pipe and
is written only after the process-family gate is released; `None` selects
`subprocess.DEVNULL`. This supersedes issue #62's blanket “Unsupported” stdin ruling in
the [Codex stdin liveness ledger](../scope/orchestrate-codex-stdin-liveness.md) for the
shared module: Claude requires prompt-over-stdin. The Codex adapter still passes `None`,
retains `DEVNULL`, and remains covered by the open-stdin regression guard from #62.

## Consequences

* State durability, schema validation, family ownership, liveness, cleanup, and the
  control-checkout refusal have one implementation for both adapters.
* Output parsing, success emission, CLI arguments, effort enums, and error prefixes remain
  adapter-local.
* Tests patch the one owner of moved machinery and fail loudly if a moved name becomes
  reachable through either adapter.
* Both local verification and CI syntax-check the shared module and both adapters.
