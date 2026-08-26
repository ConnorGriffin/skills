# Scope — 199 assurance-level matching

Route: interview mode (a concrete resolution exists in the user's head, untested).

## Decisions

- Ticket classification is `code`: prose changes landing as a pull request. inline
- Repo records changes with OpenSpec; the change folder is `openspec/changes/`. inline
- The failure this ticket fixes is mechanism escalation, not a wrong risk decision.
  plan-review axis 4 already forbids silently prescribing *hardening* when evidence
  shifts a risk decision; it says nothing about escalating the *mechanism* (parser,
  provenance record, state machine, content filter, runtime enforcement) above the
  assurance level the work was admitted at. inline

## Open questions

- Q1: home for the global assurance-matching rule — `profile/base.md` vs `profile/CHARTER.md`.
- Q2: whether the assurance ceiling becomes a declared field in scope's risk contract
  or stays freeform prose in plan-review.
- Q3: whether plan-review needs a `scope expansion` finding disposition beside
  **blocks countersign** / **note**. Framing depends on Q2.
- Q4: home for the post-compaction ledger re-read. Defaulted to scope's `## Ledger`
  section, which already owns fresh-agent resume; state if you want it elsewhere.

## Spawned tasks

- none
