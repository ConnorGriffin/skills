# Design

`ticket.py` remains the ticket workflow's command interface and gains one
applicability-preflight command. Its workflow form receives the checkout and a
caller-owned base ref, resolves that ref locally with Git's end-of-options form to a
verified commit object ID, resolves the merge base with the ticket branch, and derives
non-archive `openspec/changes/<name>/` directories changed by that diff and still
present in the ticket tree. No changed active directory is a successful no-op;
exactly one is preflighted; more than one stops visibly because this ordinary-ticket
lifecycle owns one active change and finalization defines no serial multi-change
archive. A separate production module would have only one caller and would move the
same discovery, subprocess, copy, and JSON handling behind another name, so it
would not survive the deletion test.

The public command is `ticket.py preflight-openspec --repo <ticket-worktree>
--base-ref <ref>`. Both options are required. It returns success for zero changed
active changes, success with the checked name for one applicable change, a usage-
class stop naming sorted changes for more than one, and one `ticket:` diagnostic on
stderr for every failure except `archive_spec_update_failed`. That applicability
failure emits exactly two ordered `ticket:` lines: the CLI's unmatched requirement,
then rename/header correction guidance. Workflow callers invoke the command only
after selecting the existing ordinary OpenSpec change-record route.

The command exports the resolved commit object's current `openspec/` tree into a fresh
temporary directory, overlays only the ticket worktree's one active change
directory, and runs the pinned external interface there: `openspec archive
<change> --json --yes`. It does not emulate OpenSpec's merge rules. Using the locally
resolved base commit rather than the ticket branch's stale baseline catches an applicability change
that landed after branch cut without rebasing or mutating the ticket branch.
Success requires process exit zero, a top-level JSON object with a non-null archive
object, and no error-severity entry in an optional status list of objects.
The generated-facts reproduction captures the complete OpenSpec 1.11.0 stdout,
stderr, and exit status: exit 1, `archive: null`, and an error status whose code is
`archive_spec_update_failed`. Parsing the JSON before branching on process status
preserves the actionable mismatch diagnostic. Temporary-directory cleanup is
automatic on success and every launch, export, overlay, CLI, or parse failure.

For an ordinary OpenSpec-backed ticket, flat `start` and chunked coordinator mode
fetch `origin` immediately before passing `refs/remotes/origin/HEAD`, whose merge
base names the default-branch base of the ticket worktree; a fetch or unresolved-ref
failure stops. Flat start runs after review and any resulting change-record edits,
immediately before the pull request opens. Chunked coordinator mode runs after
merged-branch review and change recording, before it rejoins pull-request creation.
For an ordinary OpenSpec-backed `revise`, the workflow completes its existing
fetch/rebase plus all active-change/checklist/decision edits, then fetches `origin`
again immediately before passing refreshed `origin/<baseRefName>` to the gate, then
pushes. Other or absent change-record conventions and epic children bypass this
command unchanged. Finalization remains the only workflow phase that archives the
authoritative tree.

## ADR 265 — Prove applicability through a disposable real archive

**Status:** accepted

**Decision:** run the pinned OpenSpec archive command against a temporary composite
of the base ref's current OpenSpec tree plus the ticket's one active change, and
judge its JSON result instead of implementing a second delta parser or performing a
reversible archive in the ticket worktree.

**Why:** the actual archive operation is the existing authority for applicability
and has no dry-run flag in OpenSpec 1.11.0. A disposable copy exercises that
authority while making pre-merge mutation of the active change and baseline
impossible, and parsing its JSON preserves the precise archive failure.

**Consequences:** preflight cost includes resolving a merge base, diffing the branch,
exporting the base OpenSpec tree, overlaying the active change, and invoking the CLI once; deleted or renamed-away paths
do not become false active changes; a multi-change ordinary ticket must be
re-scoped instead of receiving a misleading independent pass; malformed or changed
JSON fails closed; diagnostics can identify the unmatched requirement and the
correction class but do not guess the old baseline header; post-merge archive
remains unchanged.
