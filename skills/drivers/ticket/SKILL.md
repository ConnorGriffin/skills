---
name: ticket
description: "Drive one tracked ticket from arrival to resolution through four verbs: triage, start, revise, finalize. Use when the user says triage/start/revise/finalize with a ticket id, asks to turn a ticket into a locked brief, to execute a work order, to action a review round on a ticket's pull request, or to close out a merged ticket. Invoked as /ticket <triage | start | revise | finalize> <ticket-id>."
---

# Ticket

One ticket, one verb at a time. Each verb is a full procedure in `verbs/<verb>.md`;
read that file before doing anything else, then follow it. This page holds only
what every verb shares.

## Invocation

`/ticket <verb> <ticket-id>`, where verb is `triage`, `start`, `revise`, or
`finalize`. No verb or no ticket id: ask for it, one line. Unknown verb: list the
four.

## The pipeline

* `triage` reads the ticket and the repo, interviews the user through `/scope`
  when scope is thin, and ends by posting the **work order**: a locked brief as a
  ticket comment. Work too big for one agent's context is sliced into sub-orders
  in that same comment ([references/slicing.md](references/slicing.md)). It
  writes nothing to the repo except scope and spec documents committed in the
  ticket's worktree.
* `start` runs in a fresh session, fetches the work order, refuses if there is
  none, implements it on a branch in an isolated worktree (or, on a sliced order,
  coordinates one agent per chunk), iterates the verification step until the
  result matches the order's expectation, passes an adversarial review at the
  order's stamped depth ([references/review-depth.md](references/review-depth.md)),
  opens the pull request, and stops. Agents never merge.
* `revise` actions one review round on the open pull request: reload the ticket
  and the order, fix, re-verify, push.
* `finalize` runs after a human merged: close the ticket with a comment linking
  the pull request, tear the worktree down, and record what the ticket actually
  cost in context, so the slicing rubric is tuned against measured numbers rather
  than intuition.

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
substitutes a lighter check for the depth the order stamped.

## Shared rules (every verb)

1. **Open with the ticket summary.** Before any other work, read the ticket and
   give the user an extremely high-level, human-readable summary: what the ticket
   is and what this verb is about to do on it (as simple as "implementing
   `<ticket-id>`, which is `<one-line description>`"). Then mark a chapter titled
   `<ticket-id> <verb>` when the harness offers a chapter tool, so the user can
   scroll back to it. Skip the chapter silently when it does not.

2. **Claim the session.** Immediately after the ticket summary, run
   `python3 <ticket-skill-directory>/scripts/ticket.py claim <ticket-id>`, so the
   sessions that worked this ticket are recorded as they work it rather than
   guessed from prose afterwards. Pass `--session` and `--agent` whenever the
   environment cannot answer on its own: no session id in it, or more than one,
   which is what a worker launched from another agent's session sees. A claim that fails is said in one
   line and never blocks the verb: telemetry is a measurement, not a gate.

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
   reuse the ticket's worktree. Grounding, scope ledgers, and change records all
   happen and get committed there. The control checkout may be dirty, stale, or
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
   directories on the branch. The branch carries shipping code plus the repo's own
   change record, nothing else.

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

* `ready` or `indexed`: query the graph as exactly that `project`. Never choose one
  by basename, branch, recency, list order, or because it was the only result.
* `unavailable` (exit 2): no usable Codebase Memory here, so say so in one line and
  use ordinary discovery for the rest of the session.
* Any other failure (exit 1): stop at that boundary rather than reading a different
  repository's graph.

Every session recomputes this from the checkout it just verified, never from chat
memory or a remembered earlier run. It names one machine's paths, so it never goes
into a work order or any other tracker comment; a chunk agent is handed its own in
its prompt.

Before Git removes a worktree this skill authored, the same directory's
`cbm-teardown.sh` deletes that checkout's project, while the checkout still exists
for the identity to be derived from. A teardown failure is reported in one line and
does not hold up the removal.

## Standing decisions

A project may point this skill at a knowledge base of standing decisions and
traps to read before grounding in the repo. Its location is the project's to
name: a path in the repo, a file the operator configured, or a page the binding
knows about.

Absent, the verb says so in one line and continues. It never refuses a ticket for
want of it.

## The change record

The skill records the change where the target repo already records changes.

1. The repo has an OpenSpec layout (`openspec/`): write the change folder on the
   ticket branch (`proposal.md`, `tasks.md`, and `design.md` when the work
   embodies a real decision), and fold it into the baseline in the order's last
   pull request. `/openspec-adopt`, when it is installed, is what adopts OpenSpec
   in a repo that lacks it. OpenSpec is the worked example, never a requirement.
2. The repo has a different convention (a changelog, a decision-record tree, a
   design log): follow that convention exactly as the repo already uses it.
3. The repo has no convention: write down what changed and why, where that repo's
   readers would look. Do not invent a convention for it.
