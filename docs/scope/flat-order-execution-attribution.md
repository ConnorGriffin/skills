# Flat-order execution attribution

## Decisions

- Route through interview mode because the ticket presents two materially different claim-interface designs. Why: either design can satisfy the immediate verdict fix, but they create different durable telemetry contracts. Disposition: `inline`.
- Add the lifecycle verb to each new claim and select `start` claims as flat-order execution evidence. Why: this preserves role as the session's responsibility, identifies execution explicitly, and avoids adding a generic telemetry model. Disposition: `→ ADR` (discharged by `openspec/changes/234-flat-order-execution-attribution/design.md`, ADR 234).
- Keep the schema additive and closed: `verb` accepts only `triage`, `start`, `revise`, or `finalize`; old claims with no verb remain readable and are never guessed into a phase. Why: the ticket needs one discriminator, not an extensible event system or migration layer. Disposition: `inline`.

### Risk contract

- **Must prevent:** lifecycle overhead producing a false slicing verdict; secret exposure; irreversible loss of authoritative data; silent incorrect success.
- **Must recover:** none; telemetry is non-authoritative measurement and must not block ticket work.
- **Accepted failure:** when no measurable `start` claim exists, return `unmeasurable`, record no verdict, and leave manual inspection available through `scan`.
- **Unsupported:** one transcript spanning more than one lifecycle verb (the existing `start` fresh-session contract is the attribution invariant); reconstructing verbs for historical claims; inferring verbs from transcript content or claim order; retuning slicing thresholds or anchor rows; and redesigning the proposed per-repo memory store in #197.
- **Evidence owed:** command-line tests prove claim serialization, closed verb validation, legacy readback without guessing, flat verdict isolation, lifecycle-overhead reporting, and unchanged chunked worker verdicts.
- **Why:** telemetry is advisory, but a false verdict automatically triggers a bad rubric-amendment proposal.
- **Disposition:** inline.

## Open questions

- None.

## Spawned tasks

- None.
