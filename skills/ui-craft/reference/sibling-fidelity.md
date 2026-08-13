# Sibling fidelity — one panel, one app

When a mock or new surface lives beside shipped surfaces, the bar is: moving
between the shipped surface and the new one must feel like switching panes on a
single dashboard. **Any element with a sibling in a shipped surface uses the
shipped values exactly — steal, never approximate.** A 3px chip-height drift, a
square corner where the app rounds, a mono axis label where the app uses the
default face: each one breaks the one-app illusion, and the operator sees it
even when the builder doesn't. Distilled from the #660 Verify round
(ciq-autotune, 2026-08-12), where every rule below was learned as a correction.

## Steal list (what "sibling" covers)

Not just tokens and colors. Every one of these bit in practice:

- **Geometry**: pane radius, paddings, gaps, row heights, full-bleed vs inset
  hairlines, chrome icon pixel sizes.
- **Alignment spines**: the shipped app aligns pane title, axis caption
  (`mg/dL`) and axis labels on the plot's own left edge (a `--*-grid-left`
  token shared by CSS and chart config). New panes join the spine, and the
  chart grid uses the same number.
- **Type**: rank (a pane title is caps-rank like every sibling pane, even when
  it "feels like" a heading), family (axis labels in the app's default face,
  not mono, when that is what the shipped chart does), line-height.
- **Chart furniture**: axis scale rules (the shipped fixed clinical axis —
  e.g. 40–300/60 — beats data-hugging bounds; comparable zoom across views is
  the point), threshold-band treatment (fill + labeled knock-out rules, ported
  mixes), tick visibility, legend position/scale/case.
- **Interaction idioms**: hover is chrome too. If the app has a docked-readout
  hover (crosshair only, numbers land in the pane header's swap line, no
  floating tooltip), the mock ports that behavior — `showContent:false`,
  `updateAxisPointer` → header paint, `globalout` clears — not a generic
  tooltip.

## Audit empirically, not by eyeball

Run the shipped app and the mock in the same headless browser and **diff
computed styles + bounding rects on shared selectors** (radius, padding, gap,
font-size/family/weight, letter-spacing, line-height, colors, rect). Eyeballs
miss 1–3px; the diff doesn't. Re-run the diff after edits — it is the fidelity
gate, not a one-off. Two reporting artifacts to ignore: `width`/`height`
computed-property mismatches caused by box-sizing differences when the rects
match, and 0×0 rects for app elements that exist but aren't laid out in the
probed tab (fall back to the app's source values for those).

**The diff's blind spot is canvas.** Chart text (axis labels, ticks, legend,
in-chart labels) is painted, not DOM — a computed-style diff cannot see it at
all. Audit chart typography and furniture at the **option level**: diff the
mock's chart config (family, sizes, tick visibility, positions) against the
shipped chart source or a live `getOption()` dump, as its own audit step.

## Token bridges lie — verify resolution, not names

A mock that bridges onto extracted app CSS via alias tokens
(`--ck-r: var(--wk-radius)`) can silently resolve to nothing or to a wrong
literal: the name may come from a retired lineage, or the real value may live
in a **scoped** block (the app's workstation sets `--ck-r: 8px` inside `.dw`;
the global `--wk-radius` is `0px`). Grep proving a name exists proves nothing.
Verify every bridge token by **computed value on the element that uses it**,
and port scoped token blocks as literals with a comment naming their source.

## No mock-global base styles

A `body { line-height / font-size }` in the mock leaks into chrome extracted
from the app and shifts its pixel metrics (chip heights, footer text). Chrome
inherits the app's own base; scope any interior typography to the surface's
own containers.

## Findings close by edit, not by note

In a persona/critique sweep against a mock, a confirmed finding is closed by
an edited file and a fresh render — finding → edit → screenshot, one at a
time. Noting findings for later is the failure mode the sweep exists to kill.

## Concrete traps (chart library)

- ECharts 5.5 legend: custom `path://` icons collapse the legend layout (all
  items stack at 0,0, clipped). Replicate line marks via inheritance instead:
  plain string `data`, `itemStyle: { opacity: 0 }` to hide the symbol dot,
  `lineStyle: { width: 'auto', type: 'inherit' }`.
- ECharts value-axis charts whose x range spans 0: default `onZero` pins the
  y-axis (and its name) to x=0, not the plot edge — set
  `axisLine: { onZero: false }`.
- A threshold band (`markArea`) covering the whole visible axis is a uniform
  wash that reads as nothing; a fixed axis (above) keeps its edges in frame.
- Aggregate bins keyed by bin start: extend the final segment to the bin's
  end, or the series dies short of the axis edge with a cliff.
