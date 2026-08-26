# Fidelity ledger — docs-site (#198)

Build-phase evidence for [`mockups/docs-site.lock.md`](../mockups/docs-site.lock.md),
produced per `ui-craft` `build`. One row per manifest term, all 27.

## Provenance

| Artifact | SHA |
|---|---|
| Branch / base commit | `codex/198-docs-site` @ `30ea8d8` |
| Ported from commits | `0d2cf18` (generated site), `bee47c7` (publish), `e97763c` + `4f6c243` (review fixes), `e3abbbb` (heading/emphasis/edge fixes), `30ea8d8` (code-span, narrative-style, output-guard hardening) |
| `mockups/docs-site.lock.md` | `a654855bc3d95b621c83e803394666cf2b770003` |
| `mockups/docs-site-index.html` | `0968f55787ad9d640df0208c78d283d629c604a7` |
| `mockups/docs-site-skill.html` | `bd80501a93789660016f5f0692c2140e230bb616` |
| `mockups/docs-site-narrative.html` | `d550f1cbc7b4effe5ec5453dc036a132cc0ed3d5` |
| `mockups/_theme.css` | `33debf586cac2e62119248304f19b43f0742b43d` |
| `site/build.py` | `6966f07f39ac53da2d1cc18db8a4ff2e6653b55c` |
| `site/style.css` (unchanged since `3c18680`) | `360570756094f9f705b2f091e6c45b754bf0be74` |
| `site/relationships.py` | `d6aaa44c44ed6c38f3ac56da3c0d0f45237b3e33` |
| `site/narratives/ticket-flow.md` | `465630cedb9833178598f7f2067b8e8882d9f96d` |
| `tests/test_site_build.py` | `74a086ed103eb337bc3fbec718baae47a5fb9d5a` |

Rebuild: `python3 site/build.py --out _site`. Since `30ea8d8` the output
directory is cleared only when it carries the `.site-build-stamp` marker, so the
build refuses to `rmtree` a directory it did not create — pointing `--out` at a
populated foreign path is now an error rather than data loss. Suite:
`python3 -m unittest tests.test_site_build` — **OK** (5 tests).

**This table describes the build at `30ea8d8`.** Every row was re-run against
this output, not carried over. All 27 terms are met; nothing is blocked and no
re-settle is outstanding.

The suite now pins every regression this ledger caught, so none can silently
return:

| Test | Pins |
|---|---|
| `test_builds_real_pack_with_resolved_internal_links` | terms 26, 27 — link and anchor resolution |
| `test_leading_blank_h1_is_dropped_without_dropping_a_body_without_one` | term 20, in both directions (no duplicate `<h1>`, no emptied body) |
| `test_duplicate_headings_receive_suffixes` | term 27's `-1`/`-2` dedupe branch |
| `test_underscore_emphasis_and_directional_edge_anchors` | emphasis rendering and direction-aware edge routing |
| `test_refuses_to_clear_foreign_output` | the `.site-build-stamp` output guard |

## Grading caveat — read before trusting this table

`build.md` puts statuses in the hands of a verifier who did not author the port
and cannot see the builder's notes. That holds for most of this table: I did not
write the port (commits above), so grading it is verification.

It does **not** hold for terms **7, 18, 21, 23 and 14**, where I found the miss
*and wrote the fix*. Those rows are self-graded and are the weakest evidence
here. They are marked ✎ and want an independent eye.

## Evidence index

Paired renders, mock beside build. **Deliberately not committed and not paths:**
`.gitignore` excludes `*.png`, `lock.md` §6 keeps screenshots out of the repo,
and CONTRIBUTING forbids machine-specific paths in the tree. The set is
described by its capture protocol and filenames so any reviewer can regenerate
it byte-for-byte.

**Capture protocol.** Serve both trees over `python3 -m http.server` — one on
`mockups/`, one on the `--out` directory of `site/build.py`. Drive headless
Chrome:

```sh
chrome --headless=new --disable-gpu --hide-scrollbars \
       --virtual-time-budget=2500 --window-size=<W>,<H> \
       --screenshot=<name>.png <url>
```

Light renders add `--blink-settings=preferredColorScheme=1`. Dark renders omit
it and rely on the host's dark default — Chrome honours the light value but
ignores `=2`, and `--force-dark-mode` silently produces a file identical to the
light one, which is evidence of nothing. Confirm the two differ before trusting
a dark capture.

**The set — 17 files.** BUILD captures were all re-taken at `30ea8d8`; the
edge-routing, heading, emphasis and narrative-style changes touch every page
type. MOCK captures are unchanged since the lock.

| File | Viewport | Covers |
|---|---|---|
| `index-1280-{light,dark}-BUILD.png` | 1280×1450 | 4–9, 11–17, 24, 25 |
| `index-375-light-BUILD.png` | 375×1700 | 10, 15 |
| `index-768-light-BUILD.png` | 768×1500 | 10, 15 |
| `index-1440-light-BUILD.png` | 1440×1000 | 10, 15 |
| `skill-1280-{light,dark}-BUILD.png` | 1280×1150 | 18–21, 26, 27; single `<h1>`, italic emphasis, intact code spans |
| `skill-wfa-1280-light-BUILD.png` | 1280×1300 | 17–21; full body, and term 21's empty-band leaf case |
| `narrative-1280-{light,dark}-BUILD.png` | 1280×950 | 22, 23; direction-aware edges, zero inline `<style>` |
| `index-{1280-light,1280-dark,375-light}-MOCK.png` | as above | lock-side halves |
| `skill-1280-{light,dark}-MOCK.png` | 1280×1150 | lock-side halves |
| `narrative-1280-{light,dark}-MOCK.png` | 1280×950 | lock-side halves |

## Ledger

| # | Term | Status | Evidence |
|---|------|--------|----------|
| 1 | Zero JavaScript | met | Gate sweep: no `<script>`, `javascript:`, or `on*=` across all 31 pages |
| 2 | One hand-written stylesheet + generated isolation `<style>` | met | One `<link rel=stylesheet>` on every page. Inline `<style>`, re-verified at `30ea8d8`: index 1 block (4174 B, all 27 skills); each skill page 1 block (142–150 B — only the nodes in its own focus diagram); **each narrative page 0 blocks**, which is what lock term 2 states verbatim. Every block contains only `.diagram` isolation rules |
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
| 17 | Skill entry = name + **first sentence** of the real description | met | **Was blocked; fixed in `e97763c`.** Re-verified against this build: 0 of 27 descriptions differ from the first-sentence rule. `writing-for-agents` now renders in full, through "…audits the loaded skill and CLAUDE.md/AGENTS.md estate." — the `CLAUDE.md` truncation is gone |
| 18 ✎ | Skill page order: tag, name, description, meta, map, body | met **after fix** | **Was missed**: tag rendered *after* the description. Fixed in `site/build.py` `chrome(tag=…)` — tag now inside the masthead before `<h1>`. Pair `skill-1280-light` |
| 19 | Meta = Invoke, Requires, Bundled, Source; Requires from `relationships.py` | met | Four `<dt>` in locked order; Requires text matches the `requirements` field for all 27 skills (0 mismatches); empty field renders empty |
| 20 | One `<h1>`, body's leading heading dropped | met | **Was blocked at `4f6c243`; fixed in `e3abbbb`.** Re-verified: 0 of 31 pages carry a second `<h1>`, and 0 skill bodies are empty — the two constraints that previously traded off now hold together, and a test pins both. Pair `skill-1280-light-BUILD` |
| 21 ✎ | Focused map: `referenced by` / self / `references` | met **after fix** | **Was missed**: bands were labelled `workflows`/`drivers`/`tools` at map coordinates — wrong text *and* misaligned, since either band mixes categories. Fixed in `site/build.py` `diagram()`; labels now `referenced by` / `references`. Pair `skill-1280-light` |
| 22 | Narrative: prose at measure, one flow diagram, above the prose | met | One `<figure>` precedes `.prose.body`; boxes carry category colours |
| 23 ✎ | Flow wraps serpentine | met **after fix** | **Was missed**: rows both ran left-to-right, so step 3→4 wrapped diagonally across the figure. Fixed in `site/build.py` `diagram()`; row 0 x=24/224/424, row 1 x=424/224. Pair `narrative-1280-light` |
| 24 | Persistent chrome: same six-item nav + footer, `aria-current` | met | Nav verbatim and in order on all 31 pages; footer with MIT provenance on all 31 |
| 25 | No mockbar, no `href="#"` placeholder | met | Zero `href="#"` across the built site; no `.mockbar` |
| 26 | Body link destinations; fragment split and re-attached | met | **95 body links, all resolving** — 54 blob (every path exists on disk), 32 off-repo passthrough, 7 cross-page skill links, 2 same-page fragments. By page: 92 on the 27 skill pages, 3 on the 3 narrative pages. `../scope/SKILL.md#risk-contract` → `scope.html#risk-contract` |
| 27 | Deterministic GitHub-style heading slugs; fragments resolve | met | Every fragment resolves to an emitted heading id on its target page: 2 same-page, 3 cross-page. Slug rule matches on punctuation and duplicate cases |

**Counts: 27 met, 0 re-settle requested, 0 blocked.**

Movement since the previous ledger: term 20 blocked → met. Nothing else changed
verdict. Five of the 27 met rows are ✎ self-graded because I authored their fix
(terms 7, 14, 18, 21, 23); all five were re-verified against this build, and
they remain the weakest evidence in the table.

Mechanical re-verification at `30ea8d8`, across all 31 pages: no `<script>` or
inline handler; one stylesheet and one scoped `<style>` per page; no fetched
asset; every chrome link to the skills repo; 27 nodes and 36 edges matching
`relationships.py` with every endpoint a real skill directory; all 27 isolation
rules present; **95 body links** resolving (54 blob, 32 off-repo, 7 cross-page,
2 same-page fragments — 92 on skill pages plus 3 on narrative pages); 0 of 27
descriptions deviating from the first-sentence rule.

An earlier revision of this table gave 92 in one row and 95 in another. Both
were counts of different scopes stated as if they were the same thing: 92 is
skill pages only. The figure is **95** everywhere it now appears.

## Generator-logic gaps

**None open.** Every gap this ledger raised has been fixed in the generator and
re-verified against the build at `30ea8d8`.

Closed over the course of the build phase:

| Gap | Fixed in | Verified now |
|---|---|---|
| Term 17 — `description.split(".")[0]` truncated at `CLAUDE.md` | `e97763c` | 0 of 27 descriptions deviate from the first-sentence rule |
| Term 20 — leading `<h1>` no longer dropped, 24 pages with a duplicate title | `e3abbbb` | 0 of 31 pages carry a second `<h1>`, 0 empty bodies; a test pins both directions |
| Empty `writing-for-agents` body | `e97763c` / `e3abbbb` | Body renders in full |
| Index masthead stated the same sentence twice | `4f6c243` | Subtitle gone; the lede carries it |
| `<h1>` read `Skills`, pack is lowercase `skills` | `4f6c243` | Renders `skills` |
| `Bundled` hard-coded to `SKILL.md` | `4f6c243` | `ui-craft` shows `SKILL.md + agents/ + reference/ + scripts/` |
| `Invoke` missing its leading slash | `4f6c243` | Renders `/ui-craft` |
| Underscore emphasis rendered literally | `e3abbbb` | 0 literal `_…_` on `writing-for-agents`; 24 `<em>` elements |
| Edge anchors ignored direction | `e3abbbb` | `edge_path()` picks the side by relative position; the narrative flow's right-to-left row now points left instead of crossing the figure |
| Emphasis corrupted code spans | `30ea8d8` | 0 `<code>` elements contain injected `<em>`/`<strong>`; 55 underscore-bearing identifiers (`fix_introduced_defect`, `CODING_STANDARDS.md`) render literally |
| Narrative pages carried an inline `<style>` lock term 2 says they must not | `30ea8d8` | 0 `<style>` blocks on all 3 narrative pages |

None of the last three were numbered terms — no term pins emphasis, edge
routing, or code-span escaping — but all were visible body content, and all are
now correct.

### One observation, not a term violation

Removing the narrative pages' inline `<style>` (correct per term 2) leaves the
global rule in `style.css` unscoped:

```css
.diagram:has(.node:hover) .edge{opacity:.05}
```

It fires on every diagram, but the lift rules that compensate for it are only
generated for isolating maps. Measured on `workflows/ticket-flow.html`:
hovering `epic` drops all 5 flow edges to `0.05` and lifts nothing, so the
arrows nearly vanish while the pointer rests on a box.

This violates no term — term 8 governs the isolating map, and term 2 states the
narrative template has no isolating map — so **27/27 stands**. But it is a
visible wrinkle. It has no fix inside `style.css` alone: distinguishing an
isolating diagram needs either a marker class on the `<svg>` or moving the dim
rule into the generated block, both of which are `build.py` changes, so it is
reported rather than fixed under the standing visual-only remit.

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
