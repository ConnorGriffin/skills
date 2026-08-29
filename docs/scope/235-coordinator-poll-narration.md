# Scope ledger: coordinator poll narration

## Decisions

- Treat elapsed time and re-polled unchanged state as no news, including after
  three unchanged wait batches; speak on outcomes, operator-relevant
  external-state or decision/action milestones, and coordinator-authored state
  changes. A time interval alone is not a milestone. The issue already settles
  this behavior, so `/scope` returned with nothing to interview. `inline`
- Put the general rule in `profile/base.md` and the dispatch-specific form in
  ticket coordinator mode. This reaches all wait loops while keeping the
  standalone coordinator reference executable. `→ ADR`
- Keep the assurance level at prose plus normalized contract pins. Runtime polling
  machinery is outside the requested behavior and the admitted risk. `inline`
- Leave orchestrate's existing result-collection contract and the Codebase Memory
  Claude hooks unchanged. They govern durable result locators and code discovery,
  not user-facing poll narration. `inline`

### Risk contract

- **Must prevent:** routine unchanged polls flooding the operator while also
  suppressing a worker failure, completion, abandoned wait, operator-relevant
  external-state or decision milestone, or state change the coordinator caused.
- **Must recover:** none; this is an instruction contract with no runtime state to
  repair.
- **Accepted failure:** an agent may still misread the prose and narrate an
  unchanged poll; the consequence is noisy output and a corrected wait loop.
- **Unsupported:** runtime enforcement, timer or milestone machinery, telemetry
  changes, and inference about worker health from elapsed time.
- **Evidence owed:** normalized prose pins for the global and ticket-specific
  rules, plus the repository's documented verification gate.
- **Why:** the observed harm is output noise, and the repository explicitly matches
  mechanisms to the requested assurance level.
- **Disposition:** admitted at intent level.

## Open questions

None.

## Spawned tasks

None.

## Triage review rounds

- Round 1 cold pass (unvalidated Terra): one `authoring` blocker. The draft
  omitted the closed expected-diff allowlist required by
  `skills/drivers/ticket/references/drafting-conventions.md`. Reproduced against
  the cited source; corrected mechanically in the draft. The same reviewer
  confirmed the blocker resolved with no injected defect.
- Round 2 fresh cold pass (unvalidated Terra): no blockers; Appendix A1 was
  reproduced byte-for-byte and the order was countersigned.
- Round 2 load-bearing review lenses: two `authoring` blockers, both reproduced.
  The draft did not state precedence over the existing three-batch fallback, and
  a freely declared elapsed-time threshold could masquerade as a milestone. The
  draft and active change now preserve the fallback outside wait loops, make
  unchanged waits silent after three batches, limit milestones to
  operator-relevant external-state or decision/action points, and exclude time
  intervals alone. One review lens otherwise approved the order; both objecting
  lenses approved the corrections and reported no injected defect.
- Round 3 final fresh cold pass: one `authoring` blocker. The authoritative
  OpenSpec delta named unchanged worker state but omitted the order's unchanged
  result locators, files, and result sets. Reproduced directly; corrected
  mechanically in the requirement and scenario and returned to the same reviewer
  for re-check. The reviewer confirmed the acceptance contract now matches, strict
  validation passes, and no defect was injected. The order is countersigned.
- Final handoff audit: one `authoring` self-containment defect. The executable
  fence cited the private preflight appendix, which will not be posted. The
  citations were removed and the active OpenSpec folder and scope ledger were
  named directly. The final reviewer confirmed the fence stands alone, both
  artifacts exist, strict validation passes, and no defect was injected.
