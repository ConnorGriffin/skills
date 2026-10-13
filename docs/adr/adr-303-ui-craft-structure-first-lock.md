# ADR 303 — ui-craft: structure first, one-page lock, harness design tooling

Date: 2026-10-12
Status: accepted
Issue: https://github.com/ConnorGriffin/skills/issues/303

## Context

`ui-craft` had grown to about 22,400 lines. About 18,000 were a vendored
anti-pattern detector. The rest included context, palette, and critique-storage
scripts, a routing script, and fifteen reference pages. Locking a design meant
producing a behavior ledger, a committed replay script, a fidelity ledger, and
surface-ledger rows hundreds of words long. `behavior-sweep` and `resettle`
existed mostly to keep those artifacts consistent with each other.

The cost is measured. On 2026-10-12 the operator ran a redesign of a shipped app
without `ui-craft`, because the lock path was too heavy to start. The session
transcript shows:

- nine mockup rounds in 105 minutes;
- all feedback written as prose about pasted screenshots;
- agents inventing data labels the backend does not serve, continuing to write
  microcopy after it was banned, and renaming tabs every round;
- information architecture settled in rounds 6 to 8, after the visuals: which
  tab owns what, where sync errors live, and how touch gestures map to desktop;
- the only durable record of decisions left in a temporary scratch folder;
- after eight rounds the operator still rejected the craft as undesigned and
  uninspired, with three different sizes of buttons.

The operator's verdict on the skill was to drop the bloat and the jobs the
harness now does itself, and to tell the agent how to use those tools instead.
Claude Code now covers the dropped scripts' jobs:

- an artifact design skill that looks for the project's design system;
- the Design artifact type, a canvas of live artboards;
- the Design System artifact type;
- `/design-sync` for a repo with a compilable component library;
- artifact comments;
- Claude in Chrome and the desktop app's built-in browser.

## Decision

- **Structure before pixels.** `lock` starts with a structure step that the
  operator approves before any visual exists:
  - navigation names;
  - what each screen owns, and only that;
  - the screen and state inventory;
  - a touch-to-desktop interaction map;
  - a glossary of user-facing nouns and verbs;
  - the served vocabulary, traced to the backend.

  Questions go to the operator in one numbered round.
- **One-page lock doc in the repo.** It lives in `DESIGN.md` or
  `docs/design/<surface>.md`, never a scratchpad. It holds the structure,
  tokens copied from the running app's stylesheet, one size per component role,
  the absolute bans, and the approved screens. The build is checked against
  that page and nothing else. Amendments are dated lines carrying the
  operator's words.
- **Mechanical prechecks before the operator sees a render.** One
  standard-library Python script, `scripts/precheck.py`, checks rendered HTML
  against the lock: microcopy, label provenance, primary actions per screen,
  fixed widths past the frame, button sizes, and glossary use. It is honest
  that it reads static markup only. Layout is measured in the browser. A
  failing check withholds the render.
- **A cold critique, then at most three refinement rounds.** A fresh read-only
  subagent with a named model sees only the lock and the renders. After three
  rounds on the chosen direction, the skill stops and reports what is
  unresolved.
- **An explicit "locked" gate.** The operator's word "locked" marks the doc,
  writes a one-line `mockups/INDEX.md` entry (surface · status · issue · lock
  doc · URL), and files a separate build ticket. A design session never builds.
- **Tool instructions instead of bundled tooling.** `reference/tools.md` covers
  the Design type and the plain-artifact fallback, and when to use the Design
  System type or `/design-sync`. Every received comment is echoed back to the
  operator before acting, because both comment paths have documented delivery
  failures. Rendered verification uses the browsers.
- **Dropped:**
  - the behavior ledger, replay script, and fidelity ledger;
  - the `behavior-sweep`, `resettle`, `init`, and `document` modes;
  - `critique`, `audit`, and `polish`, merged into one `review` mode;
  - the vendored detector, `context.mjs`, `palette.mjs`,
    `critique-storage.mjs`, `context-signals.mjs`, `detect-csp.mjs`,
    `detect.mjs`, `route.mjs`, and `scripts/lib/`. Routing is now prose.
- **Kept:**
  - the grounding rules;
  - the repo-scoped, opt-in real-data inversion. Its renders now stay local
    and are never published to a canvas or artifact.
  - the craft bans and slop tests;
  - the brand and product register split;
  - repo personas winning over the built-in ones;
  - the "interface" vocabulary guard;
  - `web-implementation.md`;
  - `revise` for shipped surfaces.

## Amendment, 2026-10-12: component review grain

Before review, the operator chose a component as the review grain instead of a
screen. The eight rounds in the evidence session reviewed whole screens, and
three button sizes survived all of them. The default lifecycle for a surface
built from scratch or rewritten in place is now:

1. the structure step;
2. three directions on the Design canvas, concept only, until the operator
   picks one;
3. a gated **component inventory** in the lock doc: every component, with its
   states, the served fields it may show, a desktop equivalent for each touch
   gesture, and one size per role;
4. a **library** stage in its own ticket (`library` mode), one component at a
   time, with a story and a screenshot per state and prechecks per component.
   The operator reviews components in isolation, in batches of three to five,
   never as a full screen.
5. `/design-sync` mirroring the real library;
6. screens **composed** on the canvas from approved components only;
7. "locked" given per screen.

`build` then assembles the locked screens from the library and verifies them by
rendered comparison to the locked canvas.

Every stage is a gate, and the three-round cap applies per stage.

The best-supported stack is React + TypeScript + Storybook, which has the
Storybook MCP, `/design-sync`, and per-story screenshots. Web Components with
Storybook is the no-framework alternative, with weaker tool support. A repo
with no component library records its stack choice as an ADR in the build
ticket before the library stage.

A project that declines a library takes a plain-DOM path. It composes from
tokens and loses component-grain review and sync, and the lock doc's `Stack`
line says so.

The library ticket is the only code written before a screen locks. Screens are
still never built in a design session.

## ADR 48 still stands

A shipped surface is never rebuilt as a from-scratch mock and ported back. The
build ticket for a shipped surface runs `revise` against the running app,
behind the repo's declared safe dev-server entrypoint. Canvas directions for a
shipped surface are throwaway wireframes in ADR 48's sense: no fidelity claim,
never ported as code. What changes is the size of the record. The frozen
behavior ledger and replay script become the lock doc's `Must survive` list. It
is at most one page and is checked by rendered before and after evidence. A
dropped, changed, or moved behavior still blocks without a dated amendment.
This is a smaller mechanism for the same rule, not a reversal of it.

## Consequences

- An operator can start a redesign with one command and a one-page artifact
  instead of four ledgers.
- The skill stops shipping and maintaining about 21,000 lines of code it did
  not need.
- The replay script's mechanical guarantee is gone. A behavior absent from
  both the must-survive list and the before renders can now be lost without a
  red test. The structure step and the before renders are the defense, and
  that is the accepted cost.
- The precheck only sees what the render marks up. A label invented without
  `data-label` reaches the glossary check rather than the provenance check.
- The docs-site lock in this repo's `mockups/` predates the format and is kept
  as legacy history.
