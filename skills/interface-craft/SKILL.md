---
name: interface-craft
description: Design or redesign distinctive, production-quality web and product interfaces. Use for UI work that needs a grounded visual direction, non-generic layouts, refined interaction and motion, design-system discipline, critique, or a final visual and accessibility quality pass.
---

# Interface Craft

Build interfaces with an intentional point of view. Do not decorate a default
component layout. Make the interface clearer, more useful, and unmistakably
specific to the product.

## Operating contract

- Preserve product truth, real content, existing behavior, and accessibility.
- Use the project's established design system when it is sound. Extend it with
  explicit tokens; do not introduce a competing visual language accidentally.
- Make one strong, defensible visual direction. Do not combine fashionable
  aesthetics until they become anonymous.
- Treat references as evidence, not as a collage. Borrow a principle, never a
  brand's surface treatment wholesale.
- Match visual density to the job. Marketing can breathe; operational tools
  should earn every pixel with faster comprehension or action.
- Do not add a dependency just to make a UI feel designed.

## Route the work

Start by choosing one path. Do not code before completing its required first
step.

| Situation | First step | Finish condition |
| --- | --- | --- |
| New surface | Write a design brief and compare directions | A locked visual spec exists |
| Existing bland surface | Audit the live UI before changing it | Improvements retain behavior and product truth |
| Small component | Inspect its parent flow, states, and tokens | Component improves the whole flow, not only itself |
| Motion request | Make an animation decision before implementation | Motion has purpose, timing, and reduced-motion behavior |
| Final pass | Run the quality gate | Screenshots and checks show no material regressions |

## 1. Ground the work

Read the smallest useful set of real materials before proposing visuals:

1. Product purpose, audience, primary job, and current user language.
2. Existing `PRODUCT.md`, `DESIGN.md`, design tokens, typography, theme,
   representative screen, and component primitives.
3. Real data shape and all relevant states: typical, dense, empty, loading,
   error, permission-limited, and mobile when applicable.
4. Three visual references or named qualities, plus one anti-reference. If no
   references exist, derive them from the product's physical world, artifacts,
   and audience instead of the software category.

State these decisions in a compact design brief before code:

```text
Job: what the person must understand or do here.
Audience and setting: who uses it, when, and under what pressure or attention.
Direction: a precise visual world in one sentence.
Signature move: one visible typographic, structural, material, or interaction choice.
Density: sparse / balanced / dense, and why.
Constraints: existing tokens, required content, a11y, responsiveness, performance.
Anti-references: motifs this surface must avoid.
```

If the brief is weak, make a provisional choice and label it. Do not hide a
generic default behind words such as "clean," "modern," or "premium."

## 2. Create a system before components

Choose a limited token system. Every repeated visual value must trace back to it.

- **Type:** Choose roles for display, body, labels, and data. Use a deliberate
  scale, optical line-height, and tabular figures for aligned numeric data.
  Keep prose to roughly 65–75ch. Use sentence case unless uppercase carries
  real meaning.
- **Color:** Choose a color strategy: restrained, committed, full palette, or
  drenched. Use one dominant accent role unless the data model requires more.
  Use perceptual color values when the stack permits. Verify contrast; normal
  body text needs 4.5:1.
- **Space and geometry:** Define a spacing rhythm, container behavior, corner
  logic, elevation, and z-index scale. Vary rhythm intentionally; uniform
  padding everywhere is not refinement.
- **Material:** Pick surfaces, borders, shadows, texture, and image treatment
  from the direction. A blur, gradient, grain, or shadow must communicate
  hierarchy, atmosphere, or interaction—not merely announce "modern UI."
- **Motion:** Define standard durations, easing, transform origins, and a
  reduced-motion fallback before adding effects.

Avoid the category reflex: do not make a product dashboard dark just because it
is a tool, or a marketing site pale beige just because it is "warm." Derive the
choice from the audience and scene.

## 3. Explore before committing

For a whole page or major surface, produce three conceptually different
directions. Change the information hierarchy, layout metaphor, interaction
model, or density—not only colors and rounded corners.

Give each direction an idea-based name and assess it against the brief:

- **Information shape:** What becomes immediate? What recedes?
- **Spatial model:** Editorial flow, command surface, timeline, canvas,
  catalogue, split workspace, narrative, or another model native to the job.
- **Signature move:** The one memorable choice that stays useful.
- **Risk:** What could confuse, slow, exclude, or over-stylize the result?

Ground prototypes in the shipping theme, components, and real data where
possible. For data-heavy UI, use the same chart library and data field names as
the product. Compare rendered screenshots at the relevant states. Select one
direction, record it as the visual spec, then implement it rather than blending
the three proposals.

For an existing project, do not redesign blindly. First capture what users rely
on, identify visual debt, and change the highest-leverage constraints first:

1. hierarchy and typography,
2. color and contrast,
3. layout and spatial rhythm,
4. interaction feedback and missing states,
5. component clichés and ornament.

Keep a redesign focused and reviewable. Do not migrate framework, CSS strategy,
or component library unless that is the actual task.

## 4. Build with visual intent

Use semantic HTML and native controls where they fit. Keep the DOM and CSS
simple enough to preserve the direction under responsive and state changes.

### Structure and hierarchy

- Make the primary task and next action obvious without relying on decoration.
- Use layout to express relationships. Do not wrap every conceptual grouping in
  a bordered, shadowed card.
- Prefer meaningful asymmetry, mixed scale, or a strong reading order when the
  content supports it. Do not force novelty into dense operational UI.
- Use a grid for two-dimensional composition and flex for one-dimensional
  alignment. Prevent accidental blank cells and arbitrary fixed heights.
- Test optical alignment. Mathematical centering can look wrong by a pixel or
  two.

### Refuse generic scaffolding

Rewrite these unless the content genuinely requires them:

- a hero metric with tiny label and decorative gradient;
- three identical icon-title-copy cards;
- nested cards and repeated faint borders;
- numbered or uppercase eyebrow labels above every section;
- purple-blue gradients, default glass panels, or unmotivated glow;
- a left sidebar simply because the surface is called a dashboard;
- default icon metaphors, pill badges, avatar circles, or a sun/moon toggle;
- symmetrical marketing sections assembled from the same alternating pattern.

Do not replace one cliché with an arbitrary novelty. The alternative must make
the hierarchy or task better.

### Content and states

- Use real product language and credible content. Never hide incomplete design
  behind lorem ipsum, fabricated metrics, or generic AI copy.
- Design loading, empty, error, offline, success, disabled, overflow, and
  permission states as first-class screens.
- Use clear labels and direct errors. Give the user a next action and a way
  back from dead ends.
- Ensure keyboard focus, target size, logical tab order, and announcements for
  state changes. Include a skip link where page structure warrants it.

### Responsive behavior

- Design the narrow layout, do not merely stack the desktop layout.
- Test long labels, large text settings, keyboard navigation, low-motion mode,
  and both themes if supported.
- Prevent horizontal scroll and clipped overlays. Use popover, dialog, portal,
  or fixed positioning when a layer must escape a scrolling container.

## 5. Add motion only where it helps

Ask four questions before implementing animation:

1. How often will people see it? Remove or nearly remove animation from
   high-frequency and keyboard-driven actions.
2. What is its job: spatial continuity, feedback, state indication,
   explanation, or rare delight? Do not animate just to make a screen feel
   expensive.
3. What movement fits it? Entering UI generally accelerates quickly then
   settles; exiting UI can accelerate away; on-screen movement uses a balanced
   curve. Avoid slow starts for responsive controls.
4. What is the smallest effective duration? Typical ranges: press 100–160ms,
   tooltip/popover 125–200ms, select/dropdown 150–250ms, modal/drawer 200–500ms.

Animate transforms and opacity in preference to layout properties. Give buttons
clear hover and pressed feedback; make popovers originate from their trigger;
preserve perceived continuity when elements enter or leave. Use a reduced-motion
alternative that retains access to all content and state changes. Do not block
initial rendering behind a reveal animation.

## 6. Critique in layers

Review the rendered interface, not only source code. Diagnose in this order:

1. **Comprehension:** Can a first-time user identify purpose, current state,
   hierarchy, and next action?
2. **Product fit:** Does the visual direction belong to this product and its
   audience rather than its software category?
3. **Composition:** Are reading order, density, containers, rhythm, scale, and
   alignment intentional?
4. **Craft:** Are contrast, type, surfaces, icons, images, and states coherent?
5. **Interaction:** Does feedback arrive promptly and motion make state changes
   easier to understand?
6. **Resilience:** Does it work with real data, every important state, keyboard,
   touch, responsive widths, and reduced motion?

For code-review findings, use exact before/after changes with a reason:

| Before | After | Why |
| --- | --- | --- |
| `transition: all 300ms` | `transition: transform 160ms var(--ease-out)` | Avoid unintended animated properties and sharpen feedback. |

Prioritize by user impact. Do not produce a long cosmetic punch list while an
empty state, unclear action, or inaccessible contrast remains unresolved.

## 7. Ship only after the quality gate

Before declaring UI work complete:

- Confirm the implementation matches the selected visual direction and uses
  the intended tokens.
- Compare screenshots with the locked spec at the states that matter.
- Check normal and large-text contrast, keyboard focus, semantic landmarks,
  target sizes, error messaging, and reduced-motion behavior.
- Check loading, empty, error, dense, and narrow-width states using real or
  representative data.
- Verify no horizontal overflow, clipped layer, unreadable control, dead
  action, missing import, or console error.
- Remove temporary mockup controls, fake data, and unused variants. Preserve
  the selected spec and record why it won.

Report only: chosen direction, material changes, evidence checked, and any
known limitation. Do not congratulate the work or explain generic design theory.
