# Remove the unread ticket telemetry store

## Why

`ticket.py record` appends every measurable slicing verdict to
`~/.config/ticket/telemetry.jsonl`, but the pack has no reader for that file.
Finalization already sends the same record to the per-repository reviewer-memory
store, which is the durable source that triage and review actually consume.
Keeping the parallel write adds a sandbox failure path and couples public-command
tests to private persistence without serving a reader.

## What changes

- Stop `record` from creating or appending `telemetry.jsonl`; keep its JSON stdout
  contract and all verdict calculations unchanged.
- Move record assertions to the command's stdout and remove tests that exist only
  for the unused write and its write-denial path.
- Describe finalization as returning the record for reviewer-memory to persist, and
  carry a ticket-workflow spec delta that renames the live behavior to role-aware
  measurement when post-merge finalization archives the change.
- Leave `claims.jsonl`, reviewer-memory persistence, existing telemetry files, and
  frozen ADR and archived-change history unchanged. Do not add a cross-repository
  aggregation helper without a current caller.

## Risk contract

- **Must prevent:** changing `record`'s JSON stdout or verdict semantics; changing
  claim attribution; deleting or migrating an operator's existing telemetry file;
  dropping finalization's reviewer-memory append; secret exposure, irreversible
  authoritative-data loss, or silent incorrect success.
- **Must recover:** none. The removed store is advisory output with no reader.
- **Accepted failure:** existing `telemetry.jsonl` files remain as inert local
  history; an operator who wants them removed does so manually.
- **Unsupported:** reading or migrating old telemetry records, adding a new
  cross-repository query, or automatically tuning the slicing rubric.
- **Evidence owed:** public-interface tests parse `record` stdout for each existing
  verdict and field assertion; behavior tests keep finalization's reviewer-memory
  append pinned; OpenSpec validation and the repository gate pass.
