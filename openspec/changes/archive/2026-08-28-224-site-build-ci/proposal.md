# Keep the documented and CI test selections aligned

## Why

The repository's documented verification command names
`tests.test_site_build`, but the primary validation workflow omits it. A
contributor can therefore follow the repository's own gate while the required CI
job silently exercises a narrower unittest selection.

## What changes

- Run `tests.test_site_build` in the primary validation workflow.
- Add a regression check that keeps the documented unittest module selection and
  the primary validation workflow's selection equal.
- Keep explicit test selection; do not replace the repository's named lists with
  automatic discovery.

## Risk contract

- **Must prevent:** silent divergence between the unittest modules promised by the
  repository's documented test command and those run by the primary validation
  workflow; weakening unrelated CI checks; secret exposure; irreversible loss of
  authoritative data; silent incorrect success.
- **Must recover:** nothing. This is a pre-merge repository gate with no runtime
  state to recover.
- **Accepted failure:** a parity failure stops verification and requires a
  contributor to align the two selections manually before merge.
- **Unsupported:** discovering every test module from the filesystem or enforcing
  parity with the separate documentation-publication workflow. Named selections
  remain explicit by repository policy.
- **Evidence owed:** a public-interface regression test that fails on the observed
  mismatch and passes after `tests.test_site_build` joins the primary workflow,
  plus the repository's documented full verification command.
- **Why:** the observed failure is a two-list drift in a pre-merge gate; a focused
  parity assertion closes that failure without introducing a new runner or parser
  dependency.
- **Disposition:** admitted; automatic test discovery and CI centralization are out
  of scope.
