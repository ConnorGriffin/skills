# Scope — universal effort dial and Claude CLI worker dispatch (#149)

Route: interview mode (a concrete plan exists in the operator's head, untested).

## Decisions

* **Adapter surface: full parity.** `claude-worker.py` gets start/resume/stop/verify,
  one state file per worker, liveness, and group-scoped recovery, matching
  `codex-worker.py`. Why: the coordinator's recovery ownership rule in SKILL.md is
  written parent-agnostic, so a thin adapter would leave half the workers outside it.
  → issue

* **Read-only enforcement is measured, not assumed.** The contract is written around a
  mechanism proven to refuse a write in a probe run, not around a flag that reads
  right. Why: a benchmark run was already invalidated by a read-agent that wrote.
  → issue

* **Effort is a dial on both adapters.** `codex-worker.py` hard-codes
  `model_reasoning_effort=medium` today with no flag; both adapters take `--effort`.
  → issue

* **Effort defaults to medium for every model.** Why: operator ruling, 2026-08-24,
  superseding an earlier per-model split (Terra high, Luna max) on the grounds that no
  effort benchmarking has been done; values get bumped when a replay measures a reason.
  The dial exists so a coordinator can override per delegation. → ADR

* **All model dispatch defined by this pack's skills goes through this pack's
  adapters.** Not orchestrate-only: any skill that dispatches a model (code-review,
  plan-review, persona-review, ticket chunk agents, epic) dispatches through the
  adapters, never the built-in Agent tool, Workflow tool, or background agents.
  Why: operator ruling, 2026-08-24, superseding the narrower orchestrate-only option.
  → ADR

## Measured facts (this session, live)

* `claude` exposes `--effort low|medium|high|xhigh|max`, `--model`, `-p`,
  `--session-id`, `--resume`, `--permission-mode`, `--tools`, `--disallowedTools`,
  `--add-dir`, `--output-format json|stream-json`, `--max-budget-usd`.
* `--tools` and `--disallowedTools` are variadic: a trailing prompt argument is
  swallowed as a tool name. A worker adapter must pass the prompt on stdin or place it
  before those flags.
* `--permission-mode acceptEdits` still refused a new-file Write in `-p` mode.
* `--permission-mode plan` refused the write and wrote a plan file into
  `~/.claude/plans/` — a side effect outside the worker's cwd.
* Under `--permission-mode bypassPermissions`, a Haiku worker replied `DONE` while
  creating no file: a live instance of the SKILL.md warning to demand command output
  rather than trusting a reported success.

## Read-only enforcement — measured 2026-08-24 (Haiku, scratchpad dirs)

| Dispatch | Wrote the file? |
|---|---|
| `--permission-mode bypassPermissions` (baseline) | yes |
| `--permission-mode acceptEdits` | no — new-file Write still asks |
| `--permission-mode plan` | no — but wrote a plan file into `~/.claude/plans/` |
| `bypassPermissions --tools Read,Grep,Glob` | no — "Write tool is disabled" |
| `bypassPermissions --disallowedTools Write,Edit,NotebookEdit,Bash` | no |
| `bypassPermissions --disallowedTools Write,Edit,NotebookEdit` (Bash allowed) | **yes** |
| `bypassPermissions --tools Read,Grep,Glob,Bash` | **yes** |
| `--settings {"sandbox":true}` with Bash allowed | yes |
| `--settings {"permissions":{"sandbox":true,"allowUnsandboxedCommands":false}}` with Bash allowed | yes |

**Superseded.** The table above tested the wrong mechanism. Per the Claude Code
sandboxing docs, `--allowedTools` is an approval rule rather than an availability
filter, and the Bash sandbox is an object in settings with OS-level (Seatbelt/bubblewrap)
filesystem enforcement that covers a command and all its children.

### Verified sandbox pair — the real analogue of Codex sandbox modes

Read-only worker (`--permission-mode dontAsk` plus these settings) ran `ls -a`
successfully and had its bash write refused with "operation not permitted":

```json
{"sandbox": {"enabled": true, "allowUnsandboxedCommands": false,
             "filesystem": {"denyWrite": ["/", "~/"]}},
 "permissions": {"deny": ["Write", "Edit", "NotebookEdit"]}}
```

Write worker (same permission mode, sandbox on, no denyWrite) wrote inside its cwd and
nowhere else, matching Codex `workspace-write`:

```json
{"sandbox": {"enabled": true, "allowUnsandboxedCommands": false}}
```

`allowUnsandboxedCommands: false` is load-bearing: it disables the `dangerouslyDisableSandbox`
retry escape hatch, so a blocked command cannot be re-run outside the sandbox. Note that
under `dontAsk` the write worker's Write tool was itself denied and it fell back to bash —
a write worker needs its edit tools explicitly allowed.

Docs: [sandboxing](https://code.claude.com/docs/en/sandboxing),
[headless](https://docs.claude.com/en/docs/claude-code/headless),
[SDK permissions](https://docs.claude.com/en/api/agent-sdk/permissions).

## Open questions

1. Sequencing against #144 and #145, which queue edits to the same orchestrate files.
2. Shape: one chunked order on #149, or #149 builds the adapters and child issues
   convert each consuming skill.

## Spawned tasks

(none yet)
