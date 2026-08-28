---
name: openspec-adopt
description: "Adopt OpenSpec in a repo that lacks it: scaffold the openspec/ layout, write baseline specs describing the system as it exists today (from code, docs, and git history), and deliver the whole thing as a documentation-only PR. One-time per repo. Trigger when the user asks to adopt openspec, add openspec to a repo, scaffold openspec, or write baseline specs. Invoked as /openspec-adopt <org/repo or path>."
---

# openspec-adopt

One-time OpenSpec adoption for a repo. Scaffolds the documentation baseline before any change proposals reference it.

## Procedure

1. **Check it is actually absent.** An existing `openspec/` means this skill has nothing to do; point at it and stop.

2. **Require the pinned CLI.** OpenSpec is target-repository development tooling. Confirm that global `@fission-ai/openspec@1.11.0` is available as `openspec`; if it is absent, stop visibly before changing the target repository. Do not substitute another version or a package-runner invocation.

3. **Initialize the v1 tree.** Run `openspec init --tools none` at the target repository root. If initialization fails, stop visibly; do not construct a replacement tree. This produces `openspec/config.yaml`, `openspec/specs/`, and `openspec/changes/archive/` without editor integrations.

4. **Record repository context and operations.** Put the repo purpose, tech stack, conventions, and commit/PR standards in `openspec/config.yaml`'s `context:` and `rules:`. Source them from README, CONTRIBUTING, CI workflows, and observed code idioms. Record the repository's chosen archive timing and landing path at `operations.archive.guidance`; this is a repository-local convention, not a rule supplied by this skill.

5. **Choose spec domains.** Select two to four domains that partition the system by behavior. Name them for what the system does, not for directories. Examples: authentication, persistence, deployment, external integration.

6. **Write baseline specs.** For each domain, `specs/<domain>/spec.md` describing current behavior and contracts: what exists, what invariants hold, what other systems depend on. Ground every claim in code you read or history you checked; a baseline is worthless if it guesses. Reference concrete files only where the file is the contract (a schema, a versions manifest).

7. **Validate the result.** Run `openspec validate --all --strict` at the target repository root and fix every reported issue; do not deliver a baseline the CLI rejects.

8. **Deliver as a PR.** Branch, commit the initialized tree and baselines, `gh pr create`, documentation-only, no code changes. The PR body states the baseline is a starting point and invites corrections from the people who know the system.

## Rules

* Never bundle adoption with a functional change; the baseline gets reviewed on its own.
* Never write a baseline for a repo you have not read; if the repo is too large to ground properly, propose fewer domains and say what was left unspecified.
* Specs describe behavior and contracts, not implementation walkthroughs.
* Do not add generated agent integrations, `openspec/AGENTS.md`, or `openspec/project.md`.
