# Measure archived Codex rollouts

## Why

Ticket telemetry resolves a claimed Codex session only under the active
`sessions` root. Codex can move completed top-level rollouts to
`archived_sessions` before a later finalization measures them, so an exact valid
claim is reported unreadable and a measurable flat order becomes
`unmeasurable`. The archived-only public-command reproduction is recorded in
`docs/scope/290-generated-facts.md`.

## What changes

- Treat active and archived Codex rollout directories as one discovery source
  for an exact claimed session id.
- Preserve every distinct matching rollout across both roots so resumed sessions
  still report the maximum context peak.
- Cover active-only, archived-only, mixed-root, and genuinely missing rollouts
  through the public `scan` and `record` commands.
- Leave claim attribution, rollout parsing, verdict thresholds, Claude
  transcript discovery, and historical slicing records unchanged.

## Risk contract

- **Must prevent:** secret exposure, irreversible loss of authoritative data,
  and silent incorrect success; specifically, a claimed Codex session must not
  be reported unreadable when an exact matching rollout exists in either
  supported root.
- **Must recover:** none; transcript discovery is read-only.
- **Accepted failure:** when no exact matching rollout exists in either root,
  preserve the visible `unmeasurable` result and manual inspection path.
- **Unsupported:** reconstructing historical slicing records, changing rollout
  parsing, or inferring session identity from transcript contents.
- **Evidence owed:** public `scan` and `record` behavior for active-only,
  archived-only, active-plus-archived, and missing-rollout sessions; the mixed
  case must use every distinct rollout and report the maximum peak.

## Impact

The existing ticket command interface and `transcripts_for()` seam remain in
place. The implementation changes only Codex transcript discovery, its
public-command regression tests, and this ticket-workflow specification delta.
No rendered surface, new module, dependency, migration, or historical repair is
included.
