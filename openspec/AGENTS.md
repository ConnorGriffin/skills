# OpenSpec in this repo

* `specs/` holds the behavioral baseline: what the pack does today, grounded
  in code that was read. Correct it when it drifts; do not let it guess.
* `changes/<slug>/` holds one in-flight change: `proposal.md` (what and why,
  with the risk contract), `design.md` (rationale; ADRs live in `docs/adr/`
  per the charter's ADR-home rule, not here), and any change-specific state.
* A change is archived to `changes/archive/` in the pull request that
  finishes it, before that PR is marked ready — never in a follow-up commit
  after merge, never as a push onto an approved PR.
* An epic's change folder substitutes tracker child issues for `tasks.md` and
  carries `ledger.md`; see the epic driver skill once adopted.
