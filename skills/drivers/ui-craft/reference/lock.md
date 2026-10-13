# Mode: lock

The design session for one surface, shipped or greenfield. Its order is fixed:
structure, then lock prep, then directions, prechecks, a cold critique, and at
most three refinement rounds. It ends at the operator's "locked". **Building never
starts in this session.**

The order matters because a redesign that skips it fails in a predictable way.
Visuals come first. Then labels get invented that the backend does not serve,
tabs get renamed every round, and where a screen's errors live gets settled
after the pixels. The only record ends up in a scratch folder.

## 0. Embodiment

Check the app's routes, its render modules, and `mockups/INDEX.md`.

- **Greenfield:** nothing ships yet, and the build ticket will run `build`.
- **Shipped:** the app already renders this surface or the shell it lives in.
  The build ticket will run `revise` against the running app. The canvas
  directions are throwaway wireframes. They carry no fidelity claim, and their
  code is never ported (ADR 48). Capture "before" renders of the current surface
  now, through the safe entrypoint the repo declares. Without one, ask the
  operator for captures. Never start an undeclared entrypoint.

## 1. Structure step (no pixels)

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

Fill in `Tokens`, `Components`, `Bans`, `Frames`, and `Allowed strings`.

- **Tokens** come from the running app's stylesheet: palette in both themes,
  type scale, spacing, and radius. Copy them from that file and cite its path,
  never transcribe them from memory. A greenfield app with no stylesheet commits
  to a small set here, and the build creates it.
- **Components:** one size per role. Give the button height, padding, and type
  once per role, and set `Button sizes:` to the number of distinct sizes.
- Set up the design system for the canvas as [tools.md](tools.md) describes.

## 3. Directions

Make **three genuinely different directions** on a Design canvas
([tools.md](tools.md)). Vary the concept and layout: information hierarchy,
layout metaphor, interaction model. Never vary only color. Draw each direction
at every frame in `Frames:`, phone and desktop at least. Draw the primary screen
in its typical state and in one hard state (empty or error).

Mark the render conventions `precheck.py` reads:

- `data-screen` on each screen root;
- `data-label` on served-data labels;
- `data-value` on served values;
- `data-primary` on the one primary action.

Use manufactured data only.

## 4. Prechecks (before the operator sees anything)

```sh
python3 <ui-craft-skill-directory>/scripts/precheck.py <render.html | dir> <lock doc>
```

The script checks six things:

- microcopy: sentences, rhetorical questions, and explanatory subtitles not in
  `Allowed strings`;
- provenance: every `data-label` is in `Served vocabulary`;
- one primary action per screen;
- fixed widths wider than the narrowest frame;
- distinct button sizes against `Button sizes:`;
- glossary: every short visible term is in the glossary or another lock list.

It reads static markup, so it cannot see computed layout. Follow it with the
browser pass in [tools.md](tools.md) for real overflow and rendered button
heights.

**A failing check means the operator does not see that render.** Fix the
render and rerun until every check passes. Paste the full output into the
round.

## 5. Cold critique

Dispatch a fresh, read-only subagent with a named model, as
[tools.md](tools.md) describes. Give it only the lock doc and the renders: no
transcript, no rationale. It reports violations of the lock, the
[design-rules.md](design-rules.md) bans and slop test, and a persona walk of the
primary task, using repo personas first.

Fix each confirmed finding, rerun the prechecks, and carry any rejected finding
to the operator with the reason it was rejected.

## 6. Operator review, at most three refinement rounds

Present the three directions. Give each a one-line bet, its cost, and the
critique's open findings, and recommend one.

After the operator picks a direction, refinement rounds begin:

1. Echo every comment and instruction received back to the operator as a
   numbered list before acting. Ask them to name anything missing.
2. Apply the changes. A change to a name, screen, state, or gesture amends the
   structure sections first.
3. Rerun the prechecks and the browser pass, then present the result.

Nothing already ruled reopens.

**After the third round, stop.** Report what is unresolved, then offer three
options: lock as it stands, amend the structure and start a new session, or end
here. Never run a fourth round on your own.

## 7. The "locked" gate

The operator saying **"locked"** is the only approval. Then, in one change:

1. Set `Status: locked <date> by <operator>` and fill `Approved screens` with
   each screen, frame, and canvas or artifact URL.
2. Update the surface's one line in `mockups/INDEX.md`.
3. File or update a **separate build ticket**. It names the lock doc path, the
   canvas URL or a reference bundle, and `build` or `revise`.
4. Commit the lock doc and INDEX line. The design session ends here.

## Lock doc format

Keep it to one page. `precheck.py` reads three headings: `Glossary`,
`Served vocabulary`, and `Allowed strings`. It also reads the `Frames:` and
`Button sizes:` lines. A bullet's text before ` — ` is the entry, matched
without regard to case.

```markdown
# <Surface> — design lock
Status: draft | locked <YYYY-MM-DD> by <operator>
Embodiment: greenfield (build) | shipped (revise)
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
- Button, primary — <height, padding, type>; one per screen
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
- <Screen> at <frame> — <URL>
## Amendments
- <YYYY-MM-DD> <operator>: <what changed>, "<their words>"
```
