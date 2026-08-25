# Claude worker dispatch

Use this adapter for every delegated Claude worker: exploration,
implementation, review, and follow-up. Do not dispatch a Claude worker through
the Agent tool, the Workflow tool, or a background agent — those routes are
retired for delegated work by work order 149. `skills/drivers/orchestrate/scripts/claude-worker.py`
is the only dispatch path, mirroring `codex-worker.py`'s command surface:
`start`, `resume`, `stop`, `verify`, `--state`, `--model`, `--effort`,
`--sandbox read-only|workspace-write`, `--cwd`, `--control-checkout`, and
`--claude` (defaults to `claude`, the CLI binary on PATH) in place of
`codex-worker.py`'s `--codex`.

## Command surface

Run `claude-worker.py start` for a new worker. Give read work a resolved
repository or worktree path and `--sandbox read-only`. Give write work a
resolved isolated worktree path, `--sandbox workspace-write`, and the
coordinator checkout in `--control-checkout`; the adapter rejects a
`--cwd` inside the control checkout, exactly as codex-worker.py does. Persist
one state file per worker. Use `resume` with that state file for retry
findings and ordinary follow-ups; it restores the captured model, sandbox,
effort, and canonical cwd rather than taking replacements — the same contract
as codex-worker's resume.

## Prompt on stdin, not as an argument

`claude-worker.py` writes the prompt to the worker's stdin and closes it,
unlike `codex-worker.py`, which still takes the prompt positionally. The
`claude` CLI's `-p` invocation carries variadic flags (`--tools`,
`--allowedTools`, `--disallowedTools`) that would swallow a trailing
positional prompt, so a prompt-on-stdin is a fact about the `claude` CLI, not
a stylistic choice — never pass the prompt as a trailing argv token to a
`claude-worker.py`-launched command.

## Sandbox modes

Both modes are generated settings files the adapter owns and writes to a
temp path at launch — it never reads a settings shape out of `docs/`, because
`docs/` is not part of an installed skill copy.

- **`read-only`**: `sandbox.enabled: true`, `allowUnsandboxedCommands: false`,
  `filesystem.denyWrite: ["/", "~/"]` (writes denied filesystem-wide), and
  `permissions.deny: ["Write", "Edit", "NotebookEdit"]` (the edit tools
  denied). `allowUnsandboxedCommands: false` is load-bearing: it disables the
  `dangerouslyDisableSandbox` retry, so a command the sandbox blocked cannot
  be re-run outside it.
- **`workspace-write`**: `sandbox.enabled: true`, `allowUnsandboxedCommands:
  false`, no filesystem deny-list (the cwd stays writable), and
  `permissions.allow: ["Write", "Edit", "NotebookEdit"]` (the edit tools
  allowed).

## Effort

Every delegation carries `--effort`, defaulting to `medium` for every model
because no effort benchmarking exists yet (see `references/routing-table.md`
Effort notes). `claude-worker.py`'s enum is `low|medium|high|xhigh|max`,
captured in `docs/scope/149-probes/effort-enums.md` from `claude --help`; it
is not the same set as `codex-worker.py`'s `minimal|low|medium|high|xhigh`.
The chosen effort is persisted in state and replayed on `resume`.

## Liveness is process identity only

A Claude worker has no rollout file and no headroom fields — there is no
Claude analogue of Codex's `~/.codex/sessions/*.jsonl` or its
`token_count.rate_limits` payload. `claude-worker.py` does not invent one:
liveness is proving the recorded PID/PGID/SID/cwd/birth identity still
matches, the same process-family probe codex-worker.py uses, and nothing
more. Do not infer a Claude worker's health from elapsed time or output
volume; there is no equivalent "CPU time growing" heuristic documented for
this adapter.

## Interrupted workers

The coordinator that launched a worker owns its recovery, exactly as with
Codex workers: run `claude-worker.py stop --state STATE --cwd WORKTREE`, then
`claude-worker.py verify --state STATE --cwd WORKTREE` and require success
before a successor receives the worktree. A successor never discovers or
cleans unknown processes; only the adapter's recorded dedicated process group
is in scope.

## Output

On success the adapter emits one public JSON object: `session_id`, `model`,
`sandbox`, `cwd`, `effort`, `final_message` (the CLI's `result` field), and
`permission_denials` (whatever the CLI's JSON payload reported as denied, so
the coordinator can see what the sandbox refused — an empty list when
nothing was denied). `is_error: true` in the CLI's own JSON is treated as a
dispatch failure, not a worker answer; the adapter fails instead of emitting.

## Presence check

Before dispatching any Claude worker, the coordinator runs `command -v claude`.
If neither `codex` nor `claude` is present on PATH, the coordinator
cannot dispatch at all: report the blocker to the operator and stop — there
is no third route to fall back to.
