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
  delta kinds, and source/base immutability; strict OpenSpec and full repository
  verification.

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
