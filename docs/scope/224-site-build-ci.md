# Scope ledger: 224-site-build-ci

## Decisions

- Classified as `code`: the deliverable changes a required CI workflow and lands
  as a pull request. `inline`
- `/scope` found nothing genuinely uncertain. Add the missing module and enforce
  equality between the two selections from the observed regression; keep explicit
  selection rather than introducing discovery or a shared runner. `inline`
- Surface lifecycle is `none`: no rendered surface changes. `inline`
- The work order is flat. No slicing trait fires; the workflow edit, regression
  assertion, and active change record are one coherent CI contract, closest to
  anchor A's one configuration change in one target. `inline`
- Review depth is `targeted`: the required CI behavior and its regression contract
  need end-to-end review, but the change is neither sensitive nor organization-wide
  inherited workflow machinery. `inline`
- Profile is `none`: `AGENTS.md` / `CLAUDE.md` declares no `Harden:` command.
  `inline`

### Risk contract

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

### Review rounds

- Panel 1: GPT-5.6-Terra returned `SHIP` with 0 blocking objections and 0
  notes after reproducing both generated evidence blocks. Authoring blockers: 0.
  Injected blockers: 0.
- Approval-copy re-check: shortening the reviewed draft injected 2 blockers: the
  host interpreter substitution was missing and the OpenSpec paths were no longer
  a closed allowlist. Both corrections were reproduced by the same reviewer, which
  returned `SHIP` with no new blocker. Authoring blockers: 0. Injected blockers: 2.

## Open questions

(none)

## Spawned tasks

- Mandatory cold plan review before the work order is shown or posted.

## Remaining dispositions

(none)
