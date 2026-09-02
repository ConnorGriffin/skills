# Scope ledger — ticket 290: measure archived Codex rollouts

## Decisions

- Codex transcript discovery treats active and archived rollout roots as one
  exact-session-id source, while preserving distinct resumed rollouts and the
  maximum context peak across them.
  Why: the public-command reproduction proves archived top-level sessions are
  currently misclassified as unreadable, while ADR 70 requires exact-id
  attribution rather than content inference.
  Disposition: inline

- The shipping change is a flat, non-UI code order through the existing ticket
  command interface; it adds no new module or external dependency.
  Why: `transcripts_for()` is already the single transcript-discovery interface
  used by both `scan` and `record`, and the repository is standard-library only.
  Disposition: inline

- Do not reconstruct or append a corrective slicing record for
  `harmonichq/harmonic#194`; issue 290 fixes future measurement only.
  Why: the operator explicitly does not value recovering the lost historical
  calibration, and cross-repository history is unrelated to correcting rollout
  discovery.
  Disposition: inline

### Risk contract

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

Why: the command reads local telemetry and its harmful failure mode is a silent
false measurement, not loss of source data.
Disposition: inline

## Open questions

- None.

## Spawned tasks

- None.
