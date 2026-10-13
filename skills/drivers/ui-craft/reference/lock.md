# Mode: lock

The design lifecycle for a surface built from scratch or rewritten in place,
shipped or greenfield. **The review grain is a component, not a screen.** The
operator approves components in isolation, then screens composed only from
approved components.

Every stage below is a gate the operator approves before the next one starts:

1. **Structure:** names, ownership, states, interactions, glossary. No pixels.
2. **Lock prep:** tokens and the library stack.
3. **Directions:** three concepts on the Design canvas. The operator picks one.
4. **Component inventory:** every component the chosen direction needs.
5. **Library:** each component built in the project's component library, in
   its own ticket (`library`, [library.md](library.md)).
6. **Sync:** `/design-sync` mirrors the real library onto the canvas.
7. **Compose:** each screen on the canvas, from approved components only.
8. **"Locked":** given per screen.

After that, `build` (greenfield) or `revise` (shipped) assembles the locked
screens from the library. **Screens are never built in a design session.** The
library ticket is the only code before a screen locks.

The order matters because a redesign that skips it fails in a predictable way.
Visuals come first. Labels get invented that the backend does not serve, tabs
get renamed every round, and the review drifts across whole screens, so three
button sizes survive eight rounds. The only record ends up in a scratch folder.

## How every gate runs

- **Before the operator sees anything**, the stage's renders pass `precheck.py`
  and the browser pass, and a cold critique has run (below). A failing check
  means the operator does not see that render.
- **Echo every comment and instruction received** back to the operator as a
  numbered list before acting, and ask them to name anything missing.
- **At most three refinement rounds per stage.** After the third, stop. Report
  what is unresolved, and offer three options: approve as it stands, amend an
  earlier stage, or end here. Never run a fourth round on your own.
- Nothing already ruled reopens. A change to a name, screen, state, or gesture
  amends the structure sections first.
- Each approval is a dated line under the lock doc's `Amendments`, carrying the
  operator's words.

### Prechecks

```sh
python3 <ui-craft-skill-directory>/scripts/precheck.py <render.html | dir> <lock doc>
```

The script checks six things:

- microcopy: sentences, rhetorical questions, and explanatory subtitles not in
  `Allowed strings`;
- provenance: every `data-label` is in `Served vocabulary`;
- one primary action per screen (each component story counts as a screen);
- fixed widths wider than the narrowest frame;
- distinct button sizes against `Button sizes:`;
- glossary: every short visible term is in the glossary or another lock list.

Renders mark the conventions the script reads:

- `data-screen` on each screen or story root;
- `data-label` on served-data labels;
- `data-value` on served values;
- `data-primary` on the one primary action.

The script reads static markup only. The browser pass in [tools.md](tools.md)
measures real overflow and rendered button heights. Paste the full output into
the round.

### Cold critique

Dispatch a fresh, read-only subagent with a named model, as
[tools.md](tools.md) describes. Give it only the lock doc and the stage's
renders: no transcript, no rationale. It reports violations of the lock, the
[design-rules.md](design-rules.md) bans and slop test, and, for directions and
composed screens, a persona walk of the primary task, using repo personas
first. Fix each confirmed finding and rerun the prechecks. Carry any rejected
finding to the operator with the reason it was rejected.

## 0. Embodiment

Check the app's routes, its render modules, and `mockups/INDEX.md`.

- **Greenfield:** nothing ships yet, and the build ticket will run `build`.
- **Shipped:** the app already renders this surface or the shell it lives in.
  The build ticket will run `revise` against the running app, rewriting in
  place from library components. Canvas directions are throwaway wireframes.
  They carry no fidelity claim, and their code is never ported (ADR 48).
  Capture "before" renders now through the repo's declared safe entrypoint,
  or ask the operator for captures. Never start an undeclared entrypoint.

## 1. Structure (no pixels)

Write the lock doc's structure sections from the code and the operator's brief:
`Navigation`, `Screens`, `States`, `Interaction map`, `Glossary`,
`Served vocabulary`, and, for a shipped surface, `Must survive`. Read the API or
model code for the served vocabulary. A label nobody serves does not appear on
any screen.

- **Navigation:** every tab and navigation name, spelled exactly as it shows.
- **Screens:** what each screen owns, and only that. Each fact lives on exactly
  one screen. Name what a screen does *not* own, and which screen owns it.
- **States:** for each screen, its empty, loading, and error states, plus each
  transient state (syncing, offline, saving, partial data). Say where each
  error surfaces.
- **Interaction map:** every touch gesture and its desktop equivalent. A swipe,
  long-press, or pull without a pointer or keyboard equivalent is unfinished.
- **Glossary:** every user-facing noun and verb, navigation names included, each
  with a one-line meaning. A name changes only by amendment.
- **Must survive (shipped only):** what users rely on today, at most one page.
  One line per behavior, plus where a render shows it.

Put every question whose prerequisites are settled into **one numbered round**:
the symptom, the options with their costs, and a recommendation. The operator
approves the structure before any pixel exists.

## 2. Lock prep

Fill in `Tokens`, `Stack`, `Frames`, `Button sizes`, `Bans`, and
`Allowed strings`.

- **Tokens** come from the running app's stylesheet: palette in both themes,
  type scale, spacing, and radius. Copy them from that file and cite its path,
  never transcribe them from memory. A greenfield app with no stylesheet
  commits to a small set here.
- **Stack:** the project's component library, or `plain-DOM (declined)`. A repo
  with no library picks a stack per [tools.md](tools.md). The build ticket
  records that choice as an ADR before the library stage.
- Set up the canvas's design system as [tools.md](tools.md) describes.

## 3. Directions (concept only)

Make **three genuinely different directions** on a Design canvas
([tools.md](tools.md)). Vary the concept and layout: information hierarchy,
layout metaphor, interaction model. Never vary only color. Draw each direction
at every frame in `Frames:`, phone and desktop at least. Draw the primary screen
in its typical state and in one hard state (empty or error). Use manufactured
data only.

The directions settle concept, not craft. Present each with a one-line bet,
its cost, and the critique's open findings, and recommend one. The gate passes
when **the operator picks one**. Refinement rounds here may sharpen the
concept, but component detail waits for the inventory.

## 4. Component inventory

Fill in `Components` for the chosen direction. Every component appears once,
with:

- its states (default, hover, focus, active, disabled, loading, error, and any
  empty or transient state it shows);
- the served data fields it may show, each one in `Served vocabulary`;
- its desktop equivalent for each touch gesture;
- one size per role, with height, padding, and type given once.

The inventory is a gated deliverable. The operator approves the list itself
before any component is built.

## 5. Library

The `library` ticket builds the approved inventory one component at a time,
following [library.md](library.md). Each component gets a story per state and a
screenshot per story, with prechecks run per component. The operator reviews
components **in isolation, in batches of three to five, never as a full
screen**. Each batch is a gate.

## 6. Sync

Once the batches are approved, run `/design-sync` from the repo root. The
canvas then mounts the real library, not look-alikes. Confirm that one
synced component's values match the lock's `Tokens`.

## 7. Compose

Compose each screen on the Design canvas **from approved components only**, at
every frame and in every state the lock lists. A screen that needs a component
not in the inventory goes back to stage 4: amend the inventory, then build the
component as its own library batch. Never draw a one-off.

## 8. "Locked", per screen

The operator saying **"locked"** about a screen is the only approval. Then, in
one change:

1. Add the screen, its frames, and its canvas URL to `Approved screens`. When
   every screen is locked, set `Status: locked <date> by <operator>`.
2. Update the surface's one line in `mockups/INDEX.md`.
3. File or update the **separate build ticket**. It names the lock doc path,
   the locked screens and their canvas URLs, and `build` or `revise`.
4. Commit the lock doc and the INDEX line.

## Plain-DOM path (no library)

A project that declines a component library skips stages 4 to 6. After the
direction is picked, it composes screens straight from `Tokens` and a
`Components` list of sizes per role, then locks per screen. It loses two
things, and the lock doc says so in `Stack`:

- **component review grain:** the operator reviews whole screens, which is
  where inconsistencies like three button sizes hide;
- **sync:** the canvas draws look-alikes, so the build is compared against
  drawings rather than the parts it will actually use.

## Lock doc format

Keep it to one page. `precheck.py` reads three headings: `Glossary`,
`Served vocabulary`, and `Allowed strings`. It also reads the `Frames:` and
`Button sizes:` lines. A bullet's text before ` — ` is the entry, matched
without regard to case.

```markdown
# <Surface> — design lock
Status: draft | locked <YYYY-MM-DD> by <operator>
Embodiment: greenfield (build) | shipped (revise)
Stack: <library and its location> | plain-DOM (declined; screen-grain review, no sync)
Frames: 390x844, 1440x900
Button sizes: 1
Canvas: <canvas or artifact URL>

## Navigation
- <Tab name> — <what it opens>
## Screens
- <Screen> — owns: <job>. Not here: <thing>, which lives on <screen>.
## States
- <Screen>: empty — …; loading — …; error — … (shown where); <transient> — …
## Interaction map
- <gesture> on <element> — desktop: <pointer or keyboard equivalent>
## Glossary
- <Term> — <one-line meaning>
## Served vocabulary
- <Label> — <endpoint or model field that serves it>
## Allowed strings
- <exact string a screen may show beyond glossary terms>
## Tokens
- Source: <app stylesheet path>
- Color, type scale, spacing, radius: <values>
## Components
- <Component> — states: …; fields: …; gestures: <touch> → <desktop>; size: <role: height, padding, type>; story: <path>; approved: <date>
## Bans
- No microcopy: no explanatory sentences, rhetorical questions, or
  subtitles that explain the screen. Only Allowed strings.
- No predictions or claims the backend does not serve.
- No invented labels or data: every label is in Served vocabulary.
- Color is never the only signal.
- At most one primary action per screen.
- No content on a screen that does not own it.
- Plus every absolute ban in design-rules.md.
## Must survive (shipped only)
- <behavior> — seen in: <screen and state>
## Approved screens
- <Screen> at <frames> — <canvas URL> — locked <date>
## Amendments
- <YYYY-MM-DD> <operator>: <what changed or was approved>, "<their words>"
```
