---
name: epic
description: "Coordinate an OpenSpec epic and clear child tickets through a GitHub-backed planning lifecycle. Use when an effort needs multiple attended sessions, recorded decisions, spikes, or independently shippable builds."
---

# Epic

`$epic` maintains one OpenSpec-backed epic from its first uncertainty through human-verified close-out. It plans and coordinates; clear implementation belongs in ordinary child tickets and runs through `$ticket`.

## Authority and boundaries

An epic lives at `openspec/changes/<epic-slug>/`. Its `proposal.md`, `design.md`, and `tasks.md` form the OpenSpec authority: proposal owns destination and scope; design owns risk, durable decisions, and named open questions; tasks owns the checked implementation sequence and links to every child issue. Live tracker state is truth for child type, status, dependencies, deferral, and closing pull requests. Do not create a derived index of that state.

Route every tracker operation through the installed binding. [bindings/github-issues.md](bindings/github-issues.md) is the shipped default. Read [the tracker contract](references/tracker-contract.md) before the first tracker action. A tracker, authentication, or Git failure stops the current operation visibly; do not guess or repair authoritative state locally.

The home session owns the epic. It stays at planning altitude, files and reads issues,
and keeps the active change coherent. It performs no child execution. Research,
prototype, interview, triage, and build work resumes only in fresh attended sessions
that the operator invokes. Those sessions report through tracker comments and pull
requests; the epic records their tracker result and any resulting decision.

## Start and maintain an epic

1. Confirm the target repository already has OpenSpec. Otherwise run `$openspec-adopt` as a separate documentation-only pull request.
2. Create one active change with its proposal, design, and tasks. Create the epic issue
   with the `epic` label. Maintain the change on one pushed epic planning branch and
   identify each handoff by that branch's full commit, but never open a pull request
   from that branch. Add each filed
   child issue link to `tasks.md` in implementation sequence; do not duplicate live
   tracker fields there.
3. Re-read relevant live tracker state before each mutation. Update the change when destination, design, or checked sequence changes; preserve child type, status, dependencies, deferral, and closing-pull-request facts on the tracker.
4. Keep every imprecise concern as a named open question in `design.md`. Clear an open question only by recording its decision in `design.md` or promoting it to a tracker spike; never silently delete it. Do not add pointer-only Notes: owning skills and repository rules remain discoverable at their authoritative homes.

## Admit work deliberately

File a spike when an open question is precise but not yet resolved. A spike can be
research, interview, mockup, or a human prerequisite. File a build only as a bounded
refusal: refuse to file a build while an open spike or named open question can
invalidate its outcome, constraints, or acceptance criteria.

Before filing a build, require every relevant load-bearing ruling in the repository's ADR home. User-facing work also requires a locked `/ui-craft` spec. The build issue must stand alone and receive the normal `$ticket` triage flow; the epic does not manufacture a work order.

Use native `blocked-by` edges for actual dependencies. A follow-up required to reach
the epic destination is an in-scope native child. A follow-up outside that
destination is also filed as a native child, receives its `spike` or `build` type
plus `deferred`, and is reported on the originating ticket. Ordinary builds still
receive `build` from ticket triage.

Default to three or fewer child tickets. Before filing a fourth or later child,
require a written justification in the active change's `design.md`. The justification
must name the independently shippable capability boundary or real dependency that
prevents consolidation into fewer, larger children. Apply this as semantic planning
judgment through the existing child-filing interface; do not add a parser, counter
script, or tracker operation.

## Hand a child to the operator

Permit only one in-flight epic child. Refuse every later handoff until the prior
child's implementation pull request is human-merged. After that merge, fetch the
updated remote default branch, advance the pushed epic planning branch from that
updated remote default-branch tip, apply any next planning update, commit, and push a
new full-commit pin before preparing another child.

Before each handoff, commit and push the current active change on the epic planning
branch. Record its unprefixed branch name and full commit in the child issue body's
draft order as:

```text
Parent plan base: <branch name without the origin/ prefix>@<full commit>
```

The issue body is a draft, not the executable lock. The epic does not post a fenced
`WORK ORDER` comment, does not invoke `/ticket triage`, `/ticket start`, `/ticket
revise`, or `/ticket finalize`, and does not open a pull request. Stop and tell the
operator to invoke `/ticket triage <id>`. Ticket triage independently grounds,
scopes, reviews, and posts the only fenced executable work order.

## Resolve spikes

Research spikes resume in fresh attended sessions that the operator invokes;
interview and mockup spikes follow the same rule. Close a spike only after its tracker result is present and verified,
then record the tracker result and resulting decision in `design.md` when it settles
a named open question. A failed attended session leaves the spike open; do not infer
a result.

## Pull-request boundary

The coordinator never opens a pull request. A planning-only pull request is
unsupported. The epic's OpenSpec planning artifacts stay active until they travel
with the implementation pull request that realizes them. When ticket triage finds a
required parent-plan amendment, that attended ticket workflow commits the amendment
in the child's worktree and carries it through review and implementation; the epic
does not open a separate prerequisite pull request. The one-time `$openspec-adopt`
documentation-only pull request remains outside this lifecycle because it happens
before an epic exists.

## Deferred child close-out

Before archive, sweep each deferred child from live GitHub state. A human must choose exactly one disposition:

- Promote it outside the closing epic as a spike or build, and remove `deferred`.
- Reparent it to a future epic while retaining `deferred`; it is no longer this epic's child.
- Post the won't-do reason, close it with state reason `NOT_PLANNED`, keep its type label, and remove `deferred`.

Refuse to archive while an open child carries `deferred`.

## Completion and close-out

Read the three completion predicates directly from GitHub: no open spike child; every build child has a merged closing pull request or is closed `NOT_PLANNED`; and no open deferred child remains. Do not infer any predicate from a local summary.

Only after all predicates pass and the child work is human-merged, follow the repository's archive guidance for the active change. Then close the epic issue. Report the issue URL, the three direct checks, and the archive result.
