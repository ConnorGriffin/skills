# Design

This change replaces local OpenSpec conventions with the v1.x CLI workflow.
The tree migration precedes convention edits: `openspec init` deletes
`openspec/AGENTS.md`, the file the former conventions would otherwise edit.
It does not wait on tool selection. The baseline backfill is independent
because init leaves `openspec/specs/` untouched, so it may proceed in parallel.

## ADR 218 — Change-local deltas become the path to the baseline

Adopt `changes/<id>/specs/<capability>/spec.md` delta specs and merge them into
`openspec/specs/` on archive. Backfill all three current baseline specs, both
to reflect their lagging behavior and to replace their `## Behavior` shape with
the CLI-required `## Purpose` and `## Requirements` structure, including
scenario-bearing requirements.

### Consequences

The baseline becomes the current behavioral source of truth and a qualifying
behavior change has a reviewable delta. The CLI rejects malformed main specs
and requires scenarios for added or modified delta requirements; the existing
baseline cannot pass that contract until the reformat lands.

### Open question — Capability discovery at scale

OpenSpec has no manifest, YAML frontmatter, or cross-linked concept index for
baseline specs: discovery is by capability directory under
`openspec/specs/<capability>/`, plus `openspec list`, `openspec show --diff`,
and the generated `openspec-explore` skill. Upstream uses 35 capability specs
for one CLI while this repository starts with three. How an agent reliably
finds the right capability as that count grows remains unresolved; it bears on
vanilla epics that span many capabilities, but does not block this adoption.

## ADR 218 — Archive after merge

Archive a completed change after its pull request merges, replacing the
in-PR archival rule in the legacy OpenSpec instructions and the `openspec-adopt`
and `epic` skills. The CLI is Git-unaware; timing is therefore this repository's
workflow decision, while `openspec archive --json --yes` performs the validated
delta merge and move.

### Consequences

Shared specs advance only for merged work. Until this change specifies an
automation or other enforcement mechanism, a human must remember to archive;
the archive command does not establish that responsibility itself.

State that repository convention once, as `openspec/config.yaml` advisory
guidance under `operations.archive`. OpenSpec defines that field for
operation-specific repository guidance, while its team workflow recommends
post-merge archive but deliberately leaves Git timing unenforced. Skills may
tell an adopter to configure the operation; they do not retain parallel copies
of this repository's timing rule. The convention remains human-enforced: no
hook, workflow, or agent guard pretends that the Git-unaware CLI can prove the
merge boundary.

## ADR 218 — Design files carry new ADRs

Record new load-bearing decisions in each OpenSpec change's `design.md` under
`## ADR <issue> — Title`. `docs/adr/` is frozen as legacy history: its existing
records, names, and links remain, but no new records land there.

The repository charter already states this OpenSpec ADR-home rule. Only
`openspec/AGENTS.md` contradicts it by directing ADRs to `docs/adr/`; the
charter does not require an edit for this decision.

## ADR 218 — Epics use vanilla change task lists

Model an epic as one OpenSpec change whose `tasks.md` entries link the tracker
child issues. Remove the `ledger.md` convention from the `epic` skill rather
than preserving a parallel epic state artifact.

Issue #218 applies this decision to itself as the first epic run this way. It
uses `tasks.md` as its child index and deliberately has neither `ledger.md` nor
a standing planning pull request, so the decision is exercised before it ships
in the `epic` skill.

### Consequences

An epic retains tracker-native child ownership while OpenSpec retains the
single checked-in implementation checklist and change history.

The useful ledger concerns move to their vanilla authorities instead of into a
replacement index. Unsettled questions live under `Open Questions` in the
epic's `design.md`; task drafting resolves any question that could change the
build, and a precise investigation becomes a tracker spike when it needs
independent work. Durable decisions remain in `design.md`; child type, status,
dependencies, and deferral remain in the tracker; the checked implementation
sequence and child links remain in `tasks.md`; session cost remains ticket
telemetry. The ledger's derived status line, pointer-only notes, duplicated
child summaries, and round narrative are dropped because those facts already
have authoritative homes. This is the deliberate replacement for `Fog`, not a
new ledger under another name.

## ADR 218 — The OpenSpec CLI is repository tooling, not pack runtime

Use `@fission-ai/openspec` 1.11.0, which requires Node >=20.19.0, as pinned
development and CI tooling for this repository. Use its deterministic strict
validation and non-interactive JSON archive command; do not add it as a pack
dependency.

### Consequences

The pack continues to install and run on stock Python 3 and Node 20 with no
package-manager step. The documented CLI installation path is global install;
whether npx is supported remains unconfirmed and is not assumed here.

## ADR 218 — Migrate the OpenSpec tree through v1.x initialization

Replace the pre-1.0 legacy `openspec/AGENTS.md` and `project.md` practice with
the v1.x tree produced by `openspec init`, whose core artifact is
`openspec/config.yaml`. Init can also generate twelve per-tool agent skills
(`openspec-propose`, `openspec-apply-change`, `openspec-archive-change`,
`openspec-explore`, and the rest of that set); this repository declines them,
for the reason recorded below. Migrate useful `project.md` context manually
into `config.yaml`; init removes `openspec/AGENTS.md` but leaves `project.md`
for that manual migration.

The migration runs `openspec init --tools none`. The CLI is adopted for its
deterministic checks, `validate --strict` and `archive`, not for its agent
workflow. Generating the twelve skills would install a second planning
lifecycle (`/opsx:propose`, `apply`, `archive`) that duplicates what the pack's
own `ticket` and `epic` drivers already do against the same repository, and a
duplicated lifecycle is a maintenance liability rather than a convenience.

### Consequences

`openspec/config.yaml` is the only artifact the migration adds. No `.claude/`,
`.codex/`, or root `AGENTS.md` content is generated, so no tracked file gains a
tool marker block and no per-machine artifact needs ignoring. `.claude/` and
`.agents/` are already ignored, but `.codex/` is not, so selecting a tool later
would require a `.gitignore` change first.

Agents continue to learn this repository's OpenSpec practice from its own
instructions and from `config.yaml`'s `context:` and `rules:` fields, which the
CLI injects into every planning request. Adopting the generated skills later
remains available and reversible; it is a `--tools` value, not a migration.
