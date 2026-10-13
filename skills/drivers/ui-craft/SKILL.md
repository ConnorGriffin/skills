---
name: ui-craft
description: Design and verify user-facing surfaces — settle structure first, lock a one-page design in the repo, then build or revise against it in a separate ticket, and review rendered UI. Use for any request to design, redesign, review, or verify screens, dashboards, flows, or components. Not for backend-only work or module/API design ("interface" in the code sense — use codebase-design for that).
---

# UI craft

A design session settles **structure before pixels**, then reviews at
**component grain** through eight gates. Each screen ends at the operator's
**"locked"** in a one-page lock doc that lives in the repo. The stage list lives
only in [reference/lock.md](reference/lock.md). Building screens is a separate
ticket, checked against that page and nothing else. Parts are derived from `impeccable` (Apache-2.0, by Paul Bakaus —
see the repo NOTICE).

Vocabulary guard: in the engineering charter, *interface* means a module's API.
This skill owns **surfaces**, meaning rendered UI. If the request is about a class,
function signature, or module boundary, this is the wrong skill.

## Modes

Route on the first word or obvious intent, then read that mode's reference
before acting. Never auto-run a mode.

| Mode | Job | Reference |
| --- | --- | --- |
| `lock [surface]` | The design lifecycle's eight gates, from structure to "locked" per screen; at most three rounds per gate | [reference/lock.md](reference/lock.md) |
| `library [component]` | `lock`'s library gate, run as its own ticket: the approved inventory built and reviewed one component at a time | [reference/library.md](reference/library.md) |
| `build [surface]` | Build ticket for a greenfield surface: assemble locked screens from the library, verified against the locked canvas | [reference/build.md](reference/build.md) |
| `revise [surface]` | Build ticket for a shipped surface: change the running app on a branch, keeping its must-survive behaviors | [reference/revise.md](reference/revise.md) |
| `review [target]` | Critique and technical audit of rendered UI, against the lock when one exists | [reference/review.md](reference/review.md) |

Routing, in prose:

- Designing or redesigning anything, shipped or not, goes to `lock`. A design
  session never builds screens. The `library` ticket is the only code written
  before a screen locks.
- A project that declines a component library takes `lock`'s plain-DOM path,
  which says what that path loses.
- After "locked", the build ticket runs `build` for a greenfield surface or
  `revise` for one the app already ships (ADR 48: a shipped surface is never
  rebuilt from a from-scratch mock).
- A fix inside an existing lock goes straight to `build` or `revise`: spacing, a
  bug, or a state the lock already lists. A change that adds or renames a
  screen, state, navigation item, gesture, or user-facing term reopens `lock`.
- With no argument, read `mockups/INDEX.md` and recommend one or two modes,
  then list the table.

[reference/tools.md](reference/tools.md) says how to use the harness's own design
tooling for these jobs: the Design and Design System artifact types,
`/design-sync` when the repo has a component library, artifact comments,
Claude in Chrome or the built-in browser, and the cold-critique subagent. Read
it before the first canvas, artifact, or browser step.

## Setup (every mode)

1. Read the repo's `CLAUDE.md`/`AGENTS.md` for these four things: personas, a
   declared real-data protocol, the safe dev-server entrypoint and its data
   source, and the design doc location.
2. Read `mockups/INDEX.md` and the surface's lock doc if one exists.
3. Read [reference/design-rules.md](reference/design-rules.md). Then read one
   register reference: [reference/brand.md](reference/brand.md) when the design
   *is* the product (marketing, landing, portfolio), or
   [reference/product.md](reference/product.md) when it *serves* the product (app
   UI, dashboards, tools).
4. For `library`, `build`, `revise`, and any change to CSS or JavaScript/TypeScript, read
   [reference/web-implementation.md](reference/web-implementation.md) first. It
   governs web mechanics. This skill keeps ownership of the lock and the rendered
   evidence.

## The lock is the contract

- **One page, in the repo.** It lives in the project's `DESIGN.md`, or in
  `docs/design/<surface>.md` when the project has several surfaces. It never
  lives in a scratchpad, a temp folder, or a canvas. The format is in
  [reference/lock.md](reference/lock.md).
- **Checked against the page and nothing else.** Prechecks, the cold critique,
  `review`, and the build's verification all read the lock doc. Anything the
  page does not say is not a requirement, and anything it bans is a failure.
- **No arbitration in private.** Stop and ask when one of these happens:
  - the lock contradicts the app's design system;
  - a build needs something the lock does not list;
  - a shipped behavior on the must-survive list would be lost.

  A changed term is a dated line under the lock's `Amendments`, carrying the
  operator's words, made in the same change. It is never a quiet edit.
- **Evidence over green gates.** A surface is done when its rendered screens
  match the lock at every frame and state the lock lists. A passing suite alone
  never finishes a surface.

## Surface ledger

`mockups/INDEX.md` holds one line per surface:

```text
- <surface> · <draft | locked | shipped> · <issue> · <lock doc path> · <canvas or artifact URL>
```

Every mode that changes a surface's status updates its line in the same change.

## Personas

`lock`'s cold critique and `review` walk the primary task as personas. **Repo
personas win:** if the repo defines its own (canonically
`.claude/qa/personas/*.md`, or a location its `CLAUDE.md`/`AGENTS.md` names), use
those instead of inventing equivalents. When the repo has its own sweep
protocol, follow it. Built-in archetypes fill only the roles the repo's set
lacks.

## Grounding rules (every mode)

- Ground everything in the app's real tokens, its shipping UI and chart library at
  the shipping version, and the real data *shape* from a **safe, manufactured
  fixture**. Never use production, personal, health, credential, or customer
  data. This default does not bend for convenience.
- **Never put real personal, health, or customer data on a canvas or artifact.**
  Both are published pages on claude.ai, however private their sharing setting.
- **Real-data inversion is repo-scoped and opt-in.** Some repos require build
  evidence grounded in the owner's own real data, because a fixture cannot show
  what the surface does at real scale. That inversion applies **only** where the
  repo's own `CLAUDE.md`/`AGENTS.md` declares an operator-sanctioned real-data
  protocol, and only within that protocol's bounds. Without that declaration, the
  manufactured default governs, and no exception is inferred from context or
  precedent. Where the inversion applies, real-data renders **stay local**: they
  are never published to a canvas or artifact, never committed, and never
  attached to a PR. Committed and published evidence uses labeled synthetic
  fixtures.
- Vary the concept, not the decoration. Three directions that differ only in
  color are one design.
- Judge a visual artifact by its rendered output in a real browser. Source review
  alone never validates one.
- **Sibling exactness:** an element with a sibling on a shipped surface uses the
  shipped values exactly. Prove it with computed styles read in the browser,
  never by eye.
