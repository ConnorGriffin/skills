# Contributing

Open an issue before making a large behavioral change. Small fixes can go
directly to a pull request.

Keep each skill self-contained, concise, and portable:

- Put triggering context in `SKILL.md` frontmatter.
- Keep machine-specific paths, personal data, credentials, and generated files
  out of the repository.
- Third-party skills may be included only under a compatible license with
  attribution preserved in `LICENSE` and `NOTICE`, and must be edited to be
  self-contained (no dangling references to skills or files not in this pack).
- Bundle deterministic helpers under the skill's `scripts/` directory.
- Document optional upstream dependencies in the README rather than copying
  them when a reference can simply stay optional.
- Run `python3 scripts/validate.py` before opening a pull request.

## Developer Certificate of Origin

Every commit must certify the
[Developer Certificate of Origin 1.1](https://developercertificate.org/) by
including a `Signed-off-by` trailer:

```sh
git commit -s -m "Describe the change"
```

By signing off, you certify that you have the right to submit the contribution
under this repository's license.
