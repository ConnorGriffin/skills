# Simplify the skill pack

## Why

The pack carries roughly 14k lines of skill prose and 2.5k lines of worker scripts.
Much of it is now covered natively by Claude Code: subagents with a per-agent model,
effort, tools allowlist, and worktree isolation; `SendMessage` resume; Workflows for
fan-out; and `/code-review ultra`. Several layers are no longer paying for
themselves. Agents rarely used the codebase-memory graph tools while its index cost
about 29 GB on disk, the pack-owned worker adapters duplicate native dispatch, and
persona panels added review rounds without a matching gain.

## What changes

- Remove the `codebase-memory` and `cbm-onboard` skills, their hooks, tests,
  `.cbmignore`, CI lines, and the profile's code-discovery paragraph.
- Remove the `orchestrate` driver, its worker adapters, routing references, and
  tests. Skills that dispatched through the adapters (`code-review`, `plan-review`,
  `research`, `codebase-design`'s design-it-twice) now dispatch read-only native
  subagents with the model named on the dispatch. A short "Delegating to
  subagents" section in `profile/base.md` replaces the coordinator rules.
- Remove `persona-review`, the review front door's `personas` route, plan-review's
  persona panel step, and UI Craft's `consensus` panel mode and its `init` persona
  panel step.
- Delete the `scope` and `preflight` skills. Other skills point to
  `/ticket triage` instead; a follow-up under this issue folds their behavior into
  triage and rewrites the ticket skill.

## Risk contract

- **Must prevent:** a surviving skill instructing an agent to run a deleted script
  or skill outside the ticket skill, whose rewrite is the follow-up; a broken
  repository link; a weakened assertion about a surviving skill's behavior.
- **Must recover:** none; every removal is a reversible git change.
- **Accepted failure:** the ticket skill still names `/scope`, `/orchestrate`,
  and the Codebase Memory graph identity until the ticket rewrite lands.
- **Unsupported:** rewriting archived OpenSpec changes, frozen ADRs, or historical
  scope notes beyond the links the validator requires.
- **Evidence owed:** strict OpenSpec validation, the structural validator, and the
  behavior suites green on the removal commits.

## Impact

Removes six skills and their tests. Changes `code-review`, `plan-review`,
`research`, `codebase-design`, `review`, `ui-craft`, the README, the docs site
sources and mockups, CI workflows, and `profile/base.md`. Supersedes ADR 65,
ADR 149, and ADR 150.
