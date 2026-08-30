# Scope ledger — remove worker-egress consent machinery (ticket 275)

Route: interview mode. Dominant uncertainty is how far removal goes, not a missing fact.

## Decisions

- Grounding: the grant is machine-driven, not loose prose. `scripts/consent_grant.py`
  is canonical; `scripts/sync_consent_grant.py` generates three surfaces and clause
  checks ten more. Surfaces: both SKILL.md frontmatter descriptions and `## Invocation`
  sections, both `agents/openai.yaml` default prompts, three `## Approval rationale`
  sections in the orchestrate dispatch references, and the ticket verbs
  triage/start/revise plus `references/coordinator-mode.md`. inline
- Grounding: pinned by `docs/adr/adr-194-literal-invocation-egress-consent.md`, required
  by `openspec/specs/ticket-workflow/spec.md` (Requirement: Bounded worker-egress
  consent) and `openspec/specs/planning-and-review/spec.md`, gated by
  `tests/test_behavior.py::WorkerEgressConsentContractTests`. CI runs `validate.py` plus
  the unittest suite, so those tests are the gate. inline
- Grounding: the coordinator-owned-review contract (delegation handoff, durable result
  locator, worker must not launch a nested reviewer) is textually fused into the same
  spec requirement blocks and must survive removal. inline
- Grounding: consent framing is confined to the ticket and orchestrate skills. inline

- Q1: full removal. Every consent statement goes, in both skills and in the three
  adapter escalation notes, including the exclusions sentence. Why: the working theory
  is that permission-seeking framing itself causes the balking, so any retained fragment
  re-runs the same experiment. inline
- Q2: acceptance needs a live Codex worker dispatch that does not stop to re-ask, not
  only a green suite. Why: the prior reworded versions all passed their text checks and
  still balked. inline
- Q3 and Q5: no regression guard. The decision record alone keeps future agents honest,
  and a vocabulary ban is overkill for a judgment call the operator will make himself.
  Why: superseded at Q5 after the guard was priced. inline
- Q4: merge without a live Codex run gating the pull request, and leave ticket 275 open
  as a recurrence tracker rather than closing it at finalize. Why: the operator reports
  a recurrence directly, and gating the merge on an attended dispatch buys little. inline
- Q6: losing the exclusions sentence is accepted and does not change the secret-exposure
  default. Why: the worker already runs in the checkout, so the sentence withheld
  nothing; it was prose, not enforcement. inline

### Risk contract

- Must prevent: a surface silently keeping consent framing while the suite passes;
  removal that also deletes the coordinator-owned review handoff contract; secret
  exposure; irreversible loss of authoritative data.
- Must recover: none.
- Accepted failure: workers still balk after removal. Ticket 275 stays open as a
  tracker and the operator reports the recurrence; no automatic detection.
- Unsupported: runtime enforcement of what bytes reach a worker; a vocabulary guard
  banning the framing from returning; any measurement of worker balking in CI.
- Evidence owed: the suite passes with the consent contract tests removed; a closed
  grep inventory over the pack shows no surviving consent framing in the ticket and
  orchestrate skills; the coordinator-owned review handoff keeps its spec requirement
  and its existing tests.
- Why: this is a prose contract with thirteen copies being deleted, and the harm is an
  incomplete deletion or collateral loss of the review contract fused into it.
  Disposition: copied into the work order on ticket 275.

- Slicing: two serial chunks. Traits `multiple deliverable artifacts` and `lockstep
  copies of one fact` both fire, matching anchor row 259 (skills), whose Right shape
  column is two serial chunks and whose flat actual peaked 187k, over the band.
  Reviewer memory planning rule 6 agrees: broad retirement work has exceeded the band
  four times while stamped flat. The over-slicing warning (#143) is noted and both
  chunks are projected above the 120k floor. inline
- Review depth: Full on both chunks. Workflow machinery every repo inherits, and this
  alters contract semantics rather than relocating them. inline
- Probe: `docs/scope/275-probes/no_consent_framing.sh` is the closed-inventory check.
  It fails first at 34 lines across 15 files on the pre-change tree. inline
- ADR home: the reversal is recorded as `## ADR 275` in the new OpenSpec change's
  `design.md`. `docs/adr/adr-194-literal-invocation-egress-consent.md` is frozen legacy
  and stays byte-identical. inline

## Open questions

(none)

## Spawned tasks

(none)
