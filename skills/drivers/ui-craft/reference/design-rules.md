# Design rules

The shared craft discipline for every mode. Merged from `interface-craft` and
`impeccable`'s general rules.

## Operating contract

- Preserve product truth, real content, existing behavior, and accessibility.
- Use the project's established design system when it is sound. Extend it with
  explicit tokens; never introduce a competing visual language accidentally.
- Make one strong, defensible visual direction; don't blend fashionable
  aesthetics until they become anonymous.
- References are evidence, not collage: borrow a principle, never a brand's
  surface treatment wholesale.
- Match density to the job — marketing can breathe; operational tools earn
  every pixel with faster comprehension or action.
- Don't add a dependency just to make a UI feel designed.

## The design brief (before code)

```text
Job: what the person must understand or do here.
Audience and setting: who uses it, when, under what pressure or attention.
Direction: a precise visual world in one sentence.
Signature move: one visible typographic, structural, material, or interaction choice.
Density: sparse / balanced / dense, and why.
Constraints: existing tokens, required content, a11y, responsiveness, performance.
Anti-references: motifs this surface must avoid.
```

If the brief is weak, make a provisional choice and label it. Never hide a
generic default behind "clean", "modern", or "premium".

## System before components

Every repeated visual value traces to a limited token system.

- **Type:** roles for display, body, labels, data; deliberate scale; optical
  line-height; tabular figures for aligned numerics; prose at 65–75ch;
  sentence case unless uppercase carries meaning. Don't pair similar-but-not-
  identical fonts — pair on a contrast axis or use one family in weights.
  Display ceiling: clamp() max ≤ 6rem; letter-spacing floor ≥ -0.04em.
  `text-wrap: balance` on h1–h3, `pretty` on long prose.
- **Color:** pick a strategy first — restrained / committed / full palette /
  drenched. One dominant accent role unless the data model needs more. Use
  OKLCH where the stack permits. Verify contrast: body ≥4.5:1 (placeholders
  too), large text ≥3:1. Gray text on a colored background looks washed out —
  use a darker shade of the background's hue or a transparency of the text
  color. Dark vs light is never a default: write one sentence of physical
  scene (who, where, ambient light, mood) and let it force the answer.
  Beware the warm-neutral cream/sand/beige body default — "warmth" belongs in
  accent, typography, and imagery, not reflexively in the body background.
- **Space and geometry:** spacing rhythm, container behavior, corner logic,
  elevation, and a semantic z-index scale (dropdown → sticky → modal-backdrop
  → modal → toast → tooltip; never 999). Vary rhythm intentionally.
- **Material:** surfaces, borders, shadows, texture from the direction — a
  blur or gradient must communicate hierarchy, atmosphere, or interaction.
- **Motion:** standard durations, easing, transform origins, reduced-motion
  fallback — decided before effects are added.

## Explore before committing

For a whole page or major surface: three conceptually different directions
(information hierarchy, layout metaphor, interaction model, density — not
colors). Name each for its idea; assess information shape, spatial model,
signature move, and risk. Ground prototypes in the shipping theme and real
data; compare rendered screenshots; select one and record it — don't blend.

For an existing surface, don't redesign blindly: capture what users rely on,
identify visual debt, and fix the highest-leverage constraints first —
hierarchy/typography, then color/contrast, then layout/rhythm, then
interaction feedback and missing states, then clichés. Don't migrate
framework or CSS strategy unless that is the task.

## Build

- Semantic HTML and native controls where they fit; DOM and CSS simple enough
  to survive responsive and state changes.
- Layout expresses relationships — not a bordered, shadowed card around every
  grouping. Grid for 2D, flex for 1D (`flex-wrap` before Grid;
  `repeat(auto-fit, minmax(280px, 1fr))` for breakpointless grids). Test
  optical alignment.
- Real product language and credible content — no lorem ipsum, fabricated
  metrics, or generic AI copy.
- Loading, empty, error, offline, success, disabled, overflow, and
  permission states are first-class screens with a next action and a way back.
- Keyboard focus, target size, logical tab order, announcements for state
  changes; skip link where structure warrants.
- Design the narrow layout; don't merely stack the desktop one. Test long
  labels, large text, both themes. No horizontal scroll; layers that must
  escape a scrolling container use popover/`<dialog>`/portal/fixed —
  `position: absolute` inside `overflow: hidden|auto` gets clipped.

## Motion

Four questions before any animation: How often is it seen (high-frequency and
keyboard-driven actions get little or none)? What is its job (continuity,
feedback, state, explanation, rare delight — never "feels expensive")? What
movement fits (enter fast-then-settle, exit accelerates away, on-screen uses
a balanced curve; ease-out-quart/quint/expo, no bounce)? Smallest effective
duration (press 100–160ms, tooltip 125–200ms, dropdown 150–250ms,
modal/drawer 200–500ms)?

Animate transforms and opacity over layout properties. Reduced motion is not
optional — every animation needs a `prefers-reduced-motion` alternative that
keeps content and state reachable. Reveal animations enhance an
already-visible default; never gate visibility on a class-triggered
transition (hidden tabs and headless renderers ship the section blank).
Stagger within one list is legitimate; one identical entrance on every
section is the tell.

## Absolute bans

Match-and-refuse — about to write one, rewrite the element structurally:

- **Side-stripe borders** (`border-left/right` >1px as a colored accent).
  Full borders, background tints, leading numbers/icons, or nothing.
- **Gradient text** (`background-clip: text` + gradient). Solid color;
  emphasis via weight or size.
- **Glassmorphism as default.** Rare and purposeful, or nothing.
- **The hero-metric template** (big number, small label, gradient accent).
- **Identical card grids** (icon + heading + text, repeated).
- **Nested cards** and repeated faint borders.
- **Tiny uppercase tracked eyebrow above every section**, and its deeper
  variant, **numbered section markers (01/02/03) as default scaffolding** —
  numbers earn their place only when the order carries real information.
- **A left sidebar because the surface is called a dashboard**; default icon
  metaphors, pill badges, avatar circles, sun/moon toggles by reflex.
- **Text that overflows its container** — test heading copy at every
  breakpoint; the viewport is part of the design.

Don't replace a cliché with arbitrary novelty; the alternative must make the
hierarchy or task better.

## The slop test

If someone could look at the surface and say "AI made that" without doubt, it
failed. Category-reflex check at two altitudes: (1) if the theme + palette
are guessable from the category alone, rework the scene sentence and color
strategy; (2) if the aesthetic family is guessable from
category-plus-anti-references ("fintech that's not navy-and-gold →
terminal-native dark"), that's the trap one tier deeper — rework until
neither answer is obvious.

## Critique in layers

Review the rendered interface, not only source. In order: comprehension →
product fit → composition → craft → interaction → resilience. Findings as
exact before/after with a reason. Prioritize by user impact — no cosmetic
punch list while an empty state, unclear action, or inaccessible contrast
remains.

## Report style

Report only: chosen direction, material changes, evidence checked, known
limitations. No congratulating the work, no generic design theory.
