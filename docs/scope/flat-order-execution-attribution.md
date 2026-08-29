# Flat-order execution attribution

## Decisions

- Route through interview mode because the ticket presents two materially different claim-interface designs. Why: either design can satisfy the immediate verdict fix, but they create different durable telemetry contracts. Disposition: `inline`.
- Add the lifecycle verb to each new claim and select `start` claims as flat-order execution evidence. Why: this preserves role as the session's responsibility, identifies execution explicitly, and avoids adding a generic telemetry model. Disposition: `→ ADR` (discharged by `openspec/changes/234-flat-order-execution-attribution/design.md`, ADR 234).
- Keep the schema additive and closed: `verb` accepts only `triage`, `start`, `revise`, or `finalize`; old claims with no verb remain readable and are never guessed into a phase. Why: the ticket needs one discriminator, not an extensible event system or migration layer. Disposition: `inline`.
- Keep one lifecycle verb per session; same-verb resumes remain valid, but a later verb starts in a fresh session. Why: the transcript is the measurement unit, so reusing a start transcript for revise or finalize would contaminate its execution peak even with explicit claim metadata. Disposition: `inline`.
- Preserve claim idempotence for the same ticket, session, and verb; on a cross-verb re-claim, keep and print the persisted claim, report one visible non-blocking conflict, and require a fresh session. Why: the command must not claim success for metadata it did not store, but telemetry still cannot gate the ticket workflow. Disposition: `inline`.

### Risk contract

- **Must prevent:** lifecycle overhead producing a false slicing verdict; secret exposure; irreversible loss of authoritative data; silent incorrect success.
- **Must recover:** none; telemetry is non-authoritative measurement and must not block ticket work.
- **Accepted failure:** when attributable in-repository claims exist but no measurable eligible `start` claim exists, return `unmeasurable`, record no verdict, and leave manual inspection available through `scan`; when no attributable claim exists, preserve `no-data`.
- **Unsupported:** one transcript spanning more than one lifecycle verb (the existing `start` fresh-session contract is the attribution invariant); reconstructing verbs for historical claims; inferring verbs from transcript content or claim order; retuning slicing thresholds or anchor rows; and redesigning the proposed per-repo memory store in #197.
- **Evidence owed:** command-line tests prove claim serialization, closed verb validation, legacy readback without guessing, flat verdict isolation, lifecycle-overhead reporting, and unchanged chunked worker verdicts.
- **Why:** telemetry is advisory, but a false verdict automatically triggers a bad rubric-amendment proposal.
- **Disposition:** inline.

## Open questions

- None.

## Spawned tasks

- None.

## Review rounds

- Round 1, Sol cold pass (unvalidated load-bearing route): three `authoring` blockers. Preserve the existing zero-claim `no-data` branch; define `verb_peaks` as five scalar integer maxima with `0` for absence; replace the incomplete behavior-term inventory with a claim-producer and telemetry-contract inventory. All three claims reproduced against `ticket.py`, `tests/test_ticket.py`, and the generated inventory; the draft and authoritative OpenSpec wording were corrected.
- Round 1 same-reviewer re-check: two blockers resolved; the zero-claim blocker remained `authoring` because two original OpenSpec summary sentences had not been narrowed with the rest of the correction. Both sentences now distinguish attributable claims from zero claims.
- Round 1 second same-reviewer re-check: the remaining blocker resolved; Sol returned SHIP and strict OpenSpec validation remained clean.
- Round 2, fresh Sol cold pass (unvalidated load-bearing route): one `authoring` blocker. `revise.md` permits any session, while claim de-duplication and resumed-transcript measurement would let revise work inflate the original start peak. The workflow and order now require a fresh session when crossing lifecycle verbs; same-verb resumes remain supported.
- Round 2 same-reviewer re-check: the lifecycle-session blocker resolved; the inventory and strict OpenSpec validation matched, and Sol returned SHIP.
- Round 3, final fresh Sol cold pass (unvalidated load-bearing route): one `authoring` blocker at the cap. Existing de-duplication silently prints submitted metadata when it retained different persisted metadata, so a cross-verb claim could appear successful while remaining attributed to start. `/scope` found no unsettled human choice: preserve same-verb idempotence, visibly report only a cross-verb conflict using the persisted verb, and keep the failure non-blocking.
- Round 3 same-reviewer re-check: the scoped cross-verb conflict behavior resolved the blocker without transcript segmentation, migration, a new seam, or broader enforcement machinery. Sol returned SHIP; the work order is countersigned at the three-panel cap.
