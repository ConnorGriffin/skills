---
name: openspec-adopt
description: Adopt OpenSpec in a repo that lacks it: scaffold the openspec/ layout, write baseline specs describing the system as it exists today (from code, docs, and git history), and deliver the whole thing as a documentation-only PR. One-time per repo. Trigger when the user asks to adopt openspec, add openspec to a repo, scaffold openspec, or write baseline specs. Invoked as /openspec-adopt <org/repo or path>.
---

# openspec-adopt

One-time OpenSpec adoption for a repo. Scaffolds the documentation baseline before any change proposals reference it.

## Procedure

1. **Check it is actually absent.** An existing `openspec/` means this skill has nothing to do; point at it and stop.

2. **Scaffold.** Prefer `npx openspec init` to scaffold the layout, or create the structure by hand if the tool is unavailable. Create these files: `project.md`, `AGENTS.md`, `specs/`, `changes/`, and `changes/archive/`.

   One archiving rule is non-negotiable: a change is archived in the pull request that finishes it, before that PR is marked ready, never in a follow-up commit after merge and never as a push onto an approved PR. Post-merge archiving leaves the folder to whoever remembers, which is nobody.

3. **Write `project.md`.** Repo purpose, tech stack, conventions, commit/PR standards. Source: README, CONTRIBUTING, CI workflows, observed code idioms. Short; it is context, not documentation.

4. **Choose spec domains.** Select two to four domains that partition the system by behavior. Name them for what the system does, not for directories. Examples: authentication, persistence, deployment, external integration.

5. **Write baseline specs.** For each domain, `specs/<domain>/spec.md` describing current behavior and contracts: what exists, what invariants hold, what other systems depend on. Ground every claim in code you read or history you checked; a baseline is worthless if it guesses. Reference concrete files only where the file is the contract (a schema, a versions manifest).

6. **Deliver as a PR.** Branch, commit the `openspec/` tree, `gh pr create`, documentation-only, no code changes. The PR body states the baseline is a starting point and invites corrections from the people who know the system.

## Rules

* Never bundle adoption with a functional change; the baseline gets reviewed on its own.
* Never write a baseline for a repo you have not read; if the repo is too large to ground properly, propose fewer domains and say what was left unspecified.
* Specs describe behavior and contracts, not implementation walkthroughs.
