# Scope ledger: 106-dco-merge-commits

## Decisions

- Classified as "nothing genuinely uncertain": the issue's Do/Boundaries fully
  bound the change, and the one open mechanical question (how the new test
  module gets wired into CI) resolves from this repo's own precedent, not
  judgment. `inline`
- Test module registration: every prior addition to `tests/` in this repo's
  history (e.g. `tests.test_codebase_memory_install`, commit b2f94db) was
  registered in the same PR in both `AGENTS.md`'s test command and
  `.github/workflows/validate.yml`'s unittest run line. The issue's boundary
  "No change to `.github/workflows/validate.yml`; the script owns the rule"
  reads narrowly — it protects the DCO gate step (the rule stays in
  `check_dco.py`, not the workflow), not a blanket freeze on the file. Adding
  the new test module name to the existing unittest list follows precedent
  exactly and does not touch the DCO gate step. `inline`
- No risk contract required: this is a bounded, ungrounded-in-user-facing-risk
  bug fix to a CI gate script with a boundary-fenced Do list; defaults (must
  prevent: gate weakening for authored commits, already stated as the issue's
  own boundary) are already explicit in the issue text. `inline`

## Open questions

(none — routed back to triage with no ambiguity requiring a human)

## Spawned tasks

(none)
