# Preflight OpenSpec applicability before merge

## Why

OpenSpec 1.11.0 strict validation accepts a structurally valid change whose
`MODIFIED Requirements` header does not exist in the current baseline. The first
applicability check is then the post-merge `openspec archive` operation. Issue
259 demonstrated that this leaves a merged implementation waiting on a manual
delta repair before ticket finalization can complete.

## What changes

- Add a ticket command that discovers the active OpenSpec change modified by an
  ordinary ticket branch relative to a caller-owned base ref, then proves it can archive by
  overlaying that ticket change onto a disposable export of the base ref's current
  OpenSpec tree, running the pinned CLI there, and inspecting its JSON result.
- Treat no changed active change as a command no-op, ignore historical paths
  absent from the ticket tree, and stop when one ordinary ticket changes more than
  one active change because finalization owns only one serial archive.
- Invoke the gate only for ordinary tickets using the OpenSpec change-record path;
  leave other/no change-record conventions and epic children unchanged.
- Make flat and chunked `start` run that preflight after the final
  implementation/review/change-record edits and before opening the pull request;
  refresh the remote base immediately before that gate in every caller, and make
  `revise` update its change record before its own final refresh and gate.
- Report an unmatched modified requirement and direct the author to add the
  missing `RENAMED Requirements` mapping or correct the modified header.
- Preserve the authoritative active change and baseline until the existing
  post-merge archive lifecycle runs.

## Risk contract

- **Must prevent:** mutating, folding, moving, or archiving the authoritative
  active change or baseline before merge; accepting process exit zero when the
  archive JSON reports no archive or an error; secret exposure, irreversible loss
  of authoritative data, accepting an unexpected JSON shape, or silent incorrect
  success.
- **Must recover:** executable launch, base export, overlay, temporary-copy, or CLI
  execution failure must stop the workflow visibly and clean up the disposable
  copy.
- **Accepted failure:** malformed or unexpected third-party CLI output stops the
  pull request with the raw diagnostic available for manual investigation; no
  automatic recovery is required.
- **Unsupported:** repairing deltas automatically, inferring a missing old header,
  changing OpenSpec's validator, or replacing post-merge archive guidance.
- **Evidence owed:** public-command tests reproduce strict-validation success
  followed by archive applicability failure, prove a correct rename passes, and
  compare separate before/after digests for the ticket worktree and base-ref
  OpenSpec trees on both success and archive failure; boundary-fake tests cover
  executable launch, base export, and overlay failure with nonzero diagnostics and
  temporary-directory cleanup; an option-shaped base ref is rejected locally without
  a remote invocation; OpenSpec validation and the repository gate pass.
