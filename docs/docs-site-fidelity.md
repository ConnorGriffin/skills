# Fidelity ledger — docs-site (#198)

Build-phase evidence for [`mockups/docs-site.lock.md`](../mockups/docs-site.lock.md),
produced per `ui-craft` `build`. One row per manifest term, all 27.

## Provenance

| Artifact | SHA |
|---|---|
| Branch / base commit | `codex/198-docs-site` @ `4f6c2431592365fdb48b8c4c3b6f4b9e81087d8b` |
| Ported from commits | `0d2cf18` (generated site), `bee47c7` (publish), `e97763c` + `4f6c243` (review fixes) |
| `mockups/docs-site.lock.md` | `a654855bc3d95b621c83e803394666cf2b770003` |
| `mockups/docs-site-index.html` | `0968f55787ad9d640df0208c78d283d629c604a7` |
| `mockups/docs-site-skill.html` | `bd80501a93789660016f5f0692c2140e230bb616` |
| `mockups/docs-site-narrative.html` | `d550f1cbc7b4effe5ec5453dc036a132cc0ed3d5` |
| `mockups/_theme.css` | `33debf586cac2e62119248304f19b43f0742b43d` |
| `site/build.py` | `20ee2cf53c28d840a6a4f512bb2cac1b06aff35f` |
| `site/style.css` (unchanged since `3c18680`) | `360570756094f9f705b2f091e6c45b754bf0be74` |
| `site/relationships.py` | `d6aaa44c44ed6c38f3ac56da3c0d0f45237b3e33` |
| `site/narratives/ticket-flow.md` | `465630cedb9833178598f7f2067b8e8882d9f96d` |
| `tests/test_site_build.py` | `d420e38a27c0768d309f0271fc36c4d510d91526` |

Rebuild: `python3 site/build.py --out _site` (from a cleared `_site/`). Suite:
`python3 -m unittest tests.test_site_build` — **OK** (2 tests).

**This table describes the build at `4f6c243`.** It was refreshed after the review
fixes; three rows changed verdict or evidence, and one of those is a new failure
the fixes introduced. Every row below was re-run against this output, not
carried over.

## Grading caveat — read before trusting this table

`build.md` puts statuses in the hands of a verifier who did not author the port
and cannot see the builder's notes. That holds for most of this table: I did not
write the port (commits above), so grading it is verification.

It does **not** hold for terms **7, 18, 21, 23 and 14**, where I found the miss
*and wrote the fix*. Those rows are self-graded and are the weakest evidence
here. They are marked ✎ and want an independent eye.

## Evidence index

Paired renders, mock beside build — `mockups/` on port 8861, `_site/` on 8860.
Headless Chrome. **Not committed**: `.gitignore` excludes `*.png` and `lock.md`
§6 keeps screenshots out of the repo.

Directory: `/private/tmp/claude-501/-Users-connor-Code-ConnorGriffin-skills/dfc11b06-7946-402d-8988-ebaceb922980/scratchpad/fidelity/` — 17 files.

Re-captured for this refresh (the pages the review fixes changed):

| File | Covers | Why re-captured |
|---|---|---|
| `index-1280-light-BUILD.png` | 5–9, 11–17, 24 | term 17 blurbs; masthead duplication and casing fixed |
| `index-1280-dark-BUILD.png` | 13, 14 | same, dark |
| `index-375-light-BUILD.png` | 10, 15 | same, mobile |
| `narrative-1280-light-BUILD.png` | 22, 23 | narrative inline-style scoping + text fixes |
| `narrative-1280-dark-BUILD.png` | 22, 23 | same, dark |
| `skill-wfa-1280-light-BUILD.png` | 17–21, 26, 27 | `writing-for-agents` body was empty, now renders; also the leaf case for term 21's empty bands |
| `skill-1280-light-BUILD.png` | 18–21, **20** | shows the new double-`<h1>` regression, and `/ui-craft` + real `Bundled` |
| `skill-1280-dark-BUILD.png` | 13, 14, 18–21 | same, dark |

Unchanged from the previous pass (still current — the fixes did not touch what
they evidence): `index-{1280-light,1280-dark,375-light}-MOCK.png`,
`index-{768-light,1440-light}-BUILD.png`,
`skill-1280-{light,dark}-MOCK.png`, `narrative-1280-{light,dark}-MOCK.png`.

## Ledger

| # | Term | Status | Evidence |
|---|------|--------|----------|
| 1 | Zero JavaScript | met | Gate sweep: no `<script>`, `javascript:`, or `on*=` across all 31 pages |
| 2 | One hand-written stylesheet + generated isolation `<style>` | met | 1 `<link rel=stylesheet>` and exactly one `<style>` per page, containing only `.diagram` isolation rules. **Evidence corrected:** the previous ledger said narrative pages carry no `<style>`; that was wrong when written and is wrong now — every page carries one. Since `4f6c243` the block is scoped per page (index 4174 B for 27 skills; a skill page 930 B; a narrative page 854 B) rather than every page shipping the full set |
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
| 20 | One `<h1>`, body's leading heading dropped | **blocked** | **Regression introduced by `e97763c`.** 24 of 27 skill pages now render two `<h1>`s — the page title and the body's own (`ui-craft` shows "ui-craft" then a large unstyled "UI craft"). Only the 3 skills with no top-level body heading pass. Text logic, not CSS/SVG: **reported, not fixed** (see below). Pair `skill-1280-light-BUILD` |
| 21 ✎ | Focused map: `referenced by` / self / `references` | met **after fix** | **Was missed**: bands were labelled `workflows`/`drivers`/`tools` at map coordinates — wrong text *and* misaligned, since either band mixes categories. Fixed in `site/build.py` `diagram()`; labels now `referenced by` / `references`. Pair `skill-1280-light` |
| 22 | Narrative: prose at measure, one flow diagram, above the prose | met | One `<figure>` precedes `.prose.body`; boxes carry category colours |
| 23 ✎ | Flow wraps serpentine | met **after fix** | **Was missed**: rows both ran left-to-right, so step 3→4 wrapped diagonally across the figure. Fixed in `site/build.py` `diagram()`; row 0 x=24/224/424, row 1 x=424/224. Pair `narrative-1280-light` |
| 24 | Persistent chrome: same six-item nav + footer, `aria-current` | met | Nav verbatim and in order on all 31 pages; footer with MIT provenance on all 31 |
| 25 | No mockbar, no `href="#"` placeholder | met | Zero `href="#"` across the built site; no `.mockbar` |
| 26 | Body link destinations; fragment split and re-attached | met | All 92 body links resolve: 51 blob (every path exists on disk), 7 cross-page skill links, 2 fragments, 32 off-repo passthrough. `../scope/SKILL.md#risk-contract` → `scope.html#risk-contract` |
| 27 | Deterministic GitHub-style heading slugs; fragments resolve | met | Every fragment resolves to an emitted heading id on its target page: 2 same-page, 3 cross-page. Slug rule matches on punctuation and duplicate cases |

**Counts: 26 met, 0 re-settle requested, 1 blocked** (term 20).

Movement since the previous ledger: term 17 blocked → met, term 20 met →
blocked, term 2's evidence corrected. Five of the 26 met rows are ✎ self-graded
because I authored their fix; all five were re-verified against this build.

## Generator-logic gaps — reported, not fixed

Outside the visual/CSS/SVG remit. None of these are CSS or SVG.

### Open

1. **Term 20 — two `<h1>`s per skill page (blocking).** `site/build.py`
   `markdown()`:

   ```python
   if drop_leading_h1 and lines and lines[0].startswith("# "):
   ```

   A SKILL.md body always begins with a blank line once frontmatter is
   stripped, so `lines[0]` is `""` and the drop never fires. 24 of 27 skill
   pages render the body's `# Title` as a second `<h1>`; the 3 that pass have
   no top-level body heading at all, so there is nothing to drop.

   The predecessor scanned forward to the first `# ` line and dropped it, which
   is why the previous ledger recorded term 20 as met — but it also consumed
   the *entire* body when no such line existed, which is the empty
   `writing-for-agents` bug `e97763c` set out to fix. Both are satisfied by
   skipping leading blanks first and then dropping only if that line is a
   top-level heading:

   ```python
   while i < len(lines) and not lines[i].strip():
       i += 1
   if drop_leading_h1 and i < len(lines) and lines[i].startswith("# "):
       i += 1
   else:
       i = 0
   ```

   Verified in a scratch copy of `build.py` (not committed): 0 skill pages with
   a duplicate `<h1>` **and** 0 empty bodies — it satisfies both constraints at
   once, so fixing term 20 need not re-break `writing-for-agents`.

2. **Underscore emphasis renders literally.** `_process_` and `_and_` appear
   verbatim on the `writing-for-agents` page (4 occurrences). `inline()`
   handles `**bold**` but not `_em_`. Not a numbered term — no term pins
   emphasis — but it is visible body text.

3. **Edge anchors ignore direction.** Every edge leaves the source's right side
   and enters the target's left, even when the target sits to the left, so
   backward edges cross their own boxes. The mock chose the side by relative
   position. Not a numbered term; most visible on the narrative flow.

### Fixed since the previous ledger

Verified against this build, no longer outstanding:

- Term 17's first-sentence rule (`e97763c`) — see the ledger row.
- Index masthead no longer states the same sentence twice; the subtitle is gone
  and the lede carries it.
- `<h1>` now reads `skills`, lowercase, matching the mock and the footer.
- `Bundled` now lists what the skill actually ships — `ui-craft` shows
  `SKILL.md + agents/ + reference/ + scripts/`.
- `Invoke` now renders `/ui-craft` with the leading slash.

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
