# Pack integrity

How the pack guarantees a consumer installs exactly what was reviewed.

## Behavior

* `scripts/validate.py` discovers every `skills/<category>/<name>/` directory
  and fails unless the discovered set equals its hardcoded `EXPECTED` list
  (27 skills at baseline). Adding, renaming, or removing a skill is therefore
  always a deliberate two-place change.
* Each skill must carry `SKILL.md` with valid frontmatter and
  `agents/openai.yaml`. Every relative markdown link in the pack must
  resolve. A forbidden-pattern scan runs over tracked files.
* `docs/evidence/contract-v2.json` is verified byte-for-byte against a
  SHA-256 recorded in the validator, pinned to a commit of the upstream
  `ConnorGriffin/agentflow` repo. Any edit to that file fails validation
  here; changing it is upstream work.
* CI (`.github/workflows/validate.yml`) additionally runs an enumerated
  unittest module list, an enumerated `py_compile` script list, a fresh
  `npx skills add` install asserting a named subset of skills lands, and the
  DCO check. The unittest and `py_compile` lists are exhaustive: a new test
  module or skill script that is not added to them silently never runs.
* A pre-push hook mirrors validation and DCO locally.

## Invariants

* Stock Python 3 and Node 20 suffice to install and run the pack.
* Release tags are immutable; agentflow pins this repo by tag, commit, and
  per-file SHA-256 (`agentflow/capabilities.toml`, `skills-lock.json`).
* `.claude/skills/` and `.agents/skills/` are pinned vendored copies of the
  pack's own skills and are never edited directly.

## Dependents

The `skills` CLI installs from this layout; agentflow's pins name individual
file paths, so path renames under `skills/` are breaking changes for it.
