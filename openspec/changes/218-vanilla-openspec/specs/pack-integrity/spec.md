# Pack integrity — deltas

## MODIFIED Requirements

### Requirement: Repository checks

Pull-request and main-branch CI MUST run the repository validator, its named
public-interface unittest modules, syntax checks, and the DCO check where
applicable, and MUST install exactly the pinned OpenSpec CLI version through
the documented global npm path and run `openspec validate --all --strict` so an
invalid baseline spec or active change fails CI deterministically. CI MUST run
the configured install, installed-copy, and browser-driver checks when
changed-path classification selects the expensive path. The repository MUST
treat named unittest and syntax-check lists as explicit selections rather than
a claim that every eligible file is discovered automatically, and the OpenSpec
CLI MUST remain repository CI and development tooling rather than a pack
runtime dependency.

#### Scenario: CI evaluates a proposed pack change

- **WHEN** the validation workflow runs for a pull request
- **THEN** it installs the pinned OpenSpec CLI, strictly validates every
  baseline spec and active change, executes the always-required checks, and
  conditionally executes the changed-path-gated checks

#### Scenario: An OpenSpec artifact is malformed

- **WHEN** a baseline spec or an active change's delta fails strict validation
- **THEN** the validation workflow exits unsuccessfully before merge
