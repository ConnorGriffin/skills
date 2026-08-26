# Surface ledger

One row per user-facing surface. `locked` rows are binding precedent for
adjacent surfaces; `shipped` rows defer to the app itself.

| Surface | Concept | Status | Issue | File |
|---------|---------|--------|-------|------|
| docs-site (index) | grounded atlas — the reference map is the hero, categories index it | locked | #198 | [docs-site-index.html](docs-site-index.html) · [manifest](docs-site.lock.md) |
| docs-site (skill page) | description + meta + focused map + rendered SKILL.md | locked | #198 | [docs-site-skill.html](docs-site-skill.html) · [manifest](docs-site.lock.md) |
| docs-site (workflow narrative) | prose at reading measure + one flow diagram | locked | #198 | [docs-site-narrative.html](docs-site-narrative.html) · [manifest](docs-site.lock.md) |

All three page templates are governed by the single manifest
[docs-site.lock.md](docs-site.lock.md); they share one scaffold
([_theme.css](_theme.css), [SCAFFOLD.md](SCAFFOLD.md)) and one term list.

Terms 3, 4, 7, 19 and the footer string were re-settled on 2026-08-26, and term
26 added, after a cold plan review found five contradictions with the settled
order in `docs/scope/docs-site.md`. Status stays `locked` and no mock file was
added or removed; the record is the manifest's **Re-settled terms** table and
the `RE-SETTLED TERMS` block in each mock header.
