# Epic gets a tracker bindings seam

## Why

The epic driver was GitHub-Issues-only: `SKILL.md` said "Use GitHub Issues only"
and kept all tracker mechanics in one `references/github-tracker.md`, with no
binding abstraction analogous to `ticket/bindings/*.md`. A consumer binding the
ticket skill to another tracker had no seam to bind epic against and would have
had to fork the whole driver.

## What changes

* The epic driver's GitHub mechanics move to `bindings/github-issues.md`,
  mirroring `ticket`'s layout, behind a new `references/tracker-contract.md`
  naming the four operations any binding must supply (create a native child,
  apply the protocol type labels, read the epic's children, file a review
  follow-up as a native child).
* `ticket`'s `references/review-actions.md` "Necessary follow-up" disposition
  points at the epic tracker contract instead of the old GitHub-only reference.
* Default installs behave identically: GitHub Issues remains the shipped
  binding, and no binding-selection machinery is added.

## Risk contract

- **Must prevent:** a live document or test pointing at the old
  `epic/references/github-tracker.md` path.
- **Must recover:** n/a; this is a path move plus a contract document, not a
  runtime behavior change.
- **Accepted failure:** none identified.
- **Unsupported:** binding-selection config, a second shipped binding, or any
  change to what epic's tracker operations do.
- **Evidence owed:** `scripts/validate.py` (skill set and link check) and the
  full unittest suite passing.
