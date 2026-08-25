# Run log — #149 sub-order 2/2

Executed evidence for the adapters in `skills/drivers/orchestrate/scripts/`, run
from `<worktree>` (the ticket worktree, `codex/149-universal-effort-dial-c2`) with
`/opt/homebrew/bin/python3.14`. A throwaway scratch worktree was created at
`<worktree>-probe-write` (branch `scratch/149-probe-write`) for the write-mode
runs planned in Do item 3; it went unused because those runs are blocked (see
below) — nothing was written into it.

## Claude-side runs: BLOCKED

`claude auth status` reports:

```
{
  "loggedIn": false,
  "authMethod": "none",
  "apiProvider": "firstParty"
}
```

The `claude` CLI's OAuth session is expired and could not be refreshed
non-interactively. Re-authentication requires an interactive browser login,
which is outside this agent's authority to perform. Every run that depends on
the `claude` CLI is recorded below as blocked rather than faked.

### `probe.sh` (Do item 2) — blocked

Command:

```
sh docs/scope/149-probes/probe.sh /tmp/149-probe-run1
```

Actual captured output (every case failed authentication before exercising
sandbox behavior):

```
# probe run fdc091d
# claude 2.1.228 (Claude Code)
readonly: wrote_in_cwd=no escaped_cwd=no
readonly: report=Failed to authenticate: OAuth session expired and could not be refreshed
write: wrote_in_cwd=no escaped_cwd=no
write: report=Failed to authenticate: OAuth session expired and could not be refreshed
session: id_honored=True resume_carries_context=False
session: resume_accepts_effort=False
session: parsed_fields=['is_error', 'permission_denials', 'result', 'session_id', 'total_cost_usd']
resumed: wrote_after_resume=no
resumed: report=Failed to authenticate: OAuth session expired and could not be refreshed
```

blocked: `claude auth status` reports loggedIn=false; interactive browser login
required. `docs/scope/149-probes/output.txt` (checked in from an earlier,
authenticated run during triage) remains the only real evidence for the
readonly/write/session/resumed cases this script exercises; it was not
re-verified by this chunk.

### `claude-worker.py start` — read-only worker (Do item 3) — blocked

Planned command (not completed — fails at the `claude` CLI auth step):

```
python3 skills/drivers/orchestrate/scripts/claude-worker.py start \
  --state <state-dir>/readonly.json --model haiku --sandbox read-only \
  --cwd <worktree> <<< "run a shell command, then attempt to write a file"
```

blocked: `claude auth status` reports loggedIn=false; interactive browser login
required.

### `claude-worker.py start` — workspace-write worker in the throwaway worktree — blocked

Planned command (not completed):

```
python3 skills/drivers/orchestrate/scripts/claude-worker.py start \
  --state <state-dir>/write.json --model haiku --sandbox workspace-write \
  --cwd <worktree>-probe-write --control-checkout <control-checkout> \
  <<< "write a file in cwd, then attempt to write into $HOME"
```

blocked: `claude auth status` reports loggedIn=false; interactive browser login
required.

### `claude-worker.py resume` — read-only worker refused a write, effort replay — blocked

blocked: `claude auth status` reports loggedIn=false; interactive browser login
required. Not run: cannot confirm the refusal survives resume through the
adapter's own argv, and cannot confirm the resumed worker's emitted effort
matches what start captured.

### `claude-worker.py stop` + `verify` — blocked

blocked: no worker was ever started (all `start` calls above are blocked), so
there is no process family to stop or verify.

## Codex-side runs: RAN

`codex login status` reports "Logged in using ChatGPT" — the Codex CLI is
authenticated and present on PATH (`codex-cli 0.149.0`).

### Headroom gate (SKILL.md:14-40) — probe

Command:

```
python3 skills/drivers/orchestrate/scripts/codex-worker.py start \
  --state <state-dir>/headroom-probe.json --model gpt-5.6-luna --sandbox read-only \
  --cwd <worktree> "Reply with exactly: PROBE"
```

Output:

```
{"session_id": "01a0374b-1ee3-7022-b2a5-f0b41842ca46", "model": "gpt-5.6-luna", "sandbox": "read-only", "cwd": "<worktree>", "effort": "medium", "final_message": "PROBE", "headroom": 77.0, "headroom_status": "known"}
```

Headroom = 77% (known), well above the 5% gate. Codex-side spend is
authorized for the run below.

### `codex-worker.py start` with an explicit `--effort` (Do item 4) — ran

Command:

```
python3 skills/drivers/orchestrate/scripts/codex-worker.py start \
  --state <state-dir>/real-effort.json --model gpt-5.6-luna --sandbox read-only \
  --effort high --cwd <worktree> "Reply with exactly: EFFORT_RUN_OK"
```

Output:

```
{"session_id": "01a0374b-736e-7a90-b759-4a370abbcac8", "model": "gpt-5.6-luna", "sandbox": "read-only", "cwd": "<worktree>", "effort": "high", "final_message": "EFFORT_RUN_OK", "headroom": 77.0, "headroom_status": "known"}
```

The `--effort high` flag reached the session, the run completed, and the
emitted `effort` field (`"high"`) matches what was passed to `start` — the
same claim Do item 3 requires proving for the resumed Claude worker's emitted
effort, proven here on the Codex side, which was not blocked.

## Rejections (Do item 5) — ran, no auth required

These are pure adapter argument validation and complete before either CLI is
invoked.

### Effort outside each adapter's enum

Command:

```
python3 skills/drivers/orchestrate/scripts/claude-worker.py start \
  --state <state-dir>/bad-effort-claude.json --model haiku --sandbox read-only \
  --effort bogus --cwd <worktree> "noop"
```

Output (stderr, exit 1):

```
claude-worker: --effort must be one of ['high', 'low', 'max', 'medium', 'xhigh']
```

Command:

```
python3 skills/drivers/orchestrate/scripts/codex-worker.py start \
  --state <state-dir>/bad-effort-codex.json --model gpt-5.6-luna --sandbox read-only \
  --effort bogus --cwd <worktree> "noop"
```

Output (stderr, exit 1):

```
codex-worker: --effort must be one of ['high', 'low', 'medium', 'minimal', 'xhigh']
```

### `--sandbox workspace-write` pointed inside the control checkout

Command:

```
python3 skills/drivers/orchestrate/scripts/claude-worker.py start \
  --state <state-dir>/inside-cc-claude.json --model haiku --sandbox workspace-write \
  --effort medium --cwd <worktree> --control-checkout <worktree> "noop"
```

Output (stderr, exit 1):

```
claude-worker: workspace-write refuses the control checkout
```

Command:

```
python3 skills/drivers/orchestrate/scripts/codex-worker.py start \
  --state <state-dir>/inside-cc-codex.json --model gpt-5.6-luna --sandbox workspace-write \
  --effort medium --cwd <worktree> --control-checkout <worktree> "noop"
```

Output (stderr, exit 1):

```
codex-worker: workspace-write refuses the control checkout
```

## Corrections this chunk made

None. No run above contradicted a claim in `claude-worker.py`, `codex-worker.py`,
`SKILL.md`, or `references/dispatch-claude.md`. The Claude-side behavioral
claims (read-only confinement, write-worker confinement, resume-preserved
refusal, resume-preserved effort) remain unverified by this chunk's own runs
and rest only on `docs/scope/149-probes/output.txt` captured during triage —
this is a gap this run-log records, not a defect this run-log can rule on.
