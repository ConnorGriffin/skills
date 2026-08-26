# Project

Connor Griffin's public, portable skill pack for coding agents. Skills live
under `skills/<category>/<name>/` (categories: `drivers`, `tools`,
`workflows`), one directory each, consumed by the standard `skills` CLI.
`profile/`, `output-styles/`, `hooks/`, and `docs/` sit alongside.

## Stack and constraints

* Python 3 standard library and Node 20 only; no third-party dependency may
  enter the pack (the browser driver under `skills/tools/drive-local-webapp`
  installs its own deps and is the sanctioned exception).
* `scripts/validate.py` is the structural gate, not a lint: it pins the
  expected skill set, requires `SKILL.md` plus `agents/openai.yaml` per
  skill, checks every relative markdown link, and runs a forbidden-pattern
  scan.
* Tests live in `tests/`; CI (`.github/workflows/validate.yml`) runs the
  validator, an enumerated unittest module list, an enumerated `py_compile`
  list, a fresh-install smoke check of a named skill subset, and
  `scripts/check_dco.py`.

## Conventions

* Every commit carries `Signed-off-by` (DCO); CI fails without it and history
  cannot be fixed after merge.
* Nothing merges without a pull request. PR bodies are written for the human
  who merges, in domain terms, and pass the `pr-body` skill's scorer.
* Release tags are never moved, retagged, or deleted: published releases are
  immutable history and installers may pin any ref.
* `.claude/skills/` and `.agents/skills/` are generated installed copies of
  this repo's skills; edit the source under `skills/`, never the copies.
* Engineering standards live in `profile/CHARTER.md` and bind review.
