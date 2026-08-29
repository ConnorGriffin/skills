# Record tickets with no slicing traits

## Why

`ticket.py record` requires at least one `--trait` even though ticket triage can
legitimately fire no slicing traits and finalization documents traits only when
they fired. The mismatch makes the documented zero-trait command fail before it
can produce a record, and the current workaround writes a fabricated `none`
trait into reviewer memory.

## What changes

- Make `--trait` optional and emit an empty `traits` array when it is omitted.
- Keep one or more explicit `--trait` flags repeatable, ordered, and unchanged in
  the emitted JSON.
- Clarify finalization's command example so zero-trait orders omit the flag
  instead of inventing a sentinel.
- Cover the zero-trait and multiple-trait command shapes through the public CLI.
- Leave verdict calculation, claim/session attribution, reviewer-memory
  persistence, and existing local records unchanged.

## Risk contract

- **Must prevent:** silently fabricating a slicing trait; changing record verdicts,
  claim/session attribution, reviewer-memory persistence, or existing records;
  secret exposure, irreversible authoritative-data loss, or silent incorrect
  success.
- **Must recover:** none. Record construction is a local, synchronous command.
- **Accepted failure:** malformed explicit flags and missing required non-trait
  arguments continue to stop through argparse with no record emitted.
- **Unsupported:** rewriting historical `"traits": ["none"]` records, validating
  trait names against the rubric, or changing slicing verdict semantics.
- **Evidence owed:** public-command tests prove omitted traits emit `[]` and
  repeated traits preserve their order and values; strict OpenSpec validation and
  the repository gate pass.
