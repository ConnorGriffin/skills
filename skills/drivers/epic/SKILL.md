---
name: epic
description: "Coordinate an OpenSpec epic and clear child tickets through a GitHub-backed planning lifecycle. Use when an effort needs multiple attended sessions, recorded decisions, spikes, or independently shippable builds."
---

# Epic

`$epic` maintains one OpenSpec-backed epic from its first uncertainty through human-verified close-out. It plans and coordinates; clear implementation belongs in ordinary child tickets and runs through `$ticket`.

## Authority and boundaries

An epic lives at `openspec/changes/<epic-slug>/`. Its `proposal.md`, `design.md`, and `tasks.md` form the OpenSpec authority: proposal owns destination and scope; design owns risk, durable decisions, and named open questions; tasks owns the checked implementation sequence and links to every child issue. Live tracker state is truth for child type, status, dependencies, deferral, and closing pull requests. Do not create a derived index of that state.

Route every tracker operation through the installed binding. [bindings/github-issues.md](bindings/github-issues.md) is the shipped default. Read [the tracker contract](references/tracker-contract.md) before the first tracker action. A tracker, authentication, or Git failure stops the current operation visibly; do not guess or repair authoritative state locally.

The home session owns the epic. It stays at planning altitude, files and reads issues, and keeps the active change coherent. Build and triage sessions report in ticket comments and pull requests. Coordinators do not nest.

## Start and maintain an epic

1. Confirm the target repository already has OpenSpec. Otherwise run `$openspec-adopt` as a separate documentation-only pull request.
2. Create one active change with its proposal, design, and tasks. Create the epic issue with the `epic` label and its native child issues. Add each child issue link to `tasks.md` in the implementation sequence; do not duplicate live tracker fields there.
3. Re-read relevant live tracker state before each mutation. Update the change when destination, design, or checked sequence changes; preserve child type, status, dependencies, deferral, and closing-pull-request facts on the tracker.
4. Keep every imprecise concern as a named open question in `design.md`. Clear an open question only by recording its decision in `design.md` or promoting it to a tracker spike; never silently delete it. Do not add pointer-only Notes: owning skills and repository rules remain discoverable at their authoritative homes.

## Admit work deliberately

File a spike when an open question is precise but not yet resolved. A spike can be research, interview, mockup, or a human prerequisite. File a build only as a bounded refusal: refuse to file a build while an open spike or named open question can invalidate its outcome, constraints, or acceptance criteria.

Before filing a build, require every relevant load-bearing ruling in the repository's ADR home. User-facing work also requires a locked `/ui-craft` spec. The build issue must stand alone and receive the normal `$ticket` triage flow; the epic does not manufacture a work order.

Use native `blocked-by` edges for actual dependencies. A follow-up required to reach the epic destination is an in-scope native child. A follow-up outside that destination is also filed as a native child, receives its `spike` or `build` type plus `deferred`, and is reported on the originating ticket. Ordinary builds still receive `build` from ticket triage.

## Delegated execution

The operator may explicitly and revocably delegate a locked epic subtree to
the home session when every order is stamped or every needed ruling is settled.
Attended sessions remain the default; any newly opened decision returns that
subtree to attended mode.

For delegated triage the home session dispatches a worker through the existing `$ticket triage` interface; for a
delegated build it dispatches a worker through the existing `$ticket start`
interface. Those workers use their existing ticket contracts and post stamped
work orders, session-fit, and completed work products through tracker comments.

The home session dispatches only through the pack adapters, with prompt text
passed positionally from coordinator-owned session-scratch prompt files and one
coordinator-owned state file per dispatch. Do not add adapter flags or alter
adapter mechanics.

Work delegated to the home session proceeds in waves. Before each fan-out, draw
a conflict map from the queued expected diffs and verify that the shared checkout
equals the current origin default-branch tip. Fan out every read-only draft and
review in parallel. Serialize only write-bearing triage and build steps whose
expected diffs overlap; builds use per-issue worktrees, tickets editing the same
files run in order, and pull requests merge one at a time with a rebase when a
shared surface is touched. Before dispatching a build or review worker, verify
that its target worktree is at, or descends from, the current origin
default-branch tip; refuse a stale target.

Collect child results under `orchestrate`'s `## Collect child results` section.
Permit a human merge only after green CI and passed review. Surface a failure
after the applicable routing ladder is exhausted; do not retry past that ladder.

## Resolve spikes

For a research spike, run `$research` in a temporary per-spike worktree. The worker returns the required Markdown findings to the home session. The home session writes the Markdown file required by its public interface, posts that returned content under the exact heading `## Findings`, verifies the `## Findings` comment, removes the temporary worktree and its unshipped file, and only then closes the spike.

Close the spike issue only after that verification. Record the resulting decision in `design.md` when it settles a named open question. A failed worker leaves the spike `dispatched`; it is not resolved by inference. Interview and mockup spikes run as fresh attended sessions.

## Worker dispatch

The coordinator supplies the selected adapter, explicit worker model, and explicit
worker effort. Dispatch only through
`skills/drivers/orchestrate/scripts/codex-worker.py` or
`skills/drivers/orchestrate/scripts/claude-worker.py`. Never use the built-in Agent
tool, Workflow tool, or background-agent machinery.

For each research spike, the coordinator owns
`<session-scratch>/epic-research-<spike-id>.state` and
`<session-scratch>/epic-research-<spike-id>.prompt`. The prompt identifies its
recipient as the already-dispatched research worker, directs that worker to research
directly without dispatching another worker, and states the research question, required
Markdown output, temporary-worktree boundary, and return-and-verification contract.
Write that complete brief to the prompt file, then pass its exact contents as the
selected adapter's positional prompt.

Start the worker through the adapter's `workspace-write` surface with the temporary
per-spike worktree as its cwd and the coordinator checkout as its control checkout.
Use the adapter's start, resume, stop, and verify surface. Preserve adapter-owned
state, same-worker resume, and coordinator-owned recovery; do not restate adapter argv
or lifecycle mechanics here.

Reject a nonzero adapter invocation. For a successful invocation, read its
`final_message` as the Markdown findings returned to the home session. The home
session writes the Markdown file required by its public interface, then follows the
existing `## Findings` posting and verification rule. Do not close the spike as
successful without that verified result. Remove the prompt file after the home session
verifies the `## Findings` comment, or after it reports a failed worker. Never commit
the prompt file or state file.

## Deferred child close-out

Before archive, sweep each deferred child from live GitHub state. A human must choose exactly one disposition:

- Promote it outside the closing epic as a spike or build, and remove `deferred`.
- Reparent it to a future epic while retaining `deferred`; it is no longer this epic's child.
- Post the won't-do reason, close it with state reason `NOT_PLANNED`, keep its type label, and remove `deferred`.

Refuse to archive while an open child carries `deferred`.

## Completion and close-out

Read the three completion predicates directly from GitHub: no open spike child; every build child has a merged closing pull request or is closed `NOT_PLANNED`; and no open deferred child remains. Do not infer any predicate from a local summary.

Only after all predicates pass and the child work is human-merged, follow the repository's archive guidance for the active change. Then close the epic issue. Report the issue URL, the three direct checks, and the archive result.
