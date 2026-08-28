# OpenSpec CLI (`@fission-ai/openspec`) — Findings

**Method:** Read directly from a local shallow clone of github.com/Fission-AI/OpenSpec (v1.11.0-era source, not fetched live — network was unavailable this session) and a local npm registry metadata dump for `@fission-ai/openspec`. All citations are repo-relative paths into that clone unless noted. Nothing here was corroborated against the live GitHub repo, live npm registry, or any blog/secondary source — flagged as unconfirmed where the local material doesn't answer.

**Canonical repo:** `github.com/Fission-AI/OpenSpec`, package `@fission-ai/openspec` (`package.json` / npm registry `homepage`/`repository.url`). No successor repo found in the local material — the repo itself *is* mid-rewrite (OPSX, v1.0+), but that's a major version bump, not a fork/successor.

---

## 1. What `openspec validate --strict` enforces

Validation logic lives in `src/core/validation/validator.ts` (class `Validator`), invoked via `src/commands/validate.ts`.

- **Two validation targets:** a `spec` (`validator.validateSpec`, reads `openspec/specs/<id>/spec.md`) and a `change`'s delta specs (`validator.validateChangeDeltaSpecs`, reads `openspec/changes/<id>/specs/**/spec.md`). `openspec validate <name>` auto-detects which; `--type change|spec` overrides (`src/commands/validate.ts:215-236`).
- **`--strict` semantics:** in `Validator.createReport` (`validator.ts:782-800`), `valid = strictMode ? errors===0 && warnings===0 : errors===0`. Strict mode turns every WARNING into a blocking failure; it adds no new checks of its own — it's a severity gate, not a schema toggle.
- **Delta spec format enforced** (`validateChangeDeltaSpecs`, `validator.ts:159-467`):
  - Delta headers recognized: `## ADDED Requirements`, `## MODIFIED Requirements`, `## REMOVED Requirements`, `## RENAMED Requirements` (case-insensitive matching elsewhere, e.g. `archive.ts:1258`). Non-canonical `###` headers under those sections (missing `### Requirement:` prefix, or a nameless `### Requirement:`) are flagged **INFO**, not an error — they're silently skipped by the parser, not rejected (`validator.ts:205-221`).
  - **ADDED/MODIFIED**: each block needs requirement text (ERROR if missing) and at least one scenario (ERROR if `countScenarios < 1`, `validator.ts:270-274, 305-309`). Missing SHALL/MUST in the body is only a WARNING (guidance) in normal mode; the header (`constants.ts:63,67`) documents scenarios must be level-4 `#### Scenario:` headers.
  - **REMOVED**: names only — no scenario/description required (`validator.ts:331-340`).
  - **RENAMED**: `from`/`to` pairs checked for duplicates within RENAMED and cross-checked against ADDED/MODIFIED/REMOVED for conflicts (`validator.ts:342-396`).
  - Duplicate requirement names within a section, and cross-section conflicts (same name in both MODIFIED+REMOVED, MODIFIED+ADDED, ADDED+REMOVED, RENAMED collisions) are ERRORs.
  - **Scenario-loss guard** (`findScenarioLossIssues`, `validator.ts:537-621`): when `mainSpecsDir` is passed (standalone `validate` does pass it — `src/commands/validate.ts:220-223`), a MODIFIED block that drops a scenario the current main spec still has is an ERROR — the same check `archive` enforces before merging, run early at authoring time.
  - A **`spec.md` sitting directly under `specs/`** (no capability folder) is an ERROR — the merge path ignores it silently, so validate blocks it explicitly (`validator.ts:183-192`).
  - **Zero deltas total** across all files is an ERROR (`CHANGE_NO_DELTAS`) unless the change declares `skip_specs: true` in `.openspec.yaml` (see below).
- **Main spec format** (`applySpecRules`, `validator.ts:641-720`): requires `## Purpose` and `## Requirements` sections (structural check via `findMainSpecStructureIssues`); Purpose too brief (<50 chars) or still a placeholder → WARNING; each requirement needs ≥1 scenario (WARNING if none) and SHALL/MUST in the body (WARNING if missing).
- **`tasks.md` is NOT checked by ordinary `validate`** (direct, bulk, or strict) — it's out of scope for delta/spec validation entirely. It's only checked by the separate `--archived` mode, which lints already-archived changes' `tasks.md` for unchecked boxes (`src/commands/validate.ts:444-533`, `runArchivedTaskValidation`) — a distinct opt-in scope added in v1.9.0 per `CHANGELOG.md:65`, meant for a pre-commit/CI hook. It does not run under a bare `--strict` invocation.
- **Unknown/extra files are tolerated.** `discoverSpecFiles` (`src/utils/spec-discovery.ts:38-76`) only walks for files literally named `spec.md`; anything else under `specs/` or elsewhere in the change directory (a `ledger.md`, an `evidence/` folder, etc.) is never inspected. The one exception: if `skip_specs: true` is declared in `.openspec.yaml`, `hasAnyFileUnder` (`spec-discovery.ts:93-115`) checks whether *any* non-dot file exists under `specs/` specifically, and flags a conflict if so (`CHANGE_SKIP_SPECS_CONFLICT`, `validator.ts:447-449`) — but files outside `specs/` are never touched by this check either. See Q4 for detail.

## 2. Install / pin story

- **Package name:** `@fission-ai/openspec` (npm scoped package; bin name `openspec` per `package.json` `bin.openspec: "bin/openspec.js"`, confirmed in npm registry dump).
- **Current version (as of this local snapshot):** `1.11.0` (`dist-tags.latest`), also the newest `## 1.11.0` entry in `CHANGELOG.md`. `dist-tags` also show `next: 0.3.0` (stale/unused tag) and `beta: 1.6.0-beta.1`.
- **Node requirement:** `"engines": {"node": ">=20.19.0"}` in every published version inspected (0.1.0 through 1.11.0, per npm registry dump) — this has been stable since the first release. **Node 20 is OK** as long as it's ≥20.19.0 specifically (not just "Node 20"); `docs/installation.md:5` states the same floor.
- **npx vs global install:** the project's own docs (`docs/installation.md`) only document **global install** (`npm install -g @fission-ai/openspec@latest`, plus pnpm/yarn/bun/deno/Nix equivalents) and running `openspec` as a persistent CLI thereafter — there is no documented `npx openspec ...` invocation pattern in the local docs tree. `npx` would presumably work as a one-off since it's a normal npm package with a `bin`, but I found no evidence the maintainers document or recommend it. **Unconfirmed** whether npx is a supported/tested path.
- **CI suitability/cost:** the CLI supports `--json` output on `validate`, `archive`, `status`, `schemas`, etc. (see below), non-interactive flags (`--yes`, `--no-interactive`, `CI`/`OPEN_SPEC_INTERACTIVE=0` env vars are recognized per `CHANGELOG.md:135`), and machine-readable diagnostics on failure. A **global install** is the documented pattern, meaning CI would run `npm install -g @fission-ai/openspec@<version>` (or pin via lockfile-adjacent tooling) as a setup step — there's no `npx`-style zero-install path documented. `docs/installation.md:173` recommends running `openspec update` after upgrading the global package, but that step is about regenerating AI-tool skill/command files, not relevant to a CI validation job.

## 3. `openspec archive` behavior

Source: `src/core/archive.ts` (class `ArchiveCommand`), ~2100 lines.

- **Yes, it merges delta specs into `openspec/specs/` automatically** (unless `--skip-specs`). Flow (`ArchiveCommand.run`, `archive.ts:1108` onward):
  1. Validates the change's proposal (informative only) and delta specs (blocking, unless `--no-validate`) — same `Validator` as standalone `validate`.
  2. Reports task-completion status; incomplete tasks require `--yes` or an interactive confirmation to proceed (not archive-blocking on their own — just a warn-and-confirm gate, `archive.ts:1334-1371`).
  3. Computes spec updates (`findSpecUpdates`), rebuilds each target main spec from ADDED/MODIFIED/REMOVED/RENAMED deltas (`buildUpdatedSpec`), previews the change, asks for confirmation (or `--yes`), then validates every rebuilt spec before writing any of them.
  4. Writes the rebuilt main specs, or — if a change removes a capability's last requirement and `retire_capabilities: true` is declared in `.openspec.yaml` — deletes that capability's spec file entirely ("retirement", added v1.8.0 per `CHANGELOG.md:129`).
  5. Moves the change directory from `openspec/changes/<name>/` to `openspec/changes/archive/<YYYY-MM-DD>-<name>/` (date-prefixed unless the name already carries a date prefix, `ARCHIVE_DATE_PREFIX_PATTERN`).
  - The whole operation is built to be crash-safe/atomic-ish: content fingerprinting before/after each step, snapshot+rollback on failure, an exclusive `.openspec-archive.lock` claim file, and a fallback copy+verify+delete for cross-device/EPERM moves (`archive.ts:341-570` and surrounding).
- **Lifecycle timing:** the source treats archive purely as a filesystem operation with **no git awareness at all** — no commit, branch, or PR check anywhere in `archive.ts`. Whether it's meant to run pre-merge or post-merge is a **workflow convention, not something the CLI enforces or checks**; docs (`getting-started.md`) show `/opsx:archive` running as the last step of the AI-driven loop (`propose → apply → sync → archive`) before that work is presumably committed/PR'd, but this is a usage convention documented in prose, not a mechanism. **Unconfirmed** whether upstream has an opinion on pre- vs post-merge beyond "archive after implementation is done."
- **Flags on `archive`** (`ArchiveOptions` interface, `archive.ts:174-182`):
  - `--yes` — skips interactive confirmations (spec-update preview, incomplete-tasks warning, skip-validation warning); required in `--json` mode wherever a prompt would otherwise appear (JSON mode never prompts — it throws a machine-readable `ArchiveBlockedError` instead, e.g. `archive_confirmation_required`, `archive_tasks_incomplete`).
  - `--skip-specs` — skips the spec-merge step entirely (change is archived as-is, no `openspec/specs/` changes).
  - `--no-validate` / `validate: false` — skips pre-archive validation (prints a warning, requires `--yes` in JSON mode).
  - `--json` — machine-readable output (`{ archive: {...}, root }` on success, or `{ archive: null, status: [diagnostic] }` on failure) instead of prose/prompts.
  - `--store` / `--store-path` — for the beta multi-repo "stores" feature (root selection), not spec-merge-specific.
- Non-interactive/agent-safety was clearly a deliberate design theme (see the extensive comments around `ArchiveBlockedError` and `confirmOrBlock`, `archive.ts:208-324`): a run with no TTY that hits a would-be prompt fails loudly with a named flag to pass, rather than silently succeeding or hanging.

## 4. Tolerance for extra files in a change directory

**Yes — strict validation tolerates extra files.** `discoverSpecFiles` (`src/utils/spec-discovery.ts:38`) is the sole mechanism `validate`/`archive`/`show`/`apply` use to enumerate delta specs, and it only matches files literally named `spec.md` anywhere under `specs/`. A `ledger.md`, an `evidence/` folder, a `notes.md`, etc. — whether at the change root (alongside `proposal.md`/`tasks.md`) or inside `specs/` — is never read, parsed, or validated by `validate --strict`.

The one narrow exception: if the change declares `skip_specs: true` in `.openspec.yaml` (meaning "this change intentionally has zero spec deltas"), `hasAnyFileUnder(specsDir)` (`spec-discovery.ts:93`) checks for *any* non-dot file under `specs/` specifically (not the change root) and raises `CHANGE_SKIP_SPECS_CONFLICT` if one exists — because such a file would be silently ignored by the merge, contradicting the "no spec changes" claim. This check is scoped to `specs/` only; files elsewhere in the change directory are unaffected even under `skip_specs`.

## 5. What `openspec init` generates, and legacy-tree conflict

**This is the biggest surprise relative to the question's premise: current OpenSpec (v1.0+, current 1.11.0) does *not* generate `project.md` or `openspec/AGENTS.md`.** Those were the *pre-1.0* ("legacy") artifacts, and v1.0's "OPSX" rewrite explicitly removed them as a **documented breaking change**:

> "**Config files removed** — Tool-specific instruction files (`CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `project.md`) are no longer generated" — `CHANGELOG.md:629` (1.0.0 "Major Changes").

What `openspec init` (`src/core/init.ts`, class `InitCommand`) actually generates today, per-selected-tool:

- `openspec/` directory tree: `specs/`, `changes/`, `changes/archive/` (`init.ts:858-893`, `createDirectoryStructure`).
- `openspec/config.yaml` (optional, only if it doesn't already exist) — structured config with `schema:` and optional `context:`/`rules:` fields (`init.ts:1107-1133`, `createConfig`). This is the *replacement* for `project.md`'s freeform context — it's actively injected into every planning request rather than passively hoped to be read (`docs/migration-guide.md:67-80`).
- Per selected AI tool: **Agent Skills** (`SKILL.md` files under e.g. `.claude/skills/openspec-*/`) and/or slash-command files (e.g. `.claude/commands/opsx-*.md` depending on tool/delivery mode) — never a monolithic instruction file (`init.ts:899-1041`, `generateSkillsAndCommands`).
- Optionally, GitHub Copilot cloud-agent files (`.github/workflows/copilot-setup-steps.yml`, `.github/agents/openspec.agent.md`) — opt-in only, since v1.8.0 (`CHANGELOG.md:123`).

**Legacy-tree conflict:** running `openspec init`/`openspec update` on a repo with a hand-scaffolded (or pre-1.0-generated) tree containing `project.md`, `AGENTS.md`, `specs/`, `changes/archive/` is explicitly handled, not a silent conflict:
- `specs/` and `changes/archive/` — untouched (they're the same structure today; `docs/migration-guide.md:27-29`).
- `openspec/AGENTS.md` — auto-deleted (obsolete workflow trigger file), listed under "no user content to preserve" (`src/core/legacy-cleanup.ts:436-608`, `docs/migration-guide.md:39,136`).
- Root-level `CLAUDE.md`/`AGENTS.md`/etc. (`LEGACY_CONFIG_FILES`, `legacy-cleanup.ts:19-26`, includes `CLAUDE.md`, `CLINE.md`, `AGENTS.md`, `QWEN.md`, etc.) — only the OpenSpec marker block inside them is stripped; the rest of the user's file content is preserved, never deleted.
- **`openspec/project.md` is the one file the tool deliberately does NOT touch automatically** — it's flagged in the migration prompt ("Needs your attention... We won't delete this file... Review project.md, move any useful content to config.yaml, then delete the file when ready") and left for the user to migrate by hand into `config.yaml`'s `context:`/`rules:` (`docs/migration-guide.md:57-80, 544-546`, `legacy-cleanup.ts:419` docblock references detecting it as a legacy artifact).
- In non-interactive/CI mode, `openspec init --force` auto-accepts all of the above cleanup except `project.md` deletion, which remains manual regardless (`docs/migration-guide.md:150-160`).

**Is there an `openspec update`?** Yes — confirmed in both docs and changelog. `openspec update` "regenerates the skill and command files for the tools you've configured" (`docs/installation.md:173`), runs the same legacy-detection/cleanup pass as `init` (`docs/migration-guide.md:140-148`), never prompts for destructive choices on its own (e.g. Copilot cloud files are only refreshed if previously opted in, `CHANGELOG.md:125`), and checks whether a newer CLI version is published, offering to upgrade.

---

## Other load-bearing findings

- **JSON output for CI:** widespread and treated as a first-class contract, not an afterthought. `validate`, `archive`, `status` (including new `--all --json` for one-process-many-changes as of 1.11.0, `CHANGELOG.md:7`), `schemas`, and `show` all support `--json`, with structured `{ ..., status: [{severity, code, message, fix}] }` diagnostics on failure rather than free-text stderr (see `ArchiveBlockedError`/`ArchiveDiagnostic` pattern, `archive.ts:184-220`). JSON mode is explicitly designed to never prompt interactively — it fails closed with a machine-actionable diagnostic instead (a repeatedly-cited design goal across changelog entries, e.g. `CHANGELOG.md:135` re: `#1479`).
- **`openspec show --diff`** (new in 1.11.0, `CHANGELOG.md:9`): renders each MODIFIED delta requirement as a diff against the main-spec version it replaces (colorized unified diff in human mode; `diff`/`warning` fields added to the JSON payload for MODIFIED deltas only).
- **Config file:** `openspec/config.yaml`, with `schema:` (required, default `spec-driven`), optional `context:` (≤50KB, injected into every planning request) and per-artifact `rules:`. Schema resolution order: `--schema` CLI flag → change's `.openspec.yaml` → project `config.yaml` → default `spec-driven` (`docs/migration-guide.md:475-481`).
- **Breaking-change history:** the only major (semver-breaking) release in the visible history is **1.0.0** ("OPSX" rewrite — old `/openspec:*` commands removed, `CLAUDE.md`/`.cursorrules`/`AGENTS.md`/`project.md` generation removed, skills replace scattered per-tool config files). Everything from 1.0.0 through 1.11.0 in the local `CHANGELOG.md` is Minor/Patch only — no further major bumps found.
- **`.openspec.yaml`** (change-level metadata file, distinct from `openspec/config.yaml`) carries `schema:` plus optional markers: `skip_specs: true` (declares zero spec deltas intentionally) and `retire_capabilities: true` (authorizes archive to delete a capability's spec when its last requirement is removed). Both markers are only honored when the metadata file is itself schema-valid; an invalid marker is treated as *not declared* rather than silently accepted (`validator.ts:109-124`, `archive.ts:1390-1394`).

## Unconfirmed (flagged, not answered from primary source)

- Whether `npx @fission-ai/openspec ...` (as opposed to a global install) is a supported/tested invocation path — not documented in the local `docs/installation.md`.
- Whether upstream has an explicit stance on archiving pre- vs post-merge — the CLI has no git integration at all, so this is purely a workflow convention in the docs, not a mechanism I can confirm as intentional policy either way.
- Anything published to the live npm registry or GitHub repo *after* this local snapshot (v1.11.0 / npm dump timestamp) — this could not be checked since network access was unavailable this session.