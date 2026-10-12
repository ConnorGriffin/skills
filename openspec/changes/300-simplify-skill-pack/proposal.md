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
- Delete the `scope` and `preflight` skills and fold their behavior into
  `/ticket triage`.
- Rewrite the ticket skill to under 600 lines of prose: one artifact per verb, one
  cold plan review only at Full depth, one code-review pass, no chunked orders.
- Remove the `epic` skill; triage files oversized work as child issues tracked on a
  parent checklist.
- Remove four skills the harness now covers: `drive-local-webapp` (built-in browser
  and preview tools), `clean` (`/simplify`), `spin-worktree` (native worktree
  isolation), and the `review` front door (`/code-review` or `/plan-review`). Drop
  `ticket.py record`'s chunked-order verdict, which no prose calls.
- Remove the `reviewer-memory` skill and the steps in `code-review`, `plan-review`,
  and the ticket skill that read or wrote its per-repository store.

## Risk contract

- **Must prevent:** a surviving skill instructing an agent to run a deleted script
  or skill; a broken
  repository link; a weakened assertion about a surviving skill's behavior.
- **Must recover:** none; every removal is a reversible git change.
- **Accepted failure:** active change 273's finalization delta still mentions epic
  children, an inert clause left to that change.
- **Unsupported:** rewriting archived OpenSpec changes, frozen ADRs, or historical
  scope notes beyond the links the validator requires.
- **Evidence owed:** strict OpenSpec validation, the structural validator, and the
  behavior suites green on the removal commits.

## Impact

Removes twelve skills and their tests, and rewrites the ticket skill. Changes `code-review`, `plan-review`,
`research`, `codebase-design`, `ui-craft`, the README, the docs site
sources and mockups, CI workflows, and `profile/base.md`. Supersedes ADR 65,
ADR 149, ADR 150, ADR 143, and ADR 52.
