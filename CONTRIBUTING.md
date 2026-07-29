# Contributing

Open an issue before making a large behavioral change. Small fixes can go
directly to a pull request.

Keep each skill self-contained, concise, and portable:

- Put triggering context in `SKILL.md` frontmatter.
- Keep machine-specific paths, personal data, credentials, generated files,
  and copied third-party skills out of the repository.
- Bundle deterministic helpers under the skill's `scripts/` directory.
- Document optional upstream dependencies rather than copying them.
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
