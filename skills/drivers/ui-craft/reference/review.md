# Mode: review

Judge rendered UI and report what to fix. Review does not fix anything. It
covers what used to be three passes: design critique, technical audit, and a
pre-ship polish walk. The persona archetypes and heuristic list are condensed
from `impeccable` (see the repo NOTICE).

## Setup

1. Resolve the target to a source path or URL, and render it with the browser
   pass in [tools.md](tools.md), at the lock's frames or at 390 and 1440 wide.
2. When a lock doc exists, run `precheck.py` on the saved HTML, with its frame
   declared per [lock.md](lock.md)'s precheck conventions. Then walk the
   lock section by section: structure, bans, components, approved screens, must
   survive. A lock violation is at least P1. "It looks fine" never closes one.
3. When review is `lock`'s cold critique or a build's verifier, it runs as a
   fresh read-only subagent with a named model ([tools.md](tools.md)).

## What to check

- **Design, in layers** ([design-rules.md](design-rules.md)): comprehension,
  product fit, composition, craft, interaction, then resilience. Apply the
  absolute bans and the slop test, plus the register's bans
  ([product.md](product.md) or [brand.md](brand.md)).
- **Heuristics:** Nielsen's ten. Score 0–4 only those the surface exercises:
  system status, match with the real world, user control, consistency, error
  prevention, recognition over recall, efficiency, minimalism, error recovery,
  and help.
- **Personas:** walk the primary task as two or three personas, repo personas
  first. Name the first element that stalls each walk. The built-in archetypes
  fill only the roles the repo's set lacks:
  - impatient power user: keyboard paths, no forced steps;
  - first-timer: labeled icons, an obvious first action, a way back;
  - screen-reader and keyboard user: focus, labels, announced state, never
    color alone;
  - stress tester: empty, huge, and long content, refreshes mid-flow, errors;
  - distracted one-handed phone user: target size, thumb reach, interruption.
- **Technical:**
  - contrast: body text at least 4.5:1, large text at least 3:1;
  - visible keyboard focus and a logical tab order;
  - targets at least 44px;
  - no horizontal scroll at any frame;
  - both themes;
  - reduced motion;
  - every empty, loading, and error state reachable and useful;
  - tokens used instead of hard-coded values.

## Report

Lead with the lock violations and precheck failures. Then give at most five
priority issues, each in this shape:

```text
[P0–P3] <what> — <who it hurts and how> — <exact fix> — <mode that fixes it>
```

- P0 blocks the task.
- P1 causes real difficulty.
- P2 is an annoyance with a workaround.
- P3 is polish.

The fixing mode is `revise` for a shipped surface, `build` for a greenfield
build in flight, and `lock` when the fix changes structure: a screen, a state,
a name, or a gesture. Do not praise the work or explain design theory.
Unverified findings are labeled as such, not reported as fact.
