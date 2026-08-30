# Slicing calibration accrues per repository

## Why

Slicing lessons had two homes. Every finished ticket already appended a measured
slicing record to the target repository's reviewer-memory store, which triage
reads; but on an `under-sliced`, `still-degraded`, or `over-sliced` verdict,
`finalize` also drafted a diff against `ticket/references/slicing.md`, showed it
to the operator, and waited for them to land it as a skills-repo pull request.

That second channel does not fit what slicing calibration is. The rubric's anchor
table held rows measured on one operator's machine against particular
repositories (`259 (skills)`, `253 (harmonic)`), so a lesson from one repository
was growing into the rubric every installation inherits. It also put an operator
prompt and a pull request on the finalize path, which the operator does not want.

## What changes

* `finalize`'s misprediction path becomes report-only: it says which rubric call
  was wrong and by how much, and stops. The slicing record it already appended to
  this repository's reviewer-memory store is the durable calibration. It drafts no
  rubric diff, offers no pull request, and asks the operator nothing here. The
  abandoned-ticket confirmation, which guards a destructive teardown, is untouched.
* `references/slicing.md` loses its anchor table and keeps only repo-agnostic
  instruction: the trait rubric, the sizing thresholds, chunk shape, and
  orchestrator tier. Its provenance section points calibration at each
  repository's reviewer-memory store.
* `triage` reads that store for the anchors the traits are calibrated against,
  and records which anchor the ticket matched or that none was nearby.
* Repo-attributed anchor rows migrate to the matching reviewer-memory store's
  slicing digest; rows with no resolvable repository identity are dropped, their
  lessons already being in the thresholds.

## Risk contract

- **Must prevent:** `finalize` prompting the operator or proposing a rubric
  change on a misprediction verdict; a measured anchor for one repository living
  in the shared rubric.
- **Must recover:** n/a; no runtime state changes. The `append-slicing` pipeline
  and its record bytes are untouched.
- **Accepted failure:** a repository with no accumulated slicing records gets the
  bare thresholds and no anchors until it finishes a few tickets.
- **Unsupported:** cross-repo learning (per the #197 risk contract), moving the
  180k/120k constants, and implementing reviewer-memory's documented-but-absent
  `distill` command.
- **Evidence owed:** the repository gate (`scripts/validate.py` plus the named
  unittest modules and `py_compile`) and `openspec validate --all --strict`.
