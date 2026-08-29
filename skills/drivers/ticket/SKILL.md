---
name: ticket
description: "Drive one tracked ticket from arrival to resolution through four verbs: triage, start, revise, finalize. Use when the user says triage/start/revise/finalize with a ticket id, asks to turn a ticket into a locked brief, to execute a work order, to action a review round on a ticket's pull request, or to close out a merged ticket. Literal triage, start, or revise invocation requests the work order or task prompt plus only needed repository code and documentation for every mandatory worker dispatch, including nested review and nested Orchestrate work: to OpenAI's Codex model service for a Codex UI parent, or OpenAI's Codex model service or Anthropic's Claude model service for a Claude Code parent. For delegated workflow work, the coordinator dispatches every mandatory reviewer and resumes the same worker. Credentials, secrets, patient data, `.env`, and real database contents are excluded. Automatic activation outside an invoked parent workflow asks once before dispatch; finalize grants no worker-egress consent."
---

# Ticket

One ticket, one verb at a time. Each verb is a full procedure in `verbs/<verb>.md`;
read that file before doing anything else, then follow it. This page holds only
what every verb shares.

## Invocation

`/ticket <verb> <ticket-id>`, where verb is `triage`, `start`, `revise`, or
`finalize`. No verb or no ticket id: ask for it, one line. Unknown verb: list the
four.

Literal user invocation of `/ticket triage`, `/ticket start`, or `/ticket revise`
requests the bounded transfer needed for every mandatory worker dispatch the
selected workflow routes, including nested review and nested Orchestrate work. The
payload is the work order or task prompt plus only the repository code and
documentation needed for that delegated task. For a Codex UI parent, the destination
is an isolated worker on OpenAI's Codex model service. For a Claude Code parent,
existing routing selects an isolated worker on OpenAI's Codex model service or
Anthropic's Claude model service. Credentials, secrets, patient data, `.env`, and
real database contents are excluded.

Automatic activation outside an invoked parent workflow does not acquire this
consent. Before the first external dispatch it asks once, naming the same payload,
applicable destination or destination matrix, and exclusions; a denial stops the
workflow. `/ticket finalize` grants no worker-egress consent because it routes no
model dispatch.

## The pipeline

* `triage` reads the ticket and the repo, interviews the user through `/scope`
  when scope is thin, and ends by posting the **work order**: a locked brief as a
  ticket comment. Work too big for one agent's context is sliced into sub-orders
  in that same comment ([references/slicing.md](references/slicing.md)). It
  writes nothing to the repo except scope and spec documents committed in the
  ticket's worktree. An epic child writes only its work order; a required epic
  spec amendment is a separate docs-only pull request merged before stamping.
* `start` runs in a fresh session, fetches the work order, refuses if there is
  none, implements it on a branch in an isolated worktree (or, on a sliced order,
  coordinates one agent per chunk), iterates the verification step until the
  result matches the order's expectation, passes an adversarial review at the
  order's stamped depth ([references/review-depth.md](references/review-depth.md))
  unless `Profile: hardening` replaces it below Full depth,
  opens the pull request, and stops. Agents never merge.
* `revise` actions one review round on the open pull request: reload the ticket
  and the order, fix, re-verify, push.
* `finalize` runs after a human merged: verify the merge and post-merge workflow,
  complete the repository's post-merge archive guidance for an ordinary OpenSpec
  change, then close the ticket with a comment linking the pull request, record
  what the ticket actually cost in context, and tear the worktree down, so the
  slicing rubric is tuned against measured numbers rather than intuition.

## The tracker contract

Every tracker interaction goes through four operations: read a ticket, post a
comment on a ticket, move a ticket's status, and locate the newest work order on
a ticket. [references/tracker-contract.md](references/tracker-contract.md)
defines them, and one binding page supplies them for one tracker. GitHub issues
ship as the reference binding
([bindings/github-issues.md](bindings/github-issues.md)).

The procedures below and in `verbs/` call the contract, never a tracker's API
directly. A verb that cannot reach the contract stops and names what is missing.

## Review front door

`start` and `revise` reach code review as `/review` on the changed code, which
routes to `code-review`. Neither verb calls a reviewer any other way, and neither
substitutes a lighter check for the depth the order stamped. Below Full depth under
`Profile: hardening`, [start](verbs/start.md) and [revise](verbs/revise.md) use its
exception instead.

## Delegation authority

This authority covers triage's mandatory `/plan-review` and start/revise's `/review` route. Invoking `/ticket` authorizes every sub-agent dispatch that this procedure marks mandatory, including the coordinator's mandatory reviewer dispatch. Do not ask again solely because a session-level preference says "do not spawn agents"; apply that preference to discretionary delegation only. An explicit task-level refusal of this required review or revocation of delegation overrides this authorization: stop and state that the requested workflow cannot run without its required independent review.

When Ticket work is delegated, the delegation prompt identifies the
mandatory-review handoff. At that boundary the worker returns or writes its
review-ready result through the coordinator-recorded durable result locator and
does not launch a reviewer. The coordinator dispatches every mandatory reviewer
through the existing adapter after collecting the result, verifies the returned
verdict, and resumes the same worker. Actionable findings resume it for correction; a
verified clean verdict resumes it to finish. A failed launch, nonzero exit,
missing result artifact, or missing verdict is reported as unavailable and blocks
the workflow from advancing as reviewed. Direct nested adapter dispatch by the
worker is unsupported.

## Shared rules (every verb)

1. **Open with the ticket summary.** Before any other work, read the ticket and
   give the user an extremely high-level, human-readable summary: what the ticket
   is and what this verb is about to do on it (as simple as "implementing
   `<ticket-id>`, which is `<one-line description>`"). Then mark a chapter titled
   `<ticket-id> <verb>` when the harness offers a chapter tool, so the user can
   scroll back to it. Skip the chapter silently when it does not.

2. **Claim the session.** Immediately after the ticket summary, run
   `python3 <ticket-skill-directory>/scripts/ticket.py claim <ticket-id> --verb
   <current verb>`, so the
   sessions that worked this ticket are recorded as they work it rather than
   guessed from prose afterwards. Pass `--session` and `--agent` whenever the
   environment cannot answer on its own: no session id in it, or more than one,
   which is what a worker launched from another agent's session sees. Pass
   `--role` to say what the session is doing on the ticket: `coordinator` (the
   session driving the ticket, and the default), `worker` (an agent building one
   chunk), or `reviewer` (a session that only reviews). The role decides which
   costs are evidence about how big the work was, so a session claimed under the
   wrong one is a measurement error. The required `--verb` is `triage`, `start`,
   `revise`, or `finalize`, matching the lifecycle verb this session is running.
   One session serves one lifecycle verb: same-verb resumes reuse the claim, while
   changing verbs requires a fresh session. A cross-verb re-claim keeps and prints
   the persisted claim, reports the persisted and submitted verbs as one visible
   conflict, and exits successfully; telemetry never claims the submitted metadata
   landed. A claim that fails is said in one
   line and never blocks the verb: telemetry is a measurement, not a gate. A
   sandboxed session (a Codex `workspace-write` sandbox, for one) that cannot
   write the claims file under `~/.config/ticket/` sees that one-line denial
   name the path and the fix: rerun the same claim command outside the sandbox
   or with escalated permissions.

3. **Attribution first.** Every comment this skill posts opens with a one-line
   quote block. With an operator name configured:

   > Written by an AI agent operating for `<operator>`. Verify before relying on it.

   With none configured:

   > Written by an AI agent. Verify before relying on it.

   The name comes from `~/.config/ticket/config.json`, key `operator`. No file, no
   key, or an empty value all mean the nameless form. Then the content. Never post
   an unattributed comment.

4. **The lock is the only entry to execution.** A work order is a ticket comment
   whose body contains a fenced block starting `WORK ORDER`. `start` and `revise`
   locate it by scanning the ticket's comments newest-first; the newest one wins.
   No order, no execution: refuse and route to `/ticket triage <ticket-id>`.

5. **One worktree, one branch, per ticket, for the whole lifecycle.** `triage`
   cuts the branch and worktree through `spin-worktree`; `start` and `revise`
   reuse them; `finalize` tears them down. The first repository action after the
   summary-and-claim opening, before grounding or any repo read, is to cut or
   reuse the ticket's worktree. Outside an epic child, grounding, scope ledgers, and
   the active change record are written and committed there; post-merge archiving
   follows `operations.archive.guidance` on `main`. An epic child keeps its
   instrumentation in session scratch and relies on its parent record. The control checkout may be dirty, stale, or
   on another branch: its working tree is never read or written, and it never
   switches branches. Never commit, stash, move, or clean its files, and never
   substitute another task's worktree as the control checkout. It holds the
   ticket's branch ref, which is what the worktree is cut from. Before its first
   write, every verb confirms that its working directory is the path the worktree
   helper reported; a mismatch stops the verb.
   A chunked order is the one exception and does not loosen the rule: chunk agents
   work in per-chunk worktrees cut from the ticket branch and torn down as each
   chunk merges back into it, so the ticket still ends with one branch and one
   pull request ([references/coordinator-mode.md](references/coordinator-mode.md)).

6. **Working state lives on the ticket.** No plan files and no scratch
   directories on the branch. Outside an epic, the branch carries shipping code plus
   the repo's own change record; an epic child carries shipping code only and its
   parent epic owns the record.

7. **Ground in what the repo already says.** Read the repo's own decision and
   change records, `docs/`, and recent `git log` before forming opinions. Read the
   standing-decisions source named below when a project configured one.

8. **Status transitions.** Verbs move the ticket: `triage` to triaged, `start` to
   in progress when the branch is cut, `start` to pending review when the pull
   request opens, `finalize` to done. Status is the contract's one non-fatal
   operation: when a move is unavailable or fails, say so in one line and
   continue. Never retry a failed move and never force a workaround.

9. **Stop at the pull request boundary.** Opening the pull request ends `start`.
   Merging is human. `finalize` only runs after a human merged.

10. **Fresh-session contract.** `start` assumes no memory of triage. Everything it
   needs must be on the ticket, in the description plus the work order. If it is
   not there, that is a triage defect: refuse and say what is missing.

## The verification step

Every order names one verification step and one expectation for its output. The
step is a slot:

* **Default:** the target repo's own lint and tests, discovered from the repo. Read
  its `AGENTS.md` or `CLAUDE.md` for a test command, then its CI workflows, then
  its package scripts. Name the command in the order.
* **A binding may fill the slot with something stronger.** An infrastructure
  preview is the worked example: a read-only plan against real state, run locally
  before the pull request. When a binding fills the slot, the order's expectation
  line describes that tool's output instead of a test result.
* **The rule that survives either way:** iterate locally until the result is
  exactly what the order's expectation says. CI is the check of record, not the
  iteration loop.
* **Never fabricate expected output.** When verification cannot run at all (no
  credentials, no access, no runnable suite), say so, open the pull request as a
  draft, and name the missing evidence.

## The graph identity

Before a verb reads code structurally, it binds its current checkout to exactly one
Codebase Memory project, from that checkout's own path:

```sh
python3 <cbm-onboard-skill-directory>/scripts/cbm-lifecycle.py ensure <worktree path>
```

It prints one object, and the verb reports it verbatim:

```json
{"root_path": "<canonical physical checkout>", "project": "cbm-onboard-v1-<sha256>", "status": "ready"}
```

* `ready` or `indexed`: query the graph as exactly that `project`. Never pick the
  graph by project name, branch-like label, list order, apparent recency, or because
  it was the only result.
* `unavailable` (exit 2): no usable Codebase Memory here, so say so in one line and
  use ordinary discovery for the rest of the session.
* Any other failure (exit 1): stop the verb and report what `ensure` printed on
  stderr, which names the cause — a path that is not a checkout, or an installed
  tool answering for the wrong project or root. Neither is a case where guessing a
  graph is safe.
* The command never ran at all, no exit code, because the harness or sandbox
  refused it (a permission classifier declining the Bash call, for example): say so
  in one line and use ordinary discovery for the rest of the session, the same as
  `unavailable`.

Every session recomputes this from the checkout it just verified, never from chat
memory or a remembered earlier run. It names one machine's paths, so it never goes
into a work order or any other tracker comment; a chunk agent is handed its own in
its prompt.

Before Git removes a worktree this skill authored, the same directory's
`cbm-teardown.sh` deletes that checkout's project, while the checkout still exists
for the identity to be derived from. Teardown fails loudly on a machine with no
Codebase Memory installed, which is expected: report it in one line and carry on
with the removal. It never holds up the removal, and it is never retried.

## The hardening profile

The target repo declares `Harden: <command>` beside its test command in repo facts.
Triage stamps `Profile: hardening` only when that line exists.
It replaces the review rounds as [start](verbs/start.md) and [revise](verbs/revise.md) specify.
A hardening command that cannot run is an error, never a pass.
The profile order's QA script lives in its pull request body.

## Standing decisions

A project may point this skill at a knowledge base of standing decisions and
traps to read before grounding in the repo. Its location is the project's to
name: a path in the repo, a file the operator configured, or a page the binding
knows about.

Absent, the verb says so in one line and continues. It never refuses a ticket for
want of it.

## The change record

The skill records the change where the target repo already records changes.

An **epic child** creates, revises, and records no per-child change record. Its
parent epic owns the active change and its post-merge archive; the child leaves
that change active and records no child change.

Outside an epic, follow this per-ticket rule:

1. The repo has an OpenSpec layout (`openspec/`): write the change folder on the
   ticket branch (`proposal.md`, `tasks.md`, and `design.md` when the work
   embodies a real decision). Start and revise keep the active change and its
   deltas reviewable in the ticket pull request; they do not fold or archive it
   before merge. The repository's `operations.archive.guidance` determines when
   finalization archives a verified merge. `/openspec-adopt`, when it is installed,
   is what adopts OpenSpec in a repo that lacks it. OpenSpec is the worked example,
   never a requirement.
2. The repo has a different convention (a changelog, a decision-record tree, a
   design log): follow that convention exactly as the repo already uses it.
3. The repo has no convention: write down what changed and why, where that repo's
   readers would look. Do not invent a convention for it.
