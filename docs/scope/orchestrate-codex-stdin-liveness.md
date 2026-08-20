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

## Open questions

- Q1 scope of fix: helper code plus documented rule, or documented rule only.
- Q2 liveness: written coordinator rule, or a helper subcommand.
- Q3 document inventory: which of the other `codex exec` sites the change covers.

## Spawned tasks

