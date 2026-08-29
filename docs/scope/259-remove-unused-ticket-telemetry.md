# Scope ledger — ticket 259: remove unused ticket telemetry

## Decisions

- Delete the unread `telemetry.jsonl` write without a replacement aggregate.
  Why: reviewer memory already persists the same slicing record for its real
  readers, and there is no current cross-repository consumer. Disposition:
  `inline`.
- Preserve `record`'s JSON stdout and move persistence-coupled assertions to that
  public interface. Why: stdout already carries the complete record consumed by
  finalization. Disposition: `inline`.
- Leave `claims.jsonl`, reviewer-memory persistence, existing local telemetry
  files, frozen ADRs, and archived OpenSpec changes unchanged. Why: they are either
  load-bearing current state or immutable history, while deleting operator data is
  outside this ticket. Disposition: `inline`.

### Risk contract

- **Must prevent:** changing `record` stdout or verdicts; changing claim storage or
  attribution; deleting existing telemetry files; dropping reviewer-memory
  persistence; secret exposure, irreversible authoritative-data loss, or silent
  incorrect success.
- **Must recover:** none.
- **Accepted failure:** old telemetry files remain inert until manually removed.
- **Unsupported:** telemetry migration, a cross-repository reader, or automatic
  slicing-rubric tuning.
- **Evidence owed:** public-command stdout tests, the finalization behavior pin,
  OpenSpec validation, and the repository gate.
- **Why:** this is a local advisory-measurement cleanup; the only load-bearing
  surfaces are the existing stdout and reviewer-memory contracts.
- **Disposition:** `inline`.

## Open questions

None.

## Spawned tasks

None.

## Review rounds

- Round 1: 0 `authoring` blockers and 0 `injected` blockers. The grounded order
  was countersigned without revision. Non-blocking checks confirmed that the full
  role-aware measurement scenarios stay in the active spec delta and that record
  field/privacy assertions move to stdout without a replacement helper or store.
