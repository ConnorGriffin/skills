# ADR 149 — Pack-owned model dispatch, with effort settable everywhere

Status: accepted (2026-08-24)

## Context

`/orchestrate` dispatches Claude models through the harness's built-in Agent tool and
Codex models through `skills/drivers/orchestrate/scripts/codex-worker.py`. The two
paths are not comparable:

* The Agent tool takes a model override and nothing else. A Claude worker silently
  inherits the coordinator session's reasoning effort, and no skill can raise or lower
  it. The `claude` CLI does take `--effort low|medium|high|xhigh|max`.
* `codex-worker.py` pins `model_reasoning_effort=medium` as a hard-coded constant with
  no flag, so effort is unsettable on that side too — just unsettable in a different way.
* The Codex adapter enforces `cwd` and a sandbox mode; the Agent tool enforces neither,
  so read-only for a Claude worker rested on an agent type plus a sentence in the prompt.
  A benchmark run was already invalidated by a read agent that left a patch applied.

`references/dispatch-codex.md` already bans native `spawn_agent` for a Codex UI parent
on exactly these grounds. Nothing said the same about Claude's built-in dispatch.

## Decision

**All model dispatch defined by this pack goes through this pack's own adapters.** Any
skill here that dispatches a model — `orchestrate`, `code-review`, `plan-review`,
`persona-review`, `ticket`'s chunk agents, `epic` — dispatches through `codex-worker.py`
or the new `claude-worker.py`. The built-in Agent tool, the Workflow tool, and background
agents are not dispatch paths for delegated work.

**Both adapters take `--effort`, defaulting to `medium` for every model.** The dial exists
so a coordinator can override per delegation. The default is uniform because no effort
benchmarking has been done: the 2026-08-03 replay scored every Codex run at medium and
never varied the dial. A per-model default is a benchmark result, not a preference, and
gets set when a replay measures one.

**A Claude worker's sandbox mode is enforced by the OS, not by the prompt.** Read-only and
write configurations are the committed, executed artifacts under `docs/scope/149-probes/`,
verified 2026-08-24: the read-only worker keeps a working shell and has its writes refused
by Seatbelt; the write worker writes inside its cwd and nowhere else. `allowUnsandboxedCommands:
false` is part of the contract — it disables the `dangerouslyDisableSandbox` retry, so a
blocked command cannot be re-run outside the sandbox.

## Consequences

* Effort becomes a routing dial the table can carry, without changing any stamped route.
  Changing a default still requires a benchmark replay.
* A Claude worker gains what the Codex side already had: enforced `cwd`, an enforced
  sandbox mode, resumable sessions, and coordinator-owned recovery.
* Consuming skills convert one at a time behind their own issues; until a skill is
  converted it keeps its current dispatch, and the ban binds it once its issue lands.
* The pack takes on a second worker script to maintain, and both adapters now track a
  CLI surface that can change under them.
