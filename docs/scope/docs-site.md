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
- Accepted failure: generator breaks on a future SKILL.md format change → Pages deploy workflow fails visibly; operator fixes manually. Stale hand-authored narrative prose is accepted.
- Unsupported: non-GitHub-Pages hosting; browsers without SVG.
- Evidence owed: generator unit test that builds the site from the real repo and asserts every skill in skills/*/ has a page and every cross-link resolves.
- Why: public but disposable documentation; one operator; fully recoverable.
- Disposition: copied into the work order.

## Open questions

(none)

## Spawned tasks

(none)
