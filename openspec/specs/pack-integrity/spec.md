# Pack integrity

How the pack stays structurally valid for interactive readers and installers.

## Behavior

* `scripts/validate.py` discovers every `skills/<category>/<name>/` directory
  and fails unless the discovered set equals its hardcoded `EXPECTED` list
  (27 skills at baseline). Adding, renaming, or removing a skill is therefore
  always a deliberate two-place change.
* Each skill must carry `SKILL.md` with valid frontmatter and
  `agents/openai.yaml`. Every relative markdown link in the pack must
  resolve. A forbidden-pattern scan runs over tracked files.
* CI (`.github/workflows/validate.yml`) runs the enumerated unittest module
  list, enumerated `py_compile` script list, a fresh `npx skills add` smoke
  install asserting a named skill subset lands, and the DCO check. The
  unittest and `py_compile` lists are exhaustive: a new test module or skill
  script not added to them silently never runs.
* A pre-push hook mirrors validation and DCO locally.

## Invariants

* Stock Python 3 and Node 20 suffice to install and run the pack.
* Published release tags are immutable history; installers may pin any
  published ref.
* `.claude/skills/` and `.agents/skills/` are generated installed copies and
  are never edited directly.

## Dependents

The `skills` CLI installs from this layout. Interactive agents read the
source or installed skill files directly.
