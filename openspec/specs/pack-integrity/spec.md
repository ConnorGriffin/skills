# Pack integrity

## Purpose

Define the structural, validation, runtime, and publication rules that keep the
skill pack safe to install and predictable for interactive agents.

## Requirements

### Requirement: Structural validation

The repository validator MUST require the exact supported skill set under the
three recognized categories, a valid `SKILL.md` and `agents/openai.yaml` for each
skill, resolving relative Markdown links, and tracked content that passes the
repository's disclosure guards.

#### Scenario: A malformed skill enters the tracked tree

- **WHEN** `scripts/validate.py` runs with a missing skill metadata file, a broken
  relative link, an unexpected skill directory, or forbidden tracked content
- **THEN** validation exits unsuccessfully and identifies the violated structural
  rule

### Requirement: Repository checks

Pull-request and main-branch CI MUST run the repository validator, its named
public-interface unittest modules, syntax checks, and the DCO check where
applicable, and MUST install exactly the pinned OpenSpec CLI version through
the documented global npm path and run `openspec validate --all --strict` so an
invalid baseline spec or active change fails CI deterministically. CI MUST run
the configured install, installed-copy, and browser-driver checks when
changed-path classification selects the expensive path. The repository MUST
treat named unittest and syntax-check lists as explicit selections rather than
a claim that every eligible file is discovered automatically. The unittest
module selection in the documented test command MUST equal the selection in
the primary validation workflow, and a repository test MUST reject drift
between them. The OpenSpec CLI MUST remain repository CI and development
tooling rather than a pack runtime dependency.

#### Scenario: CI evaluates a proposed pack change

- **WHEN** the validation workflow runs for a pull request
- **THEN** it installs the pinned OpenSpec CLI, strictly validates every
  baseline spec and active change, executes the always-required checks, and
  conditionally executes the changed-path-gated checks

#### Scenario: The documented and primary CI unittest selections drift

- **WHEN** a unittest module is named by exactly one of the documented test
  command and the primary validation workflow
- **THEN** the repository's regression suite exits unsuccessfully and identifies
  the unequal selections

#### Scenario: An OpenSpec artifact is malformed

- **WHEN** a baseline spec or an active change's delta fails strict validation
- **THEN** the validation workflow exits unsuccessfully before merge

### Requirement: Local pre-push gate

The repository pre-push hook MUST run structural validation and MUST check the
DCO trailers of the commits each pushed ref would publish when a comparison base
can be resolved.

#### Scenario: A contributor pushes a branch through the installed hook

- **WHEN** Git invokes `scripts/pre-push` with a non-deletion ref update
- **THEN** the hook runs `scripts/validate.py` and checks the publishable commit
  range before allowing the push

### Requirement: Supported runtime

The pack SHALL install and run with the Python standard library and Node 20,
without a pack-wide third-party dependency installation step. Repository-only
development tooling and the browser driver's own dependency installation MUST NOT
become runtime dependencies of the skill pack.

#### Scenario: The pack is installed through the skills CLI

- **WHEN** a consumer installs the pack in a supported Python and Node 20
  environment
- **THEN** the skills remain usable without installing a third-party Python
  package or a pack-wide Node dependency set

### Requirement: Published release policy

Maintainers MUST treat every published release tag as immutable history: a
published tag SHALL NOT be moved, retagged, or deleted because installers may pin
the pack by any published ref.

#### Scenario: A published release needs a correction

- **WHEN** a maintainer discovers a defect after a release tag has been published
- **THEN** repository policy requires a new history-preserving correction instead
  of changing or deleting the published tag

### Requirement: Source and installed-copy boundary

Pack changes MUST be made in the authored source under `skills/` and MUST NOT be
made directly in `.agents/skills/` or `.claude/skills/`, which are generated,
pinned installed copies.

#### Scenario: An installed skill copy is stale

- **WHEN** an installed copy differs from the authored skill
- **THEN** the authored source is changed and the copy is regenerated or repinned
  deliberately rather than edited in place
