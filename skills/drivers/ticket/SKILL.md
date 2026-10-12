---
name: ticket
description: "Drive one tracked ticket from arrival to resolution through four verbs: triage, start, revise, finalize. Use when the user says triage/start/revise/finalize with a ticket id, asks to turn a ticket into a locked work order, to build a locked ticket to a pull request, to action a review round on a ticket's pull request, or to close out a merged ticket."
---

# Ticket

One ticket, one verb, one artifact per stage, a human at every gate.

| Verb | Produces | Human gate after it |
|---|---|---|
| [triage](verbs/triage.md) | a locked work order posted on the ticket | the user approves the order before it posts |
| [start](verbs/start.md) | an open pull request | a human reviews |
| [revise](verbs/revise.md) | one review round pushed | a human reviews again or merges |
| [finalize](verbs/finalize.md) | the ticket closed, the change archived, the cost recorded | a human merges the archive pull request |

`/ticket <verb> <ticket-id>`. No verb or no id: ask, one line. Unknown verb: list the
four. Read the verb's page in full before acting on it.

**Agents never merge.** Not the implementation pull request, not the archive pull
request, not after green CI. Merging is the human's gate.

## Shared rules

1. **Open with the ticket.** Read it and tell the user in one line what it is and what
   this verb will do. Mark a chapter `<ticket-id> <verb>` when the harness has a
   chapter tool.
2. **Claim the session**, so finalize can measure what the ticket cost:
   `python3 <ticket-skill-directory>/scripts/ticket.py claim <ticket-id> --verb <verb>`.
   Pass `--session`/`--agent` when the environment carries no session id, and `--role
   reviewer` for a session that only reviews. Each verb runs in its own fresh session.
   A failed claim is one line and never blocks the verb.
3. **Attribute every comment.** Open each tracker comment with
   `> Written by an AI agent operating for <operator>. Verify before relying on it.`
   The name comes from `~/.config/ticket/config.json` key `operator`; without one, drop
   ` operating for <operator>`.
4. **One worktree and one branch per ticket, for the whole lifecycle.** Triage cuts
   them fresh off the up-to-date remote base; start and revise reuse them; finalize
   tears them down. Never read, write, stash, or switch the control checkout, even when
   it is dirty. Confirm the working directory is the ticket worktree before the first
   write.
5. **The tracker is the source of truth for status.** Triage moves the ticket to
   triaged, start to in progress and then pending review, finalize to done. A failed
   move is said in one line and never retried.
6. **Ground in the repo first.** Its `AGENTS.md`/`CLAUDE.md`, decision and change
   records, `docs/`, recent `git log`, and CI workflows. A project may name a
   standing-decisions source; read it when it exists and say so in one line when not.
7. **Stay inside the selected ticket.** A verb may write the ticket's worktree, branch,
   active change, comments, and status, plus operator-local state the workflow needs
   (claims, fetched refs). Anything outside that (another branch,
   issue, pull request, or repository artifact) needs the user to approve that exact
   target and mutation first. Reading something for grounding never grants writing it.

## Delegation authority

Invoking `/ticket` authorizes every sub-agent dispatch that this procedure marks mandatory: triage's mandatory `/plan-review` at Full depth and the `/code-review` pass in start and revise. Do not ask again solely because a session-level preference says "do not spawn agents"; apply that preference to discretionary delegation only. An explicit task-level refusal of this required review or revocation of delegation overrides this authorization: stop and state that the requested workflow cannot run without its required independent review.

Delegate build work per `profile/base.md` "Delegating to subagents": name the model,
isolate an implementer in the ticket worktree, and demand the full verify output. The
coordinator dispatches every reviewer and resumes the same worker with `SendMessage`;
a worker never launches its own reviewer. A review that fails to launch or returns no
verdict is unavailable, never clean, and the ticket does not advance as reviewed.

## Review depth

Triage stamps one depth with a one-line reason; start and revise review at it.

| Depth | The reviewer checks | Fits |
|---|---|---|
| Focused | the exact change, and that nothing else moved | a value change, a version bump, a typo |
| Targeted | the changed behavior end to end and the repo rules that govern it | most tickets |
| Full | the whole diff, every check the repo defines, adversarially | the floor below, or anything wide |

**Sensitivity floor.** Authentication or authorization, secrets, destructive or
irreversible operations, and behavior shared across an organization are Full,
whatever the size. Depth escalates when the diff proves wider than the stamp and never
downgrades. A missing stamp reviews as Targeted. A finding blocks only when it breaks
the order's `Done when`, its verification expectation, or a named repo rule.

**Hardening profile.** When the target repo declares `Harden: <command>` and the user
asks for it, triage stamps `Profile: hardening`. Start and revise then run `/simplify` and
the `Harden:` command until it exits 0 (three passes at most, residue listed in the pull
request), and run `/code-review` only at Full depth. A `Harden:` command that cannot run
is an error, never a pass.

## The change record

Record the change where the repo already records changes. In an OpenSpec repo that is
an active change on the ticket branch (`proposal.md`, `tasks.md`, spec deltas, and
`design.md` when a decision needs one); it rides the pull request unarchived, and
finalize archives it after the merge. Whoever executes ticks `tasks.md` as items are
done and verified. A repo with another convention follows it; a repo with none gets a
note where its readers look. Never invent a convention.

## The tracker contract

Verbs call four operations, never a tracker's API directly. One binding page supplies
them; GitHub issues is the shipped one ([bindings/github-issues.md](bindings/github-issues.md)).

1. **Read** a ticket: title, body, parent, labels, and comments with creation times.
2. **Post** a comment. On failure, print the body so nothing is lost, then stop.
3. **Move** status to triaged, in progress, pending review, or done. A move to triaged
   carries the classification; `code` also ensures the `build` label, and a failure
   there skips `ticket:triaged`.
4. **Locate** the newest work order: the newest comment whose fence opens
   `EXECUTION LOCK ` (any version) or the legacy `WORK ORDER`. Newest by post time wins;
   no field is ever merged from an older comment.

A binding for another tracker is one page with the same four operations, the command
for each, what it needs installed, and the message it prints when that is missing. It
never falls back to another tracker or a local substitute.
