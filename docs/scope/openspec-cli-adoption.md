# Scope: openspec CLI adoption

Adopt the `openspec` CLI in the skills repo so agents validate OpenSpec structure
against deterministic checks (`openspec validate --strict`, `list`, `archive`)
instead of following prose conventions. Slots into the broader
vanilla-OpenSpec standardization effort (spec deltas + baseline backfill,
post-merge archiving, ADRs in change `design.md`, vanilla epics).

## Decisions

- Route: research — the dominant uncertainty is missing facts about the CLI
  itself (what strict validation enforces, install/pinning model, whether the
  repo's current and planned layouts pass, how `archive` composes with
  post-merge archiving). Why: nothing is buildable until the tool's real
  contract is known; team has no prior CLI practice to copy. `inline`
- Standardization decisions already settled upstream of this scope (from the
  audit session, 2026-08-28): adopt spec deltas + backfill baseline; post-merge
  archiving; ADRs move into change `design.md` (charter edit, `docs/adr/`
  frozen as legacy); epics go vanilla (`tasks.md` with tracker-issue links,
  drop `ledger.md`). Why: operator chose upstream-standard practice over
  pack-invented conventions. `→ issue` (the standardization epic)
- Pack constraint: the CLI must not become a pack dependency — pack installs
  from stock Python 3 + Node 20. CLI is dev/CI tooling for this repo (and
  optionally the operator's machine), not shipped with the pack. Why:
  CLAUDE.md portability hazard. `inline`

- Research findings recorded in `docs/research/openspec-cli.md`
  (primary-source: upstream clone at v1.11.0 + npm registry metadata;
  citations spot-verified). Key facts: package `@fission-ai/openspec` 1.11.0,
  Node ≥20.19.0, global install is the documented path (npx unconfirmed);
  `validate --strict` gates warnings, requires ≥1 scenario per ADDED/MODIFIED
  delta requirement, never checks `tasks.md`, tolerates extra files
  (`ledger.md`, evidence); `archive` merges deltas into `specs/`
  automatically, is git-unaware (pre/post-merge is pure convention), and has
  first-class `--json`/`--yes` CI modes. Why: answers all five open
  questions. `inline`
- Our hand-scaffolded `openspec/AGENTS.md` + `project.md` layout is upstream's
  **pre-1.0 legacy shape**: v1.0 (OPSX) removed generation of both;
  `openspec init` now writes `openspec/config.yaml` plus per-tool agent
  skills/commands, and its migration pass auto-deletes `openspec/AGENTS.md`
  while leaving `project.md` for manual migration into `config.yaml`. CLI
  adoption therefore implies migrating our tree to the v1.x shape, and
  `openspec-adopt` must scaffold via `openspec init`, not by hand. Why:
  adopting the CLI against a legacy-shaped tree fights the tool's own
  cleanup. `→ issue` (standardization epic)

## Open questions

- None remaining from this scope. (npx support and pre/post-merge stance are
  upstream-unconfirmed; both have safe defaults — global install, and the
  post-merge convention already decided.)

## Spawned tasks

- `docs/research/openspec-cli.md` — findings doc (this session).
- GitHub issue #217 — orchestrate adapters lack worker network access;
  research worker had to be resumed against coordinator-fetched sources.
- GitHub issue #218 — vanilla-OpenSpec standardization epic (all four settled
  decisions + CLI adoption + legacy-shape migration). Discharges both
  `→ issue` dispositions above.
