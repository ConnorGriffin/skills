# Design

`ticket.py` remains the ticket workflow's command interface and gains one
applicability-preflight command. A separate production module would have only one
caller and would move the same subprocess, copy, and JSON handling behind another
name, so it would not survive the deletion test.

The command copies only the resolved repository's `openspec/` tree into a fresh
temporary directory and runs the pinned external interface there:
`openspec archive <change> --json --yes`. It does not emulate OpenSpec's merge
rules. Success requires process exit zero, a non-null `archive` object, and no
error-severity status. The reproduced 1.11.0 failure returns exit 1 and a JSON body
with `archive: null` and `archive_spec_update_failed`; parsing the JSON before
branching on process status preserves the actionable mismatch diagnostic.
Temporary-directory cleanup is automatic on success and failure.

`start` runs the command after review and any resulting edits, immediately before
the pull request opens. `revise` runs the same gate after its review-round edits
and before push. Finalization remains the only workflow phase that archives the
authoritative tree.

## ADR 265 — Prove applicability through a disposable real archive

**Status:** accepted

**Decision:** run the pinned OpenSpec archive command against a temporary copy and
judge its JSON result instead of implementing a second delta parser or performing
a reversible archive in the ticket worktree.

**Why:** the actual archive operation is the existing authority for applicability
and has no dry-run flag in OpenSpec 1.11.0. A disposable copy exercises that
authority while making pre-merge mutation of the active change and baseline
impossible, and parsing its JSON preserves the precise archive failure.

**Consequences:** preflight cost includes copying the OpenSpec tree and invoking
the CLI; malformed or changed JSON fails closed; diagnostics can identify the
unmatched requirement and the correction class but do not guess the old baseline
header; post-merge archive remains unchanged.
