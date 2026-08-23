# Scope: /ticket hardening profile (issue 103)

Opt-in `/ticket` profile that replaces agent review rounds with a deterministic
hardening command plus a human QA script.

## Decisions

- Q2 Profile selection: a `Profile: hardening` line in the work order fence,
  stamped by triage. Why: start already parses fence lines; the default workflow
  stays untouched. inline
- Q3 No `Harden:` line in the target repo: triage refuses to stamp the profile and
  posts a default-workflow order, saying so. Why: triage-time fact, cheaper than a
  draft PR. inline
- Q4 Hardening loop stop: `Harden:` exits 0 and every survivor is killed or listed
  as equivalent in the PR body; cap of 3 passes, then the PR opens as draft with
  the residue named. Why: mirrors the two-review-round cap. inline
- Q5 QA script: profile orders only. Why: it replaces the review round; the
  default template and its tests stay unchanged. inline
- Q1 Sequencing: `/clean` landed as #104; no dependency remains. inline
- Q6 Siblings 89, 92, 94, 95 are closed; nothing to dispose. inline

### Risk contract

- Must prevent: silent incorrect success (a `Harden:` that cannot run reported as
  pass); secret exposure; irreversible loss of authoritative data.
- Must recover: none.
- Accepted failure: hardening cap reached → draft PR naming residue, manual follow-up.
- Unsupported: repos without a `Harden:` line (they get the default workflow).
- Evidence owed: tests pinning that triage, start, revise, and the template carry
  the profile contract (`Profile: hardening`, `Harden:`, `QA script:`, cap of 3,
  error-not-pass).
- Why: documentation-only change in a markdown pack; the failure surface is a
  misread rule, not runtime damage. Disposition: inline.

## Open questions

_(none)_

## Grounding (verified this session)

- No profile mechanism exists in `skills/drivers/ticket/` today; `Review depth:`
  and `Surface lifecycle:` are the only per-order switches.
- `/clean` does not exist in the pack; issue 102 is open and unbuilt.
- This repo declares no `Harden:` line; it is a markdown pack with a Python
  validator and unittest suite.
- `profile:` and `ui-surfaces:` in `AGENTS.md` are declared but consumed by no
  code in this repo, so a repo-facts declaration line has precedent.
- ADR 97 keeps the current `/ticket` workflow authoritative and defers adapters
  until a compatibility spike; issue 103 stays inside that boundary by using a
  raw command line instead of adapters.
- Issues 87, 88, 91, 93, 96 are already closed; 89, 92, 94, 95 are open and
  overlap issue 103's substance.

## Spawned tasks

_(none yet)_
