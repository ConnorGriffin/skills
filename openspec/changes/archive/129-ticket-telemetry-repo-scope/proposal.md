# Ticket telemetry repository scope

## Why

Workers correctly claim their target worktree, but a coordinator can finalize
from a different checkout. `scan` and `record` then used the coordinator's
repository and excluded the claims that belonged to the ticket. Separately, a
missing or zero-peak transcript could produce a slicing verdict without the
peak that verdict needs.

## What changes

* `scan` and `record` accept the same optional target worktree as `claim`, so
  finalization can read claims from the repository where the ticket ran.
* Telemetry returns `unmeasurable` rather than a numeric slicing call when this
  repository has claims but no usable peak. Its reason distinguishes unreadable
  Codex rollouts from no claims.
* Finalize guidance keeps a target worktree available for cross-checkout
  measurement and names the new outcome.

## Risk contract

* **Must prevent:** claims from the target repository being excluded merely
  because finalization runs elsewhere; a zero or absent peak becoming a sizing
  judgment.
* **Must preserve:** the current verdict for tickets with usable evidence,
  including `coordinator-only` when only non-worker context was measured.
* **Evidence owed:** public command tests cover target-repository scanning and
  recording, wrong-checkout exclusion, zero-peak inputs, and unreadable Codex
  rollouts; the repository gate remains green.
