# Product register

When design SERVES the product: app UIs, admin dashboards, settings panels, data tables, tools, authenticated surfaces, anything where the user is in a task.

## The product slop test

Not "would someone say AI made this." Familiarity is often a feature here. The test is: would a user fluent in the category's best tools (Linear, Figma, Notion, Raycast, Stripe come to mind) sit down and trust this interface, or pause at every subtly-off component?

Product UI's failure mode isn't flatness, it's strangeness without purpose: over-decorated buttons, mismatched form controls, gratuitous motion, display fonts where labels should be, invented affordances for standard tasks. The bar is earned familiarity. The tool should disappear into the task.

## Typography

- **One family is often right.** Product UIs don't need display/body pairing. A well-tuned sans carries headings, buttons, labels, body, data.
- **Fixed rem scale, not fluid.** Clamp-sized headings don't serve product UI. Users view at consistent DPI, and a fluid h1 that shrinks in a sidebar looks worse, not better.
- **Tighter scale ratio.** 1.125–1.2 between steps is typical. More type elements here than on brand surfaces; exaggerated contrast creates noise.
- **Line length still applies for prose** (65–75ch). Data and compact UI can run denser; tables at 120ch+ are fine.

## Color

Product defaults to Restrained. A single surface can earn Committed (a dashboard where one category color carries a report, an onboarding flow with a drenched welcome screen), but Restrained is the floor.

- State-rich semantic vocabulary: hover, focus, active, disabled, selected, loading, error, warning, success, info. Standardize these.
- Accent color used for primary actions, current selection, and state indicators only, not decoration.
- A second neutral layer for sidebars, toolbars, and panels (slightly cooler or warmer than the content surface).

## Layout

- Responsive behavior is structural (collapse sidebar, responsive table, breakpoint-driven columns), not fluid typography.

## Components

Every interactive component has: default, hover, focus, active, disabled, loading, error. Don't ship with half of these.

- Skeleton states for loading, not spinners in the middle of content.
- Empty states that teach the interface, not "nothing here."
- Consistent affordances across the surface. Same button shape. Same form-control vocabulary. Same icon style.

## Motion

- 150–250 ms on most transitions. Users are in flow; don't make them wait for choreography.
- Motion conveys state, not decoration. State change, feedback, loading, reveal: nothing else.
- No orchestrated page-load sequences. Product loads into a task; users don't want to watch it load.

## Platform conventions

Apple's Human Interface Guidelines (and Material Design where it differs) are
the reference for touch-first product UI, a web app included. Borrow their
principles, never their visuals: a web app that imitates iOS chrome, with a
fake status bar or iOS-styled controls on a desktop browser, reads as a copy.

- **Content first, chrome recedes.** Hierarchy comes from type, weight and
  position, not boxes and fills. One dominant element per screen.
- **Touch targets at least 44 × 44 px** (Material: 48 dp), including icon
  buttons, rows and tab items, even when the glyph is smaller.
- **Top-level navigation is a tab bar of three to five sections** on a phone,
  persistent on every screen, with the same items in a sidebar or rail on wide
  layouts. Tabs navigate; they never trigger actions. Each tab keeps its own
  scroll and drill-down state.
- **Adapt to the width class; don't stretch.** Compact width stacks; regular
  width shows list and detail side by side. Respect safe areas and keep one
  side margin per width class.
- **Modality is for a short, focused task** with an obvious way out. A sheet
  carries one task, at most one primary action, and a cancel or swipe-down.
  Prefer non-modal paths; never chain sheets.
- **Undo beats confirmation** for anything reversible. Reserve a confirmation
  for what can't be undone, and name the consequence in its button.
- **Every gesture has a visible equivalent.** A swipe action is also a button
  or a menu item, and no gesture overrides a system one (edge swipe back,
  pull to refresh, the home indicator).
- **Pick the standard control for the job.** A segmented control for two to
  five mutually exclusive views of the same content; a switch for a setting
  that applies immediately; a list row with a chevron for navigation; a picker
  for a bounded value.
- **Data entry asks for the least.** Bring up the right keyboard (numeric for
  amounts), default to the likely value (now, the last used), size a field to
  its content, and validate inline rather than on submit.
- **Feedback is immediate.** Every touch shows a pressed state at once; work
  that takes longer than a moment shows progress in place.
- **Respect the reader's settings.** Text scales with the user's size setting
  without clipping, nothing reads below 11 px, and reduced motion and increased
  contrast are honoured.
- **Colour is sparse and means one thing.** One accent marks what can be
  pressed or is selected; a status colour never stands alone without a label,
  glyph or position.

## Product bans (on top of the shared absolute bans)

- Decorative motion that doesn't convey state.
- Inconsistent component vocabulary across screens. If the "save" button looks different in two places, one is wrong.
- Display fonts in UI labels, buttons, data.
- Reinventing standard affordances for flavor (custom scrollbars, weird form controls, non-standard modals).
- Heavy color or full-saturation accents on inactive states.
- Modal as first thought. Modals are usually laziness. Exhaust inline / progressive alternatives first.

## Product permissions

Product can afford things brand surfaces can't.

- System fonts and familiar sans defaults (Inter, SF Pro, system-ui stacks).
- Standard navigation patterns: top bar + side nav, breadcrumbs, tabs, command palettes.
- Density. Tables with many rows, panels with many labels, dense information when users need it.
- Consistency over surprise. The same visual vocabulary screen to screen is a virtue; delight is saved for moments, not pages.
