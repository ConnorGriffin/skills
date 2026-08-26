# Fidelity ledger — docs-site (#198)

Build-phase evidence for [`mockups/docs-site.lock.md`](../mockups/docs-site.lock.md),
produced per `ui-craft` `build`. One row per manifest term, all 27.

## Provenance

| Artifact | SHA |
|---|---|
| Branch / base commit | `codex/198-docs-site` @ `bee47c75f2fa330cbf0169fd2421fa3417ae01d2` |
| Ported from commits | `0d2cf18` (generated site), `bee47c7` (publish) |
| `mockups/docs-site.lock.md` | `a654855bc3d95b621c83e803394666cf2b770003` |
| `mockups/docs-site-index.html` | `0968f55787ad9d640df0208c78d283d629c604a7` |
| `mockups/docs-site-skill.html` | `bd80501a93789660016f5f0692c2140e230bb616` |
| `mockups/docs-site-narrative.html` | `d550f1cbc7b4effe5ec5453dc036a132cc0ed3d5` |
| `mockups/_theme.css` | `33debf586cac2e62119248304f19b43f0742b43d` |
| `site/build.py` (after this pass) | `03c33819dd4b3086637af5913edde34b8c07bb67` |
| `site/style.css` (after this pass) | `360570756094f9f705b2f091e6c45b754bf0be74` |
| `site/relationships.py` | `d6aaa44c44ed6c38f3ac56da3c0d0f45237b3e33` |

Rebuild: `python3 site/build.py --out _site`. Suite: `python3 -m unittest
tests.test_site_build` — **OK** after every change below.

## Grading caveat — read before trusting this table

`build.md` puts statuses in the hands of a verifier who did not author the port
and cannot see the builder's notes. That holds for most of this table: I did not
write the port (commits above), so grading it is verification.

It does **not** hold for terms **7, 18, 21, 23 and 14**, where I found the miss
*and wrote the fix*. Those rows are self-graded and are the weakest evidence
here. They are marked ✎ and want an independent eye.

## Evidence index

Paired renders, mock beside build, at `mockups/` (port 8850) and `_site/`
(port 8851). Captured with headless Chrome; **not committed** — `.gitignore`
excludes `*.png`, and `lock.md` §6 keeps screenshots out of the repo.

Path: `<scratchpad>/fidelity/` —
`{index,skill,narrative}-1280-{light,dark}-{MOCK,BUILD}.png`,
plus `index-{375-light,768-light,1440-light}-BUILD.png` and
`index-375-light-MOCK.png`. 16 files.

| Pair | Covers |
|---|---|
| `index-1280-{light,dark}` | terms 5–9, 11–16, 24 |
| `skill-1280-{light,dark}` | terms 18–21, 26, 27 |
| `narrative-1280-{light,dark}` | terms 22, 23 |
| `index-{375,768,1440}` | terms 10, 15 |

## Ledger

| # | Term | Status | Evidence |
|---|------|--------|----------|
| 1 | Zero JavaScript | met | Gate sweep: no `<script>`, `javascript:`, or `on*=` across all 31 pages |
| 2 | One hand-written stylesheet + generated isolation `<style>` | met | 1 `<link rel=stylesheet>` per page; ≤1 `<style>`, containing only `.diagram:has(…)` rules; narrative pages carry none |
| 3 | No fetched asset; chrome repo-only, body any origin | met | No `@import`/`src=`/off-origin `url(`; every chrome href → `github.com/ConnorGriffin/skills`; 32 off-repo body links pass through |
| 4 | Diagrams inline SVG from repo data | met | `<svg class="diagram">` on all 31 pages, no chart library; graph from `relationships.py` |
| 5 | Boxes coloured by category | met | Every `.node` carries a `cat-*` class matching its skill's directory |
| 6 | Edges directed | met | Every `.edge` path carries `marker-end` |
| 7 ✎ | Full map, four columns, tools split, counts follow `relationships.py` | met **after fix** | 27 nodes == `relationships.py` keys; 36 edges == `uses` total; all endpoints real skill dirs. **Was missed**: tools rendered as one 19-row column (viewBox 900×748). Fixed in `site/build.py` `diagram()`; now four columns at x=24/248/472/684, viewBox 900×424. Pair `index-1280-light` |
| 8 | Edges rest 16%, hover/focus isolates to 95% in category colour | met | All 27 per-skill lift rules present in the inline `<style>`; computed `.edge` opacity `0.16` at rest, `0.05` under hover; hovering `ticket` lifts its edges in driver orange (in-session render) |
| 9 | Boxes keyboard-reachable, titled; svg `role=img` + `aria-label` | met | Every `.node` has `tabindex="0"` and a `<title>`; every diagram has `role="img"` and a sentence `aria-label` |
| 10 | No horizontal page scroll at 375/768/1280/1440 | met | `documentElement.scrollWidth == innerWidth` at all four; diagram scrolls inside `.diagram-scroll` (true at 375, false at 1280) |
| 11 | Prose at 34rem measure | met | `.prose` computes 544px (= 34rem × 16) at 1280 and 1440 |
| 12 | Serif body, sans furniture, mono code | met | Computed: body `Charter`; h2/nav/figcaption `ui-sans-serif`; `code` mono |
| 13 | Light and dark, `prefers-color-scheme` only, no toggle | met | Both schemes render (pairs differ byte-wise); no toggle control exists (term 1 forbids it) |
| 14 ✎ | All text AA in both schemes | met **after fix** | Computed from built `style.css`: light `--ink-dim` 4.97:1, dark 4.89:1; category ink on its box ≥5.14:1. **Was missed**: `.glabel` had no `fill`, defaulting to black — unreadable on dark. Fixed in `site/style.css` (`fill:var(--ink-mid)`); now 7.86:1 light / 7.4:1 dark |
| 15 | Asymmetric category board, collapses below 52rem | met | `grid-template-columns` = `304px 700px` at 1280/1440, `1fr` at 768/375; tools `column-count` 2 → 1 |
| 16 | Category name, count, blurb, in that order | met | Rendered `workflows 2`, `drivers 6`, `tools 19`, each followed by its locked blurb |
| 17 | Skill entry = name + **first sentence** of the real description | **blocked** | `site/build.py` uses `description.split(".")[0]`, which cuts at the first period rather than the first sentence. `writing-for-agents` renders "…audits the loaded skill and CLAUDE." — truncated mid-phrase at `CLAUDE.md`. 1 of 27 wrong. Text logic, not CSS/SVG: **reported, not fixed** (see below) |
| 18 ✎ | Skill page order: tag, name, description, meta, map, body | met **after fix** | **Was missed**: tag rendered *after* the description. Fixed in `site/build.py` `chrome(tag=…)` — tag now inside the masthead before `<h1>`. Pair `skill-1280-light` |
| 19 | Meta = Invoke, Requires, Bundled, Source; Requires from `relationships.py` | met | Four `<dt>` in locked order; Requires text matches the `requirements` field for all 27 skills (0 mismatches); empty field renders empty |
| 20 | One `<h1>`, body's leading heading dropped | met | Exactly one `<h1>` on all 31 pages |
| 21 ✎ | Focused map: `referenced by` / self / `references` | met **after fix** | **Was missed**: bands were labelled `workflows`/`drivers`/`tools` at map coordinates — wrong text *and* misaligned, since either band mixes categories. Fixed in `site/build.py` `diagram()`; labels now `referenced by` / `references`. Pair `skill-1280-light` |
| 22 | Narrative: prose at measure, one flow diagram, above the prose | met | One `<figure>` precedes `.prose.body`; boxes carry category colours |
| 23 ✎ | Flow wraps serpentine | met **after fix** | **Was missed**: rows both ran left-to-right, so step 3→4 wrapped diagonally across the figure. Fixed in `site/build.py` `diagram()`; row 0 x=24/224/424, row 1 x=424/224. Pair `narrative-1280-light` |
| 24 | Persistent chrome: same six-item nav + footer, `aria-current` | met | Nav verbatim and in order on all 31 pages; footer with MIT provenance on all 31 |
| 25 | No mockbar, no `href="#"` placeholder | met | Zero `href="#"` across the built site; no `.mockbar` |
| 26 | Body link destinations; fragment split and re-attached | met | All 92 body links resolve: 51 blob (every path exists on disk), 7 cross-page skill links, 2 fragments, 32 off-repo passthrough. `../scope/SKILL.md#risk-contract` → `scope.html#risk-contract` |
| 27 | Deterministic GitHub-style heading slugs; fragments resolve | met | Every fragment resolves to an emitted heading id on its target page: 2 same-page, 3 cross-page. Slug rule matches on punctuation and duplicate cases |

**Counts: 26 met, 0 re-settle requested, 1 blocked.** Five of the 26 are ✎
self-graded because I authored their fix.

## Generator-logic gaps — reported, not fixed

Outside the visual/CSS/SVG remit I was given. None of these are CSS or SVG.

1. **Term 17 (blocking).** `site/build.py` line ~176:
   `s["description"].split(".")[0]` truncates at the first period, not the
   first sentence. `writing-for-agents` shows "…audits the loaded skill and
   CLAUDE." on the index. A first-sentence regex (`(.+?[.?!])(\s|$)`) fixes it;
   the lock mock already used one.
2. **Index masthead states the same thing twice.** The masthead subtitle is "A
   portable skill pack for coding agents." and the very next paragraph opens
   with that identical sentence. The locked mock has no subtitle — the lede
   carries it. Not a numbered term, but it is the first thing on the page.
3. **`<h1>` reads `Skills`, the pack is `skills`.** Lowercase everywhere else —
   the mock, the footer, the repo. Page titles render "Skills — skills".
4. **`Bundled` is hard-coded to `SKILL.md`.** `ui-craft` ships `reference/` (17
   files), `scripts/` (9) and `agents/` (1); the row claims only `SKILL.md`.
   Term 19 pins the row's presence and order, not its content, so this is not a
   term miss — but the row is currently stating something untrue.
5. **`Invoke` renders `ui-craft`, mock rendered `/ui-craft`.** The slash is how
   the skill is actually invoked. Not pinned by a term.
6. **Edge anchors ignore direction.** Every edge leaves the source's right side
   and enters the target's left, even when the target sits to the left, so
   backward edges cross their own boxes. The mock chose the side by relative
   position. Not a numbered term; visible on the narrative flow.

## Recorded deviations (carried forward)

1. **`drive-local-webapp` not used** — unchanged from the lock round: the
   bundled driver has no `node_modules`, and `npm ci` plus a Chromium download
   inside the pack would add a dependency the repo's hazards forbid. Substituted
   `python3 -m http.server` over `mockups/` and `_site/`, driven by the session
   browser for interaction and computed styles, and by headless Chrome
   (`--headless=new --screenshot`) for the committed-quality pairs. Rendered
   evidence was obtained, through a different harness.
2. **Screenshots not committed** — `.gitignore` excludes `*.png` and `lock.md`
   §6 keeps them out of the repo. They live in the session scratchpad; paths
   above.
3. **Dark captures use the system scheme, not a flag.** Headless Chrome honours
   `--blink-settings=preferredColorScheme=1` (light) but ignores `=2`; the
   machine's default is dark, so dark pairs are captured by omitting the flag.
   An earlier attempt with `--force-dark-mode` produced files byte-identical to
   the light ones — evidence of nothing — and those were deleted rather than
   attached.
