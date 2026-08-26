# Scope — 199 assurance-level matching

Route: interview mode. User declined the design menu and restated the ask: don't let
work get over-hardened, and don't let a compaction lose the ledger. All four open
questions were settled by the coordinator toward the smallest change that works.

## Decisions

- Ticket classification is `code`: prose changes landing as a pull request. inline
- Repo records changes with OpenSpec; the change folder is `openspec/changes/`. inline
- The failure this ticket fixes is mechanism escalation, not a wrong risk decision.
  plan-review axis 4 already forbids silently prescribing *hardening* when evidence
  shifts a risk decision; it says nothing about escalating the *mechanism* (parser,
  provenance record, state machine, content filter, runtime enforcement) above the
  assurance level the work was admitted at. inline
- Q1 settled: the rule lands in `profile/base.md` under Working preferences, not in
  `CHARTER.md`. The charter is the bar for shipped code and its violations are
  blocking findings; making over-hardening itself a blocking finding gives reviewers
  one more thing to argue, which is the disease. inline
- Q2 settled: no new `Assurance ceiling:` field in scope's risk contract. Adding a
  required field to every risk contract to prevent over-engineering is itself the
  failure mode. The rule is prose in plan-review, pointing at the risk contract that
  already exists. inline
- Q3 settled: no new finding disposition in plan-review. **blocks countersign** /
  **note** stay as they are; an over-hardening finding is discarded or raised to the
  user as a scope question, which the existing calibration section already covers. inline
- Q4 settled: the post-compaction re-read lands in plan-review's cycle, where the
  rounds happen, rather than in scope's `## Ledger` section. scope's ledger rule is
  about a *fresh agent* resuming; the observed loss was a *continuing* session that
  compacted mid-review and kept going. inline

### Risk contract

- **Must prevent:** a review round silently raising the assurance bar above what the
  admitted work declared, with no user decision.
- **Must recover:** nothing. There is no runtime here.
- **Accepted failure:** an agent misreads the rule and still over-hardens; the user
  says so and the round is redone. Consequence is one wasted round.
- **Unsupported:** enforcement. This is instruction prose read by agents; nothing
  parses, validates, or gates on it at runtime.
- **Evidence owed:** the pinned-prose tests this repo already uses for skill
  contract text (`tests/test_behavior.py` pattern), and nothing more.
- **Why:** the subject is agent-instruction prose with no execution surface, so the
  only real consequence of failure is a wasted review round.
- **Disposition:** admitted at intent level; a mechanism stronger than prose plus a
  string-pinning test is out of scope for this ticket by decision, not by oversight.

## Open questions

- none

## Spawned tasks

- none
