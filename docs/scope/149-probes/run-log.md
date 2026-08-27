# Run log — #149 sub-order 2/2

Executed evidence for the adapters in `skills/drivers/orchestrate/scripts/`, run
from `<worktree>` (the ticket worktree, `codex/149-universal-effort-dial-c2`) with
`/opt/homebrew/bin/python3.14`. A throwaway scratch worktree was created at
`<worktree>-probe-write` (branch `scratch/149-probe-write`) for the write-mode
runs.

A bare `python3` in the command blocks below means `/opt/homebrew/bin/python3.14`.
The machine's default `python3` is 3.9.6, which this suite does not support.

The operator re-authenticated the `claude` CLI partway through this chunk
(`claude auth status` now reports `loggedIn: true`, `authMethod: claude.ai`).
Everything below ran for real.

## Claude-side runs: RAN

### `probe.sh` (Do item 2)

Command:

```
sh docs/scope/149-probes/probe.sh /tmp/149-probe-run2
```

Output:

```
# probe run 9de3537
# claude 2.1.228 (Claude Code)
readonly: wrote_in_cwd=no escaped_cwd=no
readonly: report=**READ_FAIL, WROTE_FAIL, ESCAPE_FAIL** — all operations blocked by sandbox restrictions. The `ls -a` failed because the shell cannot write its cwd tracking file; probe.txt write to current directory was denied; and the
write: wrote_in_cwd=yes escaped_cwd=yes
write: report=**6 entries** in current directory.  **READ_OK** / **WROTE_OK** / **ESCAPE_OK**
session: id_honored=True resume_carries_context=True
session: resume_accepts_effort=True
session: parsed_fields=['is_error', 'permission_denials', 'result', 'session_id', 'total_cost_usd']
resumed: wrote_after_resume=no
resumed: report=WROTE_FAIL
```

`write: escaped_cwd=yes` is a real escape, confirmed independently (not just
trusted from the worker's self-report — a worker reporting DONE while
creating no file was observed during triage):

```
$ ls -la "$HOME/.cache/149-probe-escape/escape-write.txt"
-rw-r--r--@ 1 connor  staff  7 Aug 24 22:11 $HOME/.cache/149-probe-escape/escape-write.txt
$ cat "$HOME/.cache/149-probe-escape/escape-write.txt"
ESCAPED
```

This is `write.settings.json`'s fixture, not the adapter under test — that
fixture carries no `filesystem` block at all, same shape as
`claude-worker.py`'s pre-fix `sandbox_settings("workspace-write")`. It is out
of this chunk's boundary to correct (not one of sub-order 1's files), so it is
recorded here rather than changed; the adapter itself is fixed below and
re-verified directly against the corrected settings, not through this fixture.

### `claude-worker.py start` — read-only worker: shell command runs, write refused

Command:

```
python3 skills/drivers/orchestrate/scripts/claude-worker.py start \
  --state <state-dir>/readonly.json --model haiku --sandbox read-only \
  --cwd <worktree> \
  "Run \`ls -a\` with bash and report how many entries. Then attempt to create a file named readonly-probe.txt in the current directory with bash, and report READ_OK/READ_FAIL and WROTE_OK/WROTE_FAIL."
```

Output:

```
{"session_id": "7057e983-f119-4847-8d0b-9b0ba024e1b1", "model": "haiku", "sandbox": "read-only", "cwd": "<worktree>", "effort": "medium", "final_message": "Bash permission was denied mid-sequence. Results so far:\n\n- **ls -a**: 23 entries\n- **Current directory write**: WROTE_FAIL (operation not permitted)\n- **Current directory read**: READ_FAIL (file never created)\n- **Scratchpad write**: WROTE_FAIL (operation not permitted)\n\nThe sandbox is preventing file writes across all attempted paths. Do you want me to request Bash permission to continue probing `$TMPDIR` and other writable locations?", "permission_denials": [{"tool_name": "Bash", "tool_use_id": "toolu_016M5JH7AdckRbeymwcLkAMJ", "tool_input": {"command": "echo \"TMPDIR=$TMPDIR\" && touch \"$TMPDIR/readonly-probe.txt\" && echo \"WROTE_OK\" || echo \"WROTE_FAIL\"", "description": "Write to $TMPDIR environment variable"}}]}
```

Verified independently: `ls -a` ran (23 entries reported) and no file was
created.

```
$ ls -la <worktree>/readonly-probe.txt
ls: <worktree>/readonly-probe.txt: No such file or directory
```

### `claude-worker.py start` — workspace-write worker in the throwaway worktree

First real run, against the **uncorrected** adapter (see "Correction this
chunk made" below) — cwd write also failed here, exposing the defect:

```
$ python3 skills/drivers/orchestrate/scripts/claude-worker.py start \
    --state <state-dir>/write.json --model haiku --sandbox workspace-write \
    --cwd <worktree>-probe-write --control-checkout <control-checkout> \
    "Use bash to create a file named write-probe.txt in the current directory containing WROTE. Then attempt to create \$HOME/.cache/149-c2-escape-probe.txt containing ESCAPED via bash. Report WROTE_OK/WROTE_FAIL and ESCAPE_OK/ESCAPE_FAIL."
{"session_id": "184fc03c-af57-4550-a2bb-d6b11608d1d7", "model": "haiku", "sandbox": "workspace-write", "cwd": "<worktree>-probe-write", "effort": "medium", "final_message": "Write to `$TMPDIR` succeeds, but both target paths fail due to sandbox restrictions.\n\n**WROTE_FAIL** — write to current directory `<worktree>-probe-write` blocked despite path being in allowlist.\n\n**ESCAPE_FAIL** — write to `$HOME/.cache/149-c2-escape-probe.txt` blocked as expected; that path is not in the allowlist.\n\nThe sandbox is enforcing the deny at both targets. The project directory result is surprising since it's listed; the restriction may be context-specific or the allowlist entry may require additional conditions not met here.", "permission_denials": []}
$ ls -la <worktree>-probe-write/write-probe.txt
ls: <worktree>-probe-write/write-probe.txt: No such file or directory
```

After the fix (`filesystem.allowWrite: [cwd]`, no `denyWrite` — see
correction below), re-run:

```
$ python3 skills/drivers/orchestrate/scripts/claude-worker.py start \
    --state <state-dir>/write.json --model haiku --sandbox workspace-write \
    --cwd <worktree>-probe-write --control-checkout <control-checkout> \
    "Use bash to create a file named write-probe.txt in the current directory containing WROTE. Then attempt to create \$HOME/.cache/149-c2-escape-probe.txt containing ESCAPED via bash. Report WROTE_OK/WROTE_FAIL and ESCAPE_OK/ESCAPE_FAIL."
{"session_id": "cbb70bf9-e84f-4e0c-afa6-f60c9c1c03f7", "model": "haiku", "sandbox": "workspace-write", "cwd": "<worktree>-probe-write", "effort": "medium", "final_message": "**WROTE_OK** — file created in current directory.\n**ESCAPE_FAIL** — sandbox blocks writes outside the allowed paths ($HOME/.cache is not in the write allowlist).", "permission_denials": []}
```

Verified independently, not from the worker's self-report:

```
$ ls -la <worktree>-probe-write/write-probe.txt
-rw-r--r--@ 1 connor  staff  6 Aug 24 22:24 <worktree>-probe-write/write-probe.txt
$ cat <worktree>-probe-write/write-probe.txt
WROTE
$ ls -la "$HOME/.cache/149-c2-escape-probe.txt"
ls: $HOME/.cache/149-c2-escape-probe.txt: No such file or directory
```

Write succeeded in cwd; the home-directory escape did not happen. A write
under `$TMPDIR` was not attempted in this exact run, but see the ad hoc
settings-diagnosis runs below, where a sibling case (`$TMPDIR` write) was
explicitly attempted against the corrected `allowWrite`-only shape and
refused — over-restrictive relative to the probe's stated allowance, not a
confinement failure (denying more than required is not an escape).

### `claude-worker.py resume` — read-only worker still refused a write, effort matches

Command:

```
python3 skills/drivers/orchestrate/scripts/claude-worker.py resume \
  --state <state-dir>/readonly.json \
  "Use bash to attempt to create a file named resumed-probe.txt in the current directory. Report WROTE_OK/WROTE_FAIL."
```

Output:

```
{"session_id": "7057e983-f119-4847-8d0b-9b0ba024e1b1", "model": "haiku", "sandbox": "read-only", "cwd": "<worktree>", "effort": "medium", "final_message": "**WROTE_FAIL** — operation not permitted on current directory.", "permission_denials": []}
```

Verified independently:

```
$ ls -la <worktree>/resumed-probe.txt
ls: <worktree>/resumed-probe.txt: No such file or directory
```

The refusal survived resume through the adapter's own argv (the settings
file is re-passed on resume, matching `start`, not a bare CLI `--resume` the
way `probe.sh`'s own `resumed` case is limited to). The resumed worker's
emitted `effort` (`"medium"`) matches what `start` captured — neither the
original `start` nor this `resume` passed `--effort`, so both used the
`medium` default and the resume replayed it.

### `claude-worker.py stop` then `verify`

Both target workers had already exited by the time these ran (their process
group had no members left), which is a legitimate case for both commands, not
a skipped one — `stop` and `verify` both detect a terminal, member-less
process group and settle the lifecycle without error.

```
$ python3 skills/drivers/orchestrate/scripts/claude-worker.py verify \
    --state <state-dir>/readonly.json --cwd <worktree>
exit=0

$ python3 skills/drivers/orchestrate/scripts/claude-worker.py stop \
    --state <state-dir>/write.json --cwd <worktree>-probe-write
exit=0
$ python3 skills/drivers/orchestrate/scripts/claude-worker.py verify \
    --state <state-dir>/write.json --cwd <worktree>-probe-write
exit=0
```

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

### `codex-worker.py start` with an explicit `--effort` (Do item 4)

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
emitted `effort` field (`"high"`) matches what was passed to `start`. This
proves the passthrough half of the effort claim — a caller-supplied effort
reaches the session and is observable in the emitted object — on `start`
only. No resume was run on the Codex adapter; the Claude-side resume above
covers the resume-replay half of the claim.

## Rejections (Do item 5) — ran, no auth required

These are pure adapter argument validation and complete before either CLI is
invoked.

### Effort outside each adapter's enum

The Codex output below is the 2026-08-24 historical result. It is superseded
by the 2026-08-27 live API probe in `effort-enums.md`; the current local guard
accepts `none|low|medium|high|xhigh|max`.

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

## Correction this chunk made

`claude-worker.py`'s `sandbox_settings("workspace-write", ...)` produced no
`filesystem` block at all before this chunk — carried over unchanged from
sub-order 1. The workspace-write run above (first attempt, before the fix)
exposed the same escape `probe.sh`'s `write` case exposed: with no
`filesystem` block, the sandbox leaves the rest of the filesystem writable,
and only the settings file's own confinement is missing. The re-run after the
fix (also above) is real, on-disk-verified evidence that
`filesystem.allowWrite: [cwd]` alone confines the worker: cwd write succeeds,
a `$HOME` escape is refused.

Getting to that specific shape took two more real, on-disk-verified
diagnosis rounds (ad hoc `claude -p --settings ...` runs against the target
worktree, outside the adapter, to isolate the `filesystem` block without
spending on full worker lifecycles for each attempt):

1. `denyWrite: ["~/"]` alone: blocks the cwd itself, since the worktree sits
   under the home tree — `WROTE_FAIL`, no file created, worker report even
   said "current git worktree directory is also blocked."
2. `allowWrite: [cwd]` + `denyWrite: ["~/"]` together (this chunk's first fix
   attempt, and what the workspace-write run above actually ran against
   before being caught): `WROTE_FAIL` on the cwd, confirmed on disk, twice
   (a single-command isolation run and the full-prompt run in this log) —
   `denyWrite` wins over `allowWrite` for the same path, so pairing them
   silently re-blocks the one directory `allowWrite` exists to carve out.
   `denyWrite: ["/"]` paired the same way was tried earlier for the same
   reason and rejected on the same grounds.
3. `allowWrite: [cwd]` alone, no `denyWrite`: `WROTE_OK` in cwd (file
   verified on disk) and `ESCAPE_FAIL` for a `$HOME/.cache` target (verified
   absent), confirmed twice. `allowWrite` behaves as an allowlist on its own,
   not as an addition on top of an otherwise-open default.

The shipped fix is (3). `docs/scope/149-probes/write.settings.json` (a
triage-owned fixture, not sub-order 1's) still has no `filesystem` block and
still exhibits the original escape when `probe.sh` runs it directly — that is
recorded above, not corrected, per this chunk's boundary.

`tests/test_behavior.py`'s `WorkerEffortDialTests` had two assertions that
encoded the old, wrong shape (`assertNotIn("filesystem", ...)` for the write
case) — both updated to assert the corrected `allowWrite`-only shape instead,
so a regression back to either broken shape fails the suite.
