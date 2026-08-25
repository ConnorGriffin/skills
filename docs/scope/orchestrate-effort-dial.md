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

Write worker (same permission mode, sandbox on, no denyWrite) wrote inside its cwd and was
refused a write into `$HOME`, matching Codex `workspace-write`. Its writable region is the
cwd plus the session temp directory: an escape probe aimed at a path under `/private/tmp`
succeeded, and the same probe aimed at the home directory was refused. An explicit
`denyWrite: ["/"]` is not the fix — measured, a broad deny beats a narrower `allowWrite`
for the cwd and blocks the worker entirely.

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

## Cold panel — round 1 (two Opus reviewers, 2026-08-24)

Eighteen blocking objections, every citation reproduced against the repo. The ones that
changed the order rather than its wording:

* The shared lifecycle machinery is ~550 of `codex-worker.py`'s 596 lines and is
  model-agnostic. This ticket creates the charter's second caller, so the seam is earned
  now: a shared module, not a second copy.
* Effort cannot survive `resume` as the schema stands — `BASE_STATE_FIELDS`
  (`codex-worker.py:121`) rejects unknown keys and the resume argv (`:469`) carries no
  effort. Persisting it is a schema change the order has to authorize.
* "Prompt on stdin" is a claude-worker fact; `codex-worker.py` takes its prompt
  positionally (`:584`) and no chunk changes that.
* The two CLIs do not share an effort enum. Captured in `149-probes/effort-enums.md`.
* Write confinement was asserted, not measured. Measuring it refuted the claim as written
  (see above) and corrected both the ADR and this ledger.
* The ban stranded `research` and `codebase-design`, which dispatch through banned paths
  today and were on no convert-later list.
* Agent-tool coupling survives outside Routing step 5, at `SKILL.md:63` and `:103`.

Refuted, not forwarded: that the committed `write.settings.json` had never been executed.
`probe.sh` runs the committed files; what was missing was captured output, now in
`output.txt`.

## Open questions

(none — sequencing and shape settled below)

## Cold panel — rounds 2 and 3

Round 2 (fresh Opus, no round-1 context): 7 blocking. The order commits raw run output,
which `scripts/validate.py` forbids as a literal user path in any tracked file and re-greps
across every reachable commit — one such commit fails the gate permanently, and this repo is
pinned by commit. The lifecycle move silently defeats ~42 `mock.patch.object` sites (122
`WORKER_MODULE` references) and breaks the test module at import, because
`spec_from_file_location` does not put the script's directory on `sys.path`. Effort had no
emitted field, so its replay could only be taken on a worker's word. The `STATE_VERSION`
branch offered was self-contradictory: `BASE_STATE_FIELDS.issubset(state)` at `:125` makes a
key mandatory, not permitted.

Round 3 (fresh Opus, cap): 4 blocking, all executability. A second
`spec_from_file_location` load yields a different module object, so the round-2 fix would
itself patch nothing. `run_lifecycle`/`run_portable` are not model-agnostic — they call
codex's parser and `emit`, and both launch paths hard-wire `stdin=DEVNULL` while the claude
adapter must write its prompt to stdin — so the module needs a named parse/emit/stdin seam
the order had not specified. A module-global `fail()` prefix is last-writer-wins across two
adapters in one test process. And effort replay on `--resume` was unmeasured.

Measured in response: `session: resume_accepts_effort=True`. The seam, the module identity,
and the per-call prefix are now ruled in the order.

Every round's blockers clustered on one thing: extracting the shared lifecycle module.

## Settled after the panel

* Sequencing: #144 and #145 land after #149 and inherit the adapter surface. #145's
  document is renamed so it cannot be confused with this ticket's `dispatch-claude.md`.
* Shape: two serial chunks re-cut on the anchor row's own boundary — build, then run
  live and correct.

## Spawned tasks

* #150 — extract the shared worker lifecycle into one module (the deferred half of #149)
* #151 code-review, #152 plan-review, #153 persona-review, #154 ticket, #155 epic,
  #156 research, #157 codebase-design — convert each skill's dispatch to the adapters

## Dispositions

* ADR — written: docs/adr/adr-149-pack-owned-model-dispatch.md
* Issues — filed: #150 through #157
* Work order — posted on #149; ticket labelled `ticket:triaged`

None outstanding.
