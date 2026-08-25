---
name: epic
description: "Maintain an epic ledger and work clear child tickets through a GitHub-backed planning lifecycle. Use when an effort needs multiple attended sessions, recorded decisions, spikes, or independently shippable builds."
---

# Epic

`$epic` maintains one OpenSpec-backed epic from its first uncertainty through human-verified close-out. It plans and coordinates; clear implementation belongs in ordinary child tickets and runs through `$ticket`.

## Authority and boundaries

An epic lives at `openspec/changes/<epic-slug>/`. Its `proposal.md` and `design.md` are authoritative for destination, scope, risk, and durable decisions. Tracker children substitute for `tasks.md`; `ledger.md` rides the standing planning pull request. The epic ledger is a derived index, not another source of truth. Live GitHub is truth whenever it disagrees with the ledger.

Use GitHub Issues only. Read [the tracker reference](references/github-tracker.md) before the first tracker action. A tracker, authentication, or Git failure stops the current operation visibly; do not guess or repair authoritative state from the ledger.

The home session owns the epic. It stays at planning altitude, files and reads issues, and is the only epic-ledger writer. Build and triage sessions report in their ticket comments and pull requests; the home session syncs the ledger after they return. Coordinators do not nest.

## The epic ledger

Keep `ledger.md` on one standing draft planning pull request, in a dedicated planning worktree. Every planning commit is signed-off, pushed as work proceeds, and the branch merges from main only when necessary. The close-out commit moves the OpenSpec change to the archive in that same pull request. After human merge verification, tear down the planning worktree.

This template and grammar are normative:

```markdown
# Ledger — <epic title>

## Status
next: <the single next action, one line>
updated: <YYYY-MM-DD>

## Notes
- <pointer only: a skill to invoke, or the location of an existing rule>

## Fog
- <something not yet precise enough to ticket>

## Decisions
- #<n> <title> — <one-line gist of the resolved spike's ruling>

## Spikes
- #<n> <title> — open | dispatched | resolved — <one-line gist>

## Builds
- #<n> <title> — filed | triaged | in-progress | pr:#<n> | merged

## Deferred
- #<n> <title> — <one-line reason it can wait>

## Rounds
- <YYYY-MM-DD> #<n> — <sessions used, outcome, one line>
```

Titles never contain ` — `. `Spikes` and `Builds` split at the first delimiter whose next field is a listed state token; free text follows a second delimiter. `Decisions` and `Deferred` have only free text after their first delimiter. `Rounds` lead with date, issue reference, and free text. `Notes` and `Fog` are plain lines.

`Notes` contains pointers and never rules; new standing instructions belong in the repository's ADR home. `Decisions` is derived from resolved spikes, one line for each ruling that still stands. GitHub state, including the `deferred` label, wins over every ledger line.

## Start and maintain an epic

1. Confirm the target repository already has OpenSpec. Otherwise run `$openspec-adopt` as a separate documentation-only pull request.
2. Land the proposal and design on main before opening child work. Create the epic issue with the `epic` label, its native child issues, and the standing draft planning pull request carrying the ledger.
3. Re-read relevant live GitHub state before each mutation. Sync derived ledger lines and `Status`, commit with DCO sign-off, and push. If that ledger push fails, report visible ledger staleness and recover its derived state from live GitHub before continuing.
4. Keep Fog as the operator's prompt. Remove a Fog line only through a `Decisions` line or a spike; never silently delete it.

## Admit work deliberately

File a spike when a question is precise but not yet resolved. A spike can be research, interview, mockup, or a human prerequisite. File a build only as a bounded refusal: refuse to file a build while an open spike or standing Fog line can invalidate its outcome, constraints, or acceptance criteria.

Before filing a build, require every relevant load-bearing ruling in the repository's ADR home. User-facing work also requires a locked `/ui-craft` spec. The build issue must stand alone and receive the normal `$ticket` triage flow; the epic does not manufacture a work order.

Use native `blocked-by` edges for actual dependencies. A follow-up required to reach the epic destination is an in-scope native child. A follow-up outside that destination is also filed as a native child, receives its `spike` or `build` type plus `deferred`, and is reported on the originating ticket. Ordinary builds still receive `build` from ticket triage.

## Resolve spikes

For a research spike, run `$research` in a temporary per-spike worktree. The worker writes the Markdown file required by its public interface and returns it to the home session. The home session posts that returned content under the exact heading `## Findings`, verifies the `## Findings` comment, removes the temporary worktree and its unshipped file, and only then closes the spike.

Close the spike issue only after that verification. Only then derive its `Spikes` and `Decisions` ledger lines, update `Status`, commit with DCO sign-off, and push the standing planning branch. A failed worker leaves the spike `dispatched`; it is not resolved by inference. Interview and mockup spikes run as fresh attended sessions.

## Deferred child close-out

Before archive, sweep each deferred child from live GitHub state. A human must choose exactly one disposition:

- Promote it outside the closing epic as a spike or build, and remove `deferred`.
- Reparent it to a future epic while retaining `deferred`; it is no longer this epic's child.
- Post the won't-do reason, close it with state reason `NOT_PLANNED`, keep its type label, and remove `deferred`.

Refuse to archive while an open child carries `deferred`.

## Completion and close-out

Read the three completion predicates directly from GitHub: no open spike child; every build child has a merged closing pull request or is closed `NOT_PLANNED`; and no open deferred child remains. Do not infer any predicate from a ledger line.

Only after all predicates pass, make the final ledger-and-archive commit and push it. Take the planning pull request out of draft, wait for the planning pull request to be human-merged, and verify that merge. Then close the epic issue and tear down the planning worktree. Report the issue and planning pull request URLs, the three direct checks, and any visible ledger staleness.
