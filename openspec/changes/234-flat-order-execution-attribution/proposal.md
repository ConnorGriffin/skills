# Attribute flat-order execution explicitly

## Why

A flat ticket currently judges the largest non-reviewer claim as implementation
cost. Every lifecycle verb claims the coordinator role, so triage, revise, or
finalize context can make a correctly sized flat order look under-sliced and
trigger a bad slicing-rubric amendment.

## What changes

* New claims record the ticket lifecycle verb that produced them.
* Flat verdicts use measurable `start` claims, excluding reviewer claims, as
  execution evidence. Triage, revise, and finalize peaks remain reportable
  overhead and never affect that verdict.
* Claims written before verb attribution remain readable as legacy data and are
  never guessed into a lifecycle phase. A flat order with attributable claims but
  no measurable eligible `start` claim returns `unmeasurable`; zero attributable
  claims remain `no-data`.
* The public ticket workflow, finalization guidance, baseline specification, and
  command-line regression tests move with the helper contract.

## Risk contract

* **Must prevent:** lifecycle overhead producing a false slicing verdict; secret
  exposure; irreversible loss of authoritative data; silent incorrect success.
* **Must recover:** none; telemetry is non-authoritative measurement and must not
  block ticket work.
* **Accepted failure:** when attributable in-repository claims exist but no
  measurable eligible `start` claim exists, return `unmeasurable`, record no
  verdict, and leave manual inspection available through `scan`; when no
  attributable claim exists, preserve `no-data`.
* **Unsupported:** one transcript spanning more than one lifecycle verb (the
  existing `start` fresh-session contract is the attribution invariant);
  reconstructing verbs for historical claims; inferring verbs from transcript
  content or claim order; retuning slicing thresholds or anchor rows; and
  redesigning the proposed per-repo memory store in #197.
* **Evidence owed:** command-line tests prove claim serialization, closed verb
  validation, legacy readback without guessing, flat verdict isolation,
  lifecycle-overhead reporting, and unchanged chunked worker verdicts.
