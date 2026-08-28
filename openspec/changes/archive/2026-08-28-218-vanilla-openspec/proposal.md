# Vanilla OpenSpec

## Why

The pack's hand-made OpenSpec conventions let behavior changes bypass
change-local requirements and leave the baseline stale. They also diverge from
the current CLI's v1.x tree and lifecycle.

## What changes

- Adopt upstream change-local spec deltas and archive them into the baseline.
- Backfill and reformat the three baseline specs into the CLI-enforced shape.
- Migrate the legacy OpenSpec tree, use the pinned CLI as dev/CI tooling, and
  align the OpenSpec-related skills with vanilla changes, ADRs, and epics.
- Archive completed changes after merge; freeze `docs/adr/` as legacy history.

## Risk contract

Strict CLI validation makes malformed baseline and delta requirements, including
missing scenarios, mechanically visible; archive merges validated deltas rather
than relying on a prose-only baseline convention. The CLI remains repository
dev/CI tooling, not a pack dependency, so the pack's stock Python 3 and Node
20 portability contract remains intact. Post-merge archiving still depends on
a human running it until this change specifies a mechanism.
