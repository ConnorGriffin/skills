# Codex UI parent dispatch (v0)

Use this adapter only when the interactive coordinator is a Codex UI parent.
All delegated exploration, implementation, review, and follow-up work runs
through the executable helper; do not use native `spawn_agent`. CLI workers are
the validated path and let the coordinator enforce both `cwd` and sandbox.

Run `skills/drivers/orchestrate/scripts/codex-worker.py start` for a new worker. Give
read work a resolved repository or worktree path and `--sandbox read-only`.
Give write work a resolved isolated worktree path, `--sandbox workspace-write`,
and the coordinator checkout in `--control-checkout`; the helper rejects the
control checkout. Persist one state file per worker. Use `resume` with that
state file for retry findings and ordinary follow-ups; it restores the captured
model, sandbox, and canonical cwd rather than taking replacements.

## Hosted source access

`start --network` opts the worker into provider-hosted source retrieval. The
adapter maps that capability to `-c web_search=live -c tools.web_search=true`,
persists the boolean in lifecycle state, replays it on `resume` without a
replacement flag, and reports it in successful output. Omitting the option
keeps the provider argv offline and reports `network: false`; existing state
without the field remains valid and resumes offline. This capability promises
hosted web search and fetch only; shell-command networking, command egress,
private-network access, credentials, and a wider filesystem sandbox are outside
the contract.

When the worker must judge rendered evidence, pass every evidence image as a
repeated `--image /absolute/path/to/file` argument on `start`. A path mentioned
only in the prompt is not an attachment. `resume` accepts the same repeated
option when a follow-up introduces new or revised evidence. Do not dispatch a
rendered-evidence review until the selected model accepts image input and every
image the verdict depends on is attached.

The helper closes a worker's stdin itself. Any hand-rolled background `codex
exec` must redirect stdin from /dev/null (or pipe a prompt deliberately and let
it reach EOF): an inherited open stdin is a permanent pre-session hang, because
codex reads stdin for an appended `<stdin>` block and blocks until EOF even when
the prompt was passed as an argument.

On success the helper emits one public JSON object. Read its `final_message`
field as the current worker's answer; do not infer an answer from its session or
headroom metadata.

## Approval rationale

For every mandatory worker dispatch covered by an invoked Ticket or Orchestrate
workflow, the payload is the work order or task prompt plus only the repository code
and documentation needed for the delegated task, and the destination is an isolated
worker on OpenAI's Codex model service. Credentials, secrets, patient data, `.env`,
and real database contents are excluded.

Repeat that payload, destination, invoked-workflow coverage, and exclusion list in
the escalation justification. Assistant-authored rationale helps an approval guardian
match intent but does not itself create user authorization. When no invoked workflow
supplies the consent, stop and ask once before dispatch under the invoking skill's
automatic-activation rule.

## Worker liveness

When the adapter is still running but has no terminal output or session ID, wait
another minute and check again. `session_id: ""` while `lifecycle: running` is
indeterminate, not a pre-session failure. Silence, PID presence, or low parent CPU
alone does not prove a hang and does not authorize stopping the worker.

A PID appearing in `ps` proves nothing. A healthy worker accrues CPU time
within a minute and writes `~/.codex/sessions/<date>/rollout-*.jsonl` at session
start. Before trusting a long-running worker, check that `ps -o time` is growing
and that the rollout file exists; a worker with neither hung before session
start. Such a worker burned no tokens. The coordinator stops it through the
recovery below and reports; it may then relaunch into a fresh directory, so a
late-waking zombie cannot clobber the new run.

## Interrupted workers

The coordinator that launched a worker owns its recovery. Before handing a
preserved worktree to a successor, run `codex-worker.py stop --state STATE --cwd
WORKTREE`, then run `codex-worker.py verify --state STATE --cwd WORKTREE` and
require success. State is retained for interrupted, failed, and completed runs.
Only the helper's recorded dedicated process group is in scope; a successor must
never search for or clean unknown processes, tests, providers, sessions, or
descendants. `stop` and `verify` reject legacy state. Ordinary `resume` can read
a completed legacy state, but only from a terminal state with a session ID.

The adapter reports session-bound headroom only when the matching persisted
rollout contains rate limits. `unknown`, headroom at or below 5%, and rate-limit
failures block a Codex UI parent: stop dispatching and report the blocker. It
cannot switch to Claude workers. Infrastructure failures (including a missing
rollout) are dispatch failures, not evidence that a model tier failed its task.

## Served evidence and the exec bridge

Field-derived provenance (source: #130; **field-validated (provisional)**): the
exec bridge reaps long-lived and detached processes, so a server started in one
invocation is gone by the next. Instruct workers to use one invocation to start
the server, wait for LISTEN, run the check, and kill the server. Do not read
repeated served-evidence failure as a model-tier weakness; it can bias workers
toward bounded runs instead of full replays.

Field-derived provenance (source: #130; **field-validated (provisional)**): a
worker lost to `invalid JSONL on line <n>` is a dispatch failure. Its session is
unrecoverable but committed on-disk work survives; recover the worktree under
"Interrupted workers" and resume it. Do not re-route.

## Codex-only admission routes

These are the only validated initial routes in Codex-only mode, plus the one
provisional implementation-escalation exception below:

| Area | Initial route |
|---|---|
| Bounded exploration | Luna (`gpt-5.6-luna`) |
| Hermetic implementation | Terra (`gpt-5.6-terra`) |
| Plan / spec writing | Terra (`gpt-5.6-terra`) |
| Prototyping | Sol (`gpt-5.6-sol`) |
| Default brainstorming | Terra (`gpt-5.6-terra`) |
| Documentation | Luna (`gpt-5.6-luna`) |
| Implementation escalation (not an initial admission) | Sol (`gpt-5.6-sol`) — field-validated (provisional; source: #130) |

Full-system exploration, novelty-as-deliverable brainstorming, and
other unlisted admissions are **NO_VALIDATED_ROUTE** until benchmarked.
Do not invent an escalation for those admissions. Each admitted v0 route is one
validated rung: retry once in the same worker session, then stop with
**NO_VALIDATED_ROUTE**. Never escalate Terra, Luna, or Sol to Sonnet or Opus.
Pass the exact parenthesized CLI model ID to the helper's `--model` argument.

Field-derived provenance (source: #130; **field-validated (provisional)**): for
hermetic implementation only, Terra may escalate to Sol once after its
in-session retry fails. At Sol, stop and surface. This exception changes no
benchmarked ladder.

Review admissions are owned by [`review-routing.md`](review-routing.md). Its
matrix includes the Codex UI parent's routine routes and explicit-operator
exception; do not treat review as a generic admission above.

Field-derived provenance (source: #130; **field-validated (provisional)**):
Codex-only load-bearing review remains **NO_VALIDATED_ROUTE** by default. An
operator may explicitly choose the unvalidated Codex exception in
`review-routing.md`; label the resulting review unvalidated rather than
silently promoting it into the benchmark table. Rendered evidence is a transport
constraint, not a model-family ban: use the adapter's `--image` arguments and
require image-input support from the selected model. `review-routing.md` remains
the sole authority for review precedence.
