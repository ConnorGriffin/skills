# Contributing

Open an issue before making a large behavioral change. Small fixes can go
directly to a pull request.

Keep each skill self-contained, concise, and portable:

- Put triggering context in `SKILL.md` frontmatter.
- Keep machine-specific paths, personal data, credentials, employer names,
  internal hostnames, ticket ids, and generated files out of the repository.
  `scripts/validate.py` enforces this on the working tree.
- Third-party skills may be included only under a compatible license with
  attribution preserved in `LICENSE` and `NOTICE`, and must be edited to be
  self-contained (no dangling references to skills or files not in this pack).
- Bundle deterministic helpers under the skill's `scripts/` directory.
- Document optional upstream dependencies in the README rather than copying
  them when a reference can simply stay optional.
- Run `python3 scripts/validate.py` before opening a pull request.
- Install the publish guard once per clone, so validation **and the DCO check**
  run before a push instead of after the tree is already public:
  `ln -sfn ../../scripts/pre-push .git/hooks/pre-push`. It composes with a
  global `core.hooksPath` dispatcher rather than replacing it. Installing it is
  worth the one command: a missing `Signed-off-by` caught before a push is one
  `git rebase --signoff`, while the same miss caught by CI afterwards means
  rewriting commits other people may already have pulled.

## Developer Certificate of Origin

Every commit must certify the
[Developer Certificate of Origin 1.1](https://developercertificate.org/) by
including a `Signed-off-by` trailer:

```sh
git commit -s -m "Describe the change"
```

By signing off, you certify that you have the right to submit the contribution
under this repository's license.
