---
name: ci-design
description: Vocabulary and principles for well-designed CI. Use when the user wants to design, review, or audit CI, says CI is noisy, slow, or expensive, or is designing a workflow yml.
---

# CI Design

Design CI so cost tracks the surface area actually touched, not the number of
pushes. Use this language wherever CI is being designed, reviewed, or audited.

## Priorities

Fix in this order — each tier assumes the ones above it are already sound:

1. **Minutes and billing waste.** Runner tier, caching, unconditional jobs.
   Money leaks here even when every run is green.
2. **PR feedback latency.** How long a contributor waits to learn a push is
   good or bad. Concurrency and trigger surface live here.
3. **Run and notification volume.** Duplicate or invisible checks, noisy
   scheduling. Annoying, but cheaper than the first two.

Baseline failure noise (a flaky test, a known-red job) matters less than any
of these — it's visible and locally fixable. Structural waste isn't; it
compounds silently across every run.

## Vocabulary

Use these terms exactly.

**Trigger surface** — the product of events, branches, and paths that fire a
workflow (`on: push/pull_request` × branch filters × path filters). The
trigger surface is the first lever: a workflow that fires on every push to
every branch has a trigger surface many times larger than the work it
actually needs to validate.

**Path filtering** — restricting a job to run only when files it cares about
changed. The required-checks-safe pattern: never put `paths:` at the
workflow level on a job that's a required status check — GitHub can leave a
required check permanently pending if its workflow never triggers. Instead,
filter *inside* the job with a paths-filter step that gates the real work,
so the workflow still runs and reports green (or explicitly skipped) on
every PR.

**Concurrency group** — a `concurrency:` key that cancels superseded runs on
the same branch/PR (`cancel-in-progress: true`), so a burst of pushes
collapses to one live run instead of a growing queue. Release and deploy
paths are the deliberate exception: don't cancel a run that's mid-deploy
just because a new commit landed.

**Caching** — persisting dependencies or toolchains across runs, keyed on
something that changes only when the cache should invalidate (a lockfile
hash, a pinned tool version). The sin isn't the absence of a cache line —
it's reinstalling a toolchain, browser binary, or dependency tree from
scratch on every single run when the inputs didn't change.

**Runner cost tiers** — macOS runners cost several times what Linux runners
cost per minute; Windows sits in between. A job earns a pricier runner only
by a real platform dependency (building a macOS binary, testing an
Xcode-only path) — never by inertia or a single assumption (like a temp
path) that's trivially fixable on Linux.

**Scheduled scans** — expensive or slow analysis (security scanning, full
matrix builds) that doesn't need to gate every PR. When merge velocity is
high, put it on a schedule plus main-branch pushes instead of every pull
request — it still runs regularly, just not once per push.

**Iteration burst** — a string of pushes to the same branch in quick
succession, each firing its own run. Expected during active development,
not itself a problem. The concurrency group is what determines whether a
burst turns into cancellations (cheap, correct) or a queue of runs that
finish stale and red (expensive, misleading).

**Invisible checks** — status checks that show up on a PR with no
corresponding yml in the repo, most commonly GitHub's CodeQL default setup
configured through repo settings rather than a workflow file. They can't be
inventoried, diffed, or reviewed by reading the repo. Export them to a
checked-in workflow so every check the repo runs is visible from its files.

## Principles

- **Every job answers "which changed files require me?"** If a job can't
  name the files that would make it necessary, its trigger surface is too
  wide.
- **Every workflow has exactly one visible definition on disk.** No check
  should exist that isn't traceable to a yml file in the repo.
- **Cost scales with touched surface area, not PR volume.** Ten pushes that
  touch nothing relevant should cost less than one push that touches
  everything.
- **CI is a signal.** A check that's red mid-iteration by design — because
  nothing cancelled it, because it always runs even on draft churn — trains
  people to ignore red, which erodes the signal for the run that matters.

## Going deeper

- **Running an audit** — see
  [references/AUDIT-PLAYBOOK.md](references/AUDIT-PLAYBOOK.md): the
  repeatable procedure for inventorying, measuring, and ranking CI findings
  across one or more repos.
