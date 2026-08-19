# ADR 48 — Never mock a surface that already exists

Date: 2026-08-19
Status: accepted
Issue: https://github.com/ConnorGriffin/skills/issues/48
Ledger: `docs/scope/ui-craft-shipped-surface-iteration.md`

## Context

`ui-craft`'s `lock` mode treats a mockup tournament as the default entry point
for every surface, shipped or not. A surface that already exists therefore gets
rebuilt from scratch as HTML, reviewed, locked, and only then ported back into
the app.

That inverts the default that makes review work. In the shipped app a behavior
survives unless someone deletes it, and the deletion is a diff line with an
author. In a from-scratch mock a behavior exists only if someone rebuilds it,
and **absence has no representation**: nothing is emitted, nothing is diffed,
nothing is reviewed. Every checker in the lifecycle compares things that are
present, so all of them are blind in the same direction.

The failure is measured, not hypothetical. harmonic's
`mockups/finding-evidence-routing.behavior.md` records 55 behaviors of a shipped
Diagnose surface driven against a real browser engine: 12 kept, **43 missed**,
0 sanctioned. Ten exploration rounds, a persona panel and a 52-run technical
audit all passed, and a 60-term lock froze those 43 retirements as contract
(harmonichq/harmonic#40, retracted by #44). A human caught it by looking at a
screenshot. Seventeen of the misses were one drag-to-draw selection window.

`ui-craft`'s predecessor inventory (branch `ui-craft/predecessor-inventory`)
makes a mock survivable by running one pass that reads the other artifact. It
patches the inversion; it does not remove it.

## Decision

A surface the app already ships is revised by **iterating the running app on a
branch**. Building a from-scratch mock of a shipped surface is banned.

- The work lands as a new `ui-craft` mode, **`revise`**, beside `lock`. `lock`
  refuses on a surface with a shipped embodiment and names `revise`.
- The frozen contract is the **behavior ledger plus its replay script, run
  against the built app**. No lock manifest is pinned to an app template.
- The shipped surface gets **one full behavior inventory, frozen**, on its first
  revision; later changes diff against it. It runs **before** the design
  conversation, so the design is drawn against what exists.
- Throwaway wireframes stay legitimate for **divergent** exploration, including a
  new view inside a shipping shell. They live in the change's own decision record
  (an OpenSpec change folder where the repo uses one, otherwise
  `docs/scope/<slug>/`), carry no fidelity claim, are never lockable, and are
  deleted when the change lands. Only screenshots survive.
- The wireframe phase is **interactive**: the human and the agent work it
  together in the code. An unattended fleet run never takes it on a surface whose
  shell already ships. When the decisions settle, an agent lifts the wireframe
  into a branch or worktree of the app and iteration continues there under a
  fresh behavior sweep.
- App-branch iteration requires the repo to **declare a safe dev-server
  entrypoint** in its `CLAUDE.md`/`AGENTS.md` that names its data source. An
  agent refuses to start the app on any ambiguity. Absent that declaration, the
  round falls back to mockup plus the predecessor sweep, which is retained for
  exactly this case.

## Consequences

- A dropped behavior becomes a diff line with an author again, which is the
  property the mock path cannot provide at any review depth.
- Repos that cannot run their own app safely keep the weaker path, and the cost
  of that is now visible rather than implicit.
- The predecessor inventory stops being load-bearing wherever `revise` applies,
  and stays load-bearing everywhere else.
- harmonic cannot use `revise` until its own prohibition on starting the app is
  narrowed to the synthetic path and a provenance-stamped synthetic database
  exists. Both are harmonic-side and operator-owned.
- The mode owes one real end-to-end run on a shipped surface before it ships;
  prose that has never been executed is a plan, and the last contract this pack
  wrote passed every gate while being wrong.
