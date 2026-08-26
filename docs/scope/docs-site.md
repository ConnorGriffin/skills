# Scope ledger — GitHub Pages docs site (ticket #198)

## Decisions

- Build: Python-stdlib generator in the repo, run by a GitHub Actions Pages workflow on push to main. Why: keeps the repo's no-third-party-dependency rule; site regenerates from real skill files. — inline
- Visuals: generator emits inline SVG at build time from real skill metadata; no runtime JS/CDN. Why: deterministic, dependency-free, fully styleable. — inline
- Content: relationship data and per-skill summaries derived from SKILL.md frontmatter + README tables; workflow narratives hand-authored under the site source. Why: prose "how it works" isn't derivable. — inline
- Coverage: workflows, drivers, tools categories only; profile/output-styles/hooks excluded. Why: operator-personal, off the public story. — inline
- Pages enablement: operator enables Pages (workflow build mode) himself; the order assumes it is enabled and does not verify. — inline
- Execution: /ticket start via /orchestrate, Codex-model workers only (no Claude workers), per operator instruction. — inline

### Risk contract

- Must prevent: secret exposure; publishing content identifying real colleagues (persona-review hazard); silent incorrect success (site claiming a skill exists that doesn't).
- Must recover: nothing automatic.
- Accepted failure: generator breaks on a future SKILL.md format change → Pages deploy workflow fails visibly; operator fixes manually. Stale hand-authored narrative prose is accepted; stale or incomplete hand-maintained relationship edges are accepted (only endpoint existence is checked).
- Unsupported: non-GitHub-Pages hosting; browsers without SVG.
- Evidence owed: generator unit test that builds the site from the real repo and asserts every skill in skills/*/ has a page and every cross-link resolves.
- Why: public but disposable documentation; one operator; fully recoverable.
- Disposition: copied into the work order.

- Edge graph source (lock manifest open question): settled as the hand-maintained `site/relationships.py` (uses + requirements), transcribed from README tables and SKILL.md prose, endpoint-existence-checked at build. The lock mock's SKILL.md body scan (87 edges) was exploratory, not authoritative. Lock term 8 (hover isolation) stands regardless of edge density; resettle only if the built map makes it pointless. — inline

## Open questions

(none)

## Spawned tasks

(none)

## Review rounds (triage, /plan-review via Sol worker)

- Round 1: 5 blockers, all `authoring` (lifecycle stamp, forbidden escalation path, non-byte-exact verification, open producer/consumer schema, undefined disclosure oracle). All verified and fixed; ui-craft lock produced (e9bcab9).
- Round 2: 5 blockers — 1 `authoring` (converter scope), 4 `injected` by the round-1 lock (edge-source contradiction, link-term contradiction, body-link rule, wrong footer license). Fixed via resettle ba5e06b.
- Round 3 (cap): 2 blockers, both `injected` narrowing defects (origin allowlist tighter than real bodies; unspecified anchor slugs). Judged mechanical with obvious defaults, no unsettled human decision (scope's nothing-uncertain rule), fixed via resettle e5c9813 and order amendment; posted without a fourth panel per the cap.
