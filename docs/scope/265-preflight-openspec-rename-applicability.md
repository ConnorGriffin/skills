# Scope: preflight OpenSpec rename applicability

## Decisions

- Use the existing `ticket.py` command interface rather than a one-caller module.
  Why: the behavior belongs to ticket execution and the separate module would not
  survive the deletion test. Disposition: → ADR (ADR 265 in the active change).
- Export the freshly fetched base ref's current OpenSpec tree, overlay the ticket's
  one active change, and run the real archive command in that disposable composite.
  Why: OpenSpec 1.11.0 has no archive dry-run, and the composite catches baseline
  advances without mutating or rebasing the ticket branch. Disposition: → ADR (ADR
  265 in the active change).
- Zero changed active changes is a no-op, exactly one is preflighted, and more than
  one stops. Why: an ordinary ticket owns one active change and finalization owns one
  archive; independent multi-change checks cannot prove serial interaction.
  Disposition: inline.
- Every ordinary OpenSpec-backed caller fetches `origin` immediately before the gate
  and stops on fetch or base-ref failure. Why: the remote fixture proves a stale
  tracking ref passes before fetch and fails after refresh. Disposition: inline.
- Archive applicability mismatch has exactly two ordered `ticket:` stderr lines:
  the unmatched requirement first, then rename/header correction guidance; every
  other failure has one diagnostic. Why: this preserves the already-executed public
  behavior without contradicting the general result contract. Disposition: inline.
- Capture the complete raw OpenSpec archive stdout, stderr, and exit status for the
  historical failure before admitting an implementation order. Why: the command's
  parsed `archive: null` and `archive_spec_update_failed` shape is load-bearing
  third-party behavior and the existing generated facts suppress those bytes.
  Disposition: inline.
- Slice implementation into two serial chunks: the public CLI and executable
  contract evidence first; its three workflow consumers and OpenSpec contract
  alignment second. Why: both multiple-deliverable-artifacts and lockstep-copies-of-
  one-fact fire, matching the repository's shared-interface-plus-consumers anchor.
  Disposition: inline.

### Risk contract

- **Must prevent:** mutating, folding, moving, or archiving the authoritative active
  change or baseline before merge; approving a stale-base, null, error, malformed,
  or wrong-typed archive result; secret exposure, irreversible authoritative-data
  loss, or silent incorrect success.
- **Must recover:** temporary export/overlay or CLI failure stops visibly and the
  disposable directory is cleaned automatically.
- **Accepted failure:** unexpected third-party output, fetch failure, unresolved
  base, or several active ticket changes stops for manual correction/re-scoping.
- **Unsupported:** automatic delta repair, inferring old requirement headers,
  multi-change ordinary tickets, changing OpenSpec's validator, or replacing the
  post-merge archive lifecycle.
- **Evidence owed:** public-command tests for historical #259, changed-path
  discovery, JSON shapes, current-base composition, fetch timing/failure, ordinary
  delta kinds, source/base immutability, executable launch failure, base export
  failure, overlay failure, and temporary-directory cleanup on every recovery path;
  strict OpenSpec and full repository verification.

Why: this prices the smallest non-mutating gate that prevents the observed
post-merge failure. Disposition: inline.

## Open questions

None.

## Spawned tasks

None.

## Review rounds

- Panel 1 initial cold pass: five `authoring` blockers — no durable #259 evidence;
  unspecified change discovery/chunked caller; revise record edits after push;
  under-specified JSON shape; missing host-interpreter substitution.
- Panel 1 re-check 1: one `authoring` blocker (caller-owned base source) and two
  `injected` blockers (deleted-path discovery and unsound independent multi-change
  support).
- Panel 1 re-check 2: one `authoring` blocker (stale ticket baseline copied into the
  simulation) and one `injected` blocker (chunked spec still said every delta).
- Panel 1 re-check 3: one `injected` blocker — remote-tracking base was not refreshed
  immediately before flat/coordinator preflight.
- Panel 1 re-check 4: one `injected` blocker — revise's earlier rebase fetch left the
  same stale-ref window before its gate.
- Panel 1 re-check 5: no blockers; same-reviewer `PASS`. Fresh cold countersign still
  required.
- Panel 2 fresh cold pass: three `authoring` blockers — missing non-OpenSpec caller
  bypass; incomplete shared CLI invocation/result contract; test plan promised only
  source-tree rather than separate source/base immutability evidence.
- Panel 2 re-check 1: one `injected` blocker — the new bypass scenario conflicted
  with universal wording retained in the requirement, proposal, and scope decision.
- Panel 2 re-check 2: two `injected` blockers — generic start/coordinator scenario
  clauses still implied universal preflight, and proposal evidence still named only
  source-tree rather than separate ticket/base digests.
- Panel 2 re-check 3: one `injected` blocker — the ADR design retained universal
  caller wording after the requirement, proposal, scope decision, and work order
  had qualified the gate as ordinary OpenSpec-backed only.
- Panel 2 re-check 4: no blockers; same-reviewer `PASS`. A third fresh cold panel
  remains required for the full-depth countersign.
- Panel 3 fresh cold pass: four `authoring` blockers — contradictory one-line versus
  two-line mismatch diagnostics; raw third-party failure JSON absent from generated
  facts; missing launch/export/overlay cleanup acceptance; and a flat shape despite
  both multiple-artifact and lockstep-copy traits. The three-panel cap was reached,
  so the order was not countersigned or posted and these decisions returned to
  scope.
- Renewed cycle, panel 1 cold pass: one `authoring` blocker — the order assigned
  executable stale-remote proof to three Markdown workflow consumers. The public
  command owns that fixture; consumer evidence is prose-contract assertions for
  eligibility, ordering, base refs, bypass, and outbound boundaries.
