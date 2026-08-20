# Scope ledger — orchestrate: Codex background dispatch stdin hang and liveness

Routed by /scope → interview mode. Ticket:
[#62](https://github.com/ConnorGriffin/skills/issues/62).

## Grounding facts

- `references/dispatch-codex.md` carries no raw `codex exec` template; every
  dispatch goes through `skills/drivers/orchestrate/scripts/codex-worker.py`.
- Both launch paths in that helper leave stdin inherited:
  `gated_process()` (`subprocess.Popen`, stdout/stderr piped, no `stdin=`) and
  `run_portable()` (`subprocess.run`, same omission). A backgrounded coordinator
  hands them whatever stdin it holds.
- `codex exec --help` (v0.144.x, homebrew): the prompt argument does not stop
  stdin being read — "If stdin is piped and a prompt is also provided, stdin is
  appended as a `<stdin>` block". So an open, never-closing stdin blocks before
  session start.
- Reproduced 2026-08-19 in this session: `codex exec` with a `socketpair` fd as
  stdin printed `Reading additional input from stdin...`, held 0:00.08 CPU at
  12s, and wrote no rollout. The same command with `stdin=subprocess.DEVNULL`
  completed inside 20s and wrote
  `~/.codex/sessions/2026/08/19/rollout-2026-08-19T23-20-38-*.jsonl`.
- `codex-worker.py verify` is a teardown check (process group empty), not a
  liveness check; the helper has no liveness command today.
- `tests/test_behavior.py` already drives the helper through its CLI against a
  fake `codex` binary, so a regression test has a home.
- Other places naming a `codex exec` invocation:
  `references/benchmark/README.md:87`, `docs/orchestrate-spec.md:16,81`,
  `docs/scope/orchestrate-codex-headroom.md:19`,
  `skills/drivers/orchestrate/SKILL.md:63,105`.

## Decisions

- Fix the helper and document the rule, not one or the other: `codex-worker.py`
  closes stdin on both launch paths, and `references/dispatch-codex.md` states
  the rule where dispatch is described. The adapter carries no shell template to
  annotate, so a written rule alone would protect nobody dispatching the
  supported way. — `inline`
- Liveness stays a written coordinator rule (CPU time growing plus a rollout
  file), not a new helper subcommand. `verify` already owns the process-family
  surface, and a second probe command would be a seam with one caller. —
  `inline`
- Document inventory is the adapter only. The other `codex exec` sites describe
  foreground or probe runs, which the reproduction showed behave normally. —
  `inline`

### Risk contract

- **Must prevent:** a dispatched worker that blocks forever before session start
  while the coordinator believes it is working.
- **Must recover:** nothing automatically; the coordinator stops and reports.
- **Accepted failure:** a worker that hangs *after* session start is out of
  scope and still needs the operator's `stop`/`verify` path.
- **Unsupported:** deliberately piping a prompt through stdin to the helper; the
  helper takes its prompt as an argument only.
- **Evidence owed:** a regression test that drives `codex-worker.py start`
  through its CLI with an inherited open stdin and a fake codex that reads stdin
  to EOF, failing before the fix and passing after.
- **Why:** the helper is the shared dispatch path every fleet coordinator
  inherits, so a deadlock here is silent and expensive.
- **Disposition:** `inline` — copied into the work order on
  [#62](https://github.com/ConnorGriffin/skills/issues/62).

### Spike — run 2026-08-19, scratchpad, not committed

Copied `codex-worker.py`, applied the two `stdin=subprocess.DEVNULL` edits, and
ran `start` under a `socketpair` stdin against a fake codex that calls
`sys.stdin.read()` before emitting JSONL:

```
patched=False: HUNG (10s timeout) - stdin inherited
patched=True: exit=0 stdout='{"session_id": "worker-1", ...}'
```

## Open questions

None; Q1-Q3 settled above.

## Spawned tasks
