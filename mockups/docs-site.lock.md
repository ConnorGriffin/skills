# Lock manifest — docs-site

Locked: 2026-08-26 by Claude Fable 5 (ui-craft `lock`, issue #198)
Mocks: `docs-site-index.html`, `docs-site-skill.html`, `docs-site-narrative.html`, `_theme.css`, `SCAFFOLD.md`
Supersedes: — (greenfield; this repo ships no application and no prior docs surface, so the predecessor inventory is skipped by the one-line greenfield rule in `lock.md` §9.3)

## Precedence

The mock wins for anything it states explicitly. There is no shipped design
system to defer to — this repo has no app and no stylesheet — so anything the
mock is silent on is the builder's call, made consistently across all three
templates and recorded in the fidelity ledger. `_theme.css` is the material
ground truth for tokens; once the site ships, its own stylesheet replaces it
and this manifest is archived.

## Views

Three page templates, one contract. There is no default view and no view
switcher: these are separate URLs, not modes of one screen.

## Terms

| # | Term | Kind | Evidence expected |
|---|------|------|-------------------|
| 1 | Zero JavaScript ships. No `<script>` tag, no inline handler, no `javascript:` href, on any page. | gate | grep across built output |
| 2 | Exactly one hand-written stylesheet, linked as `_theme.css` (renamed at build). Per-skill edge-isolation rules are generated into an inline `<style>` on the pages that carry an isolating map, and are the only other CSS. A page with no isolating map (the narrative template) carries no `<style>` at all. | gate | assertion: exactly one `<link rel=stylesheet>` per page; at most one `<style>`, containing only `.diagram:has(...)` rules |
| 3 | No external font, CDN, image, or fetched asset. Every `href`/`src` resolves inside the site. | gate | grep for `//`, `http`, `@import`, `url(` |
| 4 | Diagrams are build-time inline `<svg>` generated from real SKILL.md frontmatter — never a library, never a raster, never hand-drawn. | gate | assertion: `<svg class="diagram">` present, no chart library in output |
| 5 | Every diagram box is coloured by its skill's category, using `--cat`/`--cat-bg`, on every page. Colour is the only carrier of category meaning in the palette. | gate | assertion: each `.node` carries a `cat-*` class matching its skill's directory |
| 6 | Edges are directed: every edge path carries `marker-end` pointing at the referenced skill. | gate | assertion |
| 7 | Index hero is the full pack map: all 27 skills, all 87 reference edges, four layout columns labelled `workflows` / `drivers` / `tools` (tools split across two columns). Counts follow the source tree, not this number. | gate | assertion: `.node` count == skill count, `.edge` count == edge count |
| 8 | Edges rest at 16% opacity. Hovering or keyboard-focusing a box drops all other edges to 5% and lifts that skill's edges to 95% in its category colour. Pure CSS `:has()`; a `@supports not selector(:has(*))` fallback renders the map static at 20%. | eye | paired render, rest vs. hover |
| 9 | Every diagram box is keyboard reachable (`tabindex="0"`) and carries a `<title>` naming the skill and its category; every `<svg class="diagram">` has `role="img"` and a sentence-long `aria-label`. | gate | assertion |
| 10 | The page body never scrolls horizontally, at 375px, 768px, 1280px, or 1440px. Diagrams scroll inside their own `.diagram-scroll` box (`min-width: 620px`). | gate | browser-gate: `documentElement.scrollWidth <= innerWidth` at four widths |
| 11 | Prose sits at a 34rem measure (`.prose`) on every page, including the 68rem index. Lists, tables, and diagrams may use the full frame; a paragraph never does. | eye | render at 1280 |
| 12 | Body text is the serif stack; all UI furniture — nav, headings, labels, tags, captions, table headers, footer — is the sans stack. Code is the mono stack. No web fonts; system stacks only. | gate | computed-style assertion on one element of each class |
| 13 | Light and dark both ship, via `prefers-color-scheme` only. There is no theme toggle — adding one would need JavaScript and violate term 1. | gate | render both schemes |
| 14 | All body and UI text meets WCAG AA (4.5:1) against its own background in both schemes. Measured at lock: light `--ink-dim` 4.97:1, dark 4.89:1; category ink on its own box ≥5.14:1. | gate | contrast assertion over the token pairs |
| 15 | Index category board is asymmetric: a narrow left column carrying workflows and drivers stacked, and a wide right column where the tools list flows into two text columns. Collapses to one column below 52rem. A symmetric three-column board is banned — it strands ~1400px beside the 19-row tools list. | gate | computed `grid-template-columns` at 1280 and 375 |
| 16 | Each category section shows its name, its live count, and a one-sentence blurb, in that order, above the list. | eye | render |
| 17 | Every skill entry is its name plus the first sentence of its real SKILL.md `description`. No invented copy, no truncation with an ellipsis, no count badges. | gate | string diff against frontmatter |
| 18 | Skill page order is fixed: category tag, name, full description, meta list, focused map, then the rendered SKILL.md body under an `SKILL.md` heading. | eye | render |
| 19 | Skill page meta list carries exactly four rows, in order: Invoke, Requires, Bundled, Source. Requires is derived from what the skill directory actually contains, never asserted. | gate | assertion: four `<dt>`, labels verbatim |
| 20 | The skill page's own `<h1>` is the skill name; the rendered body's leading `#` heading is dropped so the title is not stated twice. | gate | assertion: one `<h1>` per page |
| 21 | Focused map is three bands: skills that reference this one on the left under `referenced by`, the skill itself centred, the skills it references on the right under `references`. Category colour still governs every box, including the centre. | eye | render |
| 22 | Narrative page is prose at reading measure with exactly one flow diagram, placed above the prose it explains. Flow boxes are coloured by the category of the skill that owns the step. | eye | render |
| 23 | The flow diagram wraps serpentine — left-to-right, then right-to-left — so it fits the frame without shrinking boxes below the index map's box size. | eye | render |
| 24 | Persistent chrome on all three templates: the same six-item nav above the masthead, and the same footer line below the content. The nav marks the current page with `aria-current="page"`. Nothing else persists; there is no sidebar, no breadcrumb, no search. | gate | assertion: nav items verbatim and in order on each page |
| 25 | The `.mockbar` strip does not ship. Neither does any `href="#"` placeholder — every link resolves to a real page or an external repo URL. | gate | grep built output |

## Fixture obligations

The content is the repository itself; there is no fixture to manufacture, and
nothing here is personal or sensitive. What the build must exercise:

- **The real graph, not a sample.** All 27 skills across all three categories.
  Terms 7, 8 and 15 are only provable at full scale — the hairball, the
  isolation payoff, and the tools-column imbalance all appeared at 27 nodes and
  were invisible at three.
- **A skill page for a skill with a rich body** — headings, a table, a bulleted
  list, a numbered list, and inline emphasis — or terms 18–20 prove nothing.
  `ui-craft` is the locked exemplar and carries all five (verified at lock: 1
  table, 3 lists, 1 ordered list, 3 emphases).
- **A skill page whose body has a fenced code block.** `ui-craft`'s does not,
  so the mock never exercised `<pre>`. The build must render one — `pr-body`
  and `cbm-onboard` have fenced blocks — and prove it does not force a
  horizontal page scroll at 375px (term 10).
- **A skill page for a leaf** — one with no inbound and no outbound edges
  (`cbm-onboard`, `openspec-adopt`) — so term 21's empty bands are designed,
  not discovered.
- **Both schemes and four widths** for terms 10, 13 and 14.

## Verbatim strings

Navigation, in order, on every page:
`Overview` · `Workflows` · `Drivers` · `Tools` · `The ticket flow` · `Source on GitHub`

Category names and blurbs:

- `workflows` — "Front doors. You name the situation; the workflow classifies it and routes to exactly one specialist skill — it does no work itself."
- `drivers` — "Lifecycles. A driver owns a piece of work from arrival to done, through named verbs and state it records outside the conversation."
- `tools` — "References and single passes. Load one for its vocabulary, its checklist, or one bounded job, then get on with the work."

Index lede:
"A portable skill pack for coding agents. Twenty-seven skills that turn a vague request into tracked work, that work into a reviewed pull request, and that pull request into merged history — with the decisions written down as they are made."

Diagram captions:

- index — "Every skill in the pack, and every skill it names. Hover or tab to a box to isolate that skill's references."
- skill page — "N skills name `<skill>`; it names M."
- narrative — "The common path. Boxes are coloured by the category of the skill that owns the step."

Focused-map band labels: `referenced by` · `references`
Skill-page meta labels: `Invoke` · `Requires` · `Bundled` · `Source`
Skill-page body heading: `SKILL.md`
Footer: "skills — Connor Griffin · Apache-2.0 · every page on this site is generated from SKILL.md frontmatter"

## Recorded deviations

1. **`drive-local-webapp` was not used for rendered evidence.** The bundled
   driver at `skills/tools/drive-local-webapp` has no `node_modules`, and
   standing it up means `npm ci` plus a Chromium download *inside the pack
   directory* — writes outside `mockups/`, which this task forbids, and the
   repo's own hazard list bars adding dependencies to the pack. Substituted: a
   `python3 -m http.server` over `mockups/` driven by the session's headless
   browser. Every state below was rendered and inspected, so the grounding rule
   ("inspect rendered output") is satisfied by a different harness, not waived.
   Screenshots were inspected in-session and not committed.

2. **No `_shell.js`.** `lock.md` §4 specifies an ES-module shell for capture
   loading and mock-bar state/theme toggles. The surface is locked at zero
   JavaScript (term 1), so a JS shell would give the mock affordances the build
   could never have — the exact class of mock/app divergence the scaffold rule
   exists to prevent. Theme is `prefers-color-scheme` only and was exercised by
   driving the browser's colour scheme instead of an in-page toggle.

3. **Lightest-weight variant round.** Three index concepts (atlas / column /
   ledger) were fanned out by one generator rather than three fresh subagents,
   rendered, and converged in one round; the two losing variants are deleted per
   §9.5. Justified by the surface being a disposable one-operator docs site.
   The concepts differed in layout metaphor and information hierarchy, not
   decoration, and the round changed the design: the ledger variant's objection
   to a static hairball produced term 8, and the column variant's reading
   measure produced term 11.

4. **No persona round against repo personas.** The repo has no
   `.claude/qa/personas/`. Two generic walkthroughs were run instead — an agent
   author looking for one skill's requirements, and a newcomer asking what the
   pack is for. The first stalled on the index at not knowing where to start,
   which produced term 16's blurbs and the orienting paragraph; the second
   stalled on the skill page at not knowing what a skill needs to run, which
   produced term 19's Requires row.

## Open question for the operator — not settled here

**Where do the edges come from?** Three answers are in play and they are not
the same graph:

- `docs/scope/docs-site.md` line 7 (settled decision): "relationship data …
  derived from SKILL.md frontmatter + README tables".
- The same file's risk contract, in an uncommitted working-tree edit: "stale or
  incomplete **hand-maintained** relationship edges are accepted (only endpoint
  existence is checked)".
- This mock: a full-text scan of each SKILL.md **body** for the names of other
  skills, which is what produced 27 nodes and 87 edges.

The mock's method is the densest of the three; frontmatter-only or
hand-maintained edge lists would both yield a far sparser map. That changes the
*counts* in terms 7 and 8 but not the terms themselves — term 7 already says
"counts follow the source tree, not this number", and term 8's isolation
behaviour is what makes a dense map readable and a sparse one lose nothing.

Per `ui-craft`'s no-arbitration rule the builder must not pick one privately.
Take the answer from the operator, then record it. If the answer is a sparse
graph, re-examine term 8 in `resettle` rather than dropping it silently: at a
dozen edges the isolation still helps, but the hairball argument that produced
it no longer applies.

## What the build still owes

The fidelity ledger — one row per term above, with its evidence — attached to
the implementation pull request, per `ui-craft` `build`.
