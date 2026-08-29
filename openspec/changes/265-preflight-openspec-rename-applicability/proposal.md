# Preflight OpenSpec applicability before merge

## Why

OpenSpec 1.11.0 strict validation accepts a structurally valid change whose
`MODIFIED Requirements` header does not exist in the current baseline. The first
applicability check is then the post-merge `openspec archive` operation. Issue
259 demonstrated that this leaves a merged implementation waiting on a manual
delta repair before ticket finalization can complete.

## What changes

- Add a ticket command that proves an active OpenSpec change can archive by
  running the pinned CLI against a disposable copy of the repository's OpenSpec
  tree and inspecting its JSON result.
- Make `start` run that preflight after the final implementation/review edits and
  before opening the pull request; make `revise` repeat it before pushing an
  amended OpenSpec-backed change.
- Report an unmatched modified requirement and direct the author to add the
  missing `RENAMED Requirements` mapping or correct the modified header.
- Preserve the authoritative active change and baseline until the existing
  post-merge archive lifecycle runs.

## Risk contract

- **Must prevent:** mutating, folding, moving, or archiving the authoritative
  active change or baseline before merge; accepting process exit zero when the
  archive JSON reports no archive or an error; secret exposure, irreversible loss
  of authoritative data, or silent incorrect success.
- **Must recover:** temporary-copy creation or CLI execution failure must stop the
  workflow visibly and clean up the disposable copy.
- **Accepted failure:** malformed or unexpected third-party CLI output stops the
  pull request with the raw diagnostic available for manual investigation; no
  automatic recovery is required.
- **Unsupported:** repairing deltas automatically, inferring a missing old header,
  changing OpenSpec's validator, or replacing post-merge archive guidance.
- **Evidence owed:** public-command tests reproduce strict-validation success
  followed by archive applicability failure, prove a correct rename passes, and
  prove the source OpenSpec tree is byte-for-byte untouched; OpenSpec validation
  and the repository gate pass.
