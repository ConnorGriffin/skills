# Scope ledger — ui-craft: never mock a surface that already exists

Routed: scope → interview mode (2026-08-19). Proposal, accepted in conversation
and not yet recorded anywhere: a surface that has already shipped is changed by
iterating the running app on a branch, not by rebuilding it as a from-scratch
mockup. Mockups survive only for divergent throwaway exploration, carry no
fidelity claims, and are never lockable.

Tracking issue: https://github.com/ConnorGriffin/skills/issues/48

Origin: handoff from the harmonic session that produced
`mockups/finding-evidence-routing.behavior.md` (55 rows: 12 kept, 43 missed) and
PR harmonichq/harmonic#44, which retracted a 60-term lock that had frozen those
43 retirements as contract.

## The reasoning that must survive

A from-scratch mock inverts the default. In the shipped app a behavior survives
unless someone deletes it, and the deletion is a diff line with an author. In a
mock a behavior exists only if someone rebuilds it, and **absence has no
representation**. Every checker in the lifecycle compares things that are
present, so none of them could see 43 behaviors that were never built.

## Grounding facts (verified this session)

- `harmonic serve --no-fetch --db <path>` exists and does what the handoff
  claims: `ciq_autotune/cli.py:119` defines the flag ("skip the startup
  live-fetch (safe for scratch/synthetic DBs)"), `ciq_autotune/api.py:94-95`
  gates the hourly fetch loop on it. Not run end to end — verified by reading.
- harmonic `CLAUDE.md` forbids `harmonic serve` / `harmonic fetch` in automated
  work with no carve-out for a synthetic DB. Operator-owned to amend; not
  amended, and `serve` not run.
- No synthetic `.db` exists in the harmonic tree. `mockups/*.synthetic/` holds
  captures and JSON payloads only.
- **Handoff claim refuted:** ui-craft's `lock` reference does not distinguish
  `local` from `surface` scope. The only "scope" in the pack is CSS scoping
  (`skills/ui-craft/reference/build.md:24-27`). That candidate for the
  divergent/convergent boundary does not exist and cannot be reused.
- Branch `ui-craft/predecessor-inventory` (`f68c8d4`, `2e6fb4b`) is local and
  unpushed. It adds the predecessor inventory to `behavior-sweep` §2, gates the
  lock on it (`lock.md` §9.3), makes RETIRED entries replay in `build`, and
  routes a post-lock `missed` verdict to `resettle`. It patches the inversion;
  it does not remove it.

## Decisions

- Route to interview mode: the proposal is concrete, accepted, and untested;
  its shape (mode vs. lock branch, contract artifact, preconditions) is not
  designed. `inline`
- **The core rule.** A surface the app already ships is revised by iterating the
  running app on a branch. A from-scratch mock of a shipped surface is banned,
  because absence has no representation in a mock and every checker in the
  lifecycle reads only what is present. (why: 43 unruled retirements survived
  ten rounds, a persona panel and a 52-run audit) `→ ADR`
- **Q1 = A.** The rule lands as a **new mode beside `lock`**, with its own flow
  against an app branch. `lock`'s scaffold, variant fan-out and delete-losers
  steps have no counterpart there. Working name: `revise` (operator may
  overrule). `→ issue #48`
- **Q2 = B.** With no mock, the frozen contract is the **behavior ledger plus
  its replay script, run against the built app**. No lock manifest is pinned to
  an app template. (why: the only artifact with a working precedent, harmonic's
  28 stories under `TARGET=app`) `→ issue #48`
- **Q3 = A.** Merge `ui-craft/predecessor-inventory` as is. It becomes the
  **fallback path** for repos that cannot run their own app safely, not dead
  weight. (why: narrowing it later is cheaper than un-dropping it) `→ issue #48`
- **Q4, partial.** A partly-new surface (new view inside a shipping shell)
  **starts divergent and ends convergent**: throwaway wireframes are legitimate
  for exploring the new view, and porting the winner into the shipping shell is
  **interactive work with a human in the session, not AFK**. Transition point and
  headless availability still open (Q6, Q7). `→ issue #48`
- **Q5 = A.** App-branch iteration requires the repo to **declare a safe
  dev-server entrypoint** in its `CLAUDE.md`/`AGENTS.md`. Absent that
  declaration, the round falls back to mockup plus predecessor sweep. (why:
  harmonic has the capability and a blanket prohibition against using it, so an
  agent reading the repo today would get it wrong) `→ issue #48`
- **Q6.** The wireframe is **scratch inside the change's own decision record**,
  not a deliverable. Sanctioned path: open a change (OpenSpec change folder where
  the repo uses one, as harmonic does), keep a decision ledger in it, build the
  wireframe there, and work it interactively with the agent. When the decisions
  settle the change becomes a plan, an agent **lifts the wireframe into a clone of
  the app**, and iteration continues there under a fresh behavior sweep. Human and
  agent are in the code together throughout. `→ issue #48`
- **Q7 = A.** Unattended fleet runs never take the wireframe route on a surface
  whose shell already ships; they go straight to the app branch. Greenfield
  surfaces are untouched by this. `→ issue #48`
- **Q8 = A.** The shipped surface gets **one full behavior inventory, frozen**, on
  its first revision; later changes diff against it. `→ issue #48`
- **Q9 = A.** An agent refuses to start the app unless the repo's declared
  entrypoint names its data source, and stops on any ambiguity. This is the
  must-prevent: no run that might be reading real or authoritative data.
  `→ issue #48`
- **Q10 = A.** harmonic narrows its prohibition to permit the synthetic path
  explicitly, naming the flag and the database, gated on one supervised run
  proving no vendor contact. `→ issue` (harmonic)
- **Q11 = A.** In a repo with no change folder, the wireframe lives beside the
  scope ledger in `docs/scope/<slug>/`, never in `mockups/`. `→ issue #48`
- **Q12 = A.** The wireframe is deleted when the change lands; only screenshots
  survive in the record. (why: a runnable artifact that outlives the change is a
  second source of truth) `→ issue #48`
- **Q13 = A.** The lift target is a branch or worktree of the app, changed in
  place. Live comparison comes from serving the base branch in a second worktree
  (`spin-worktree`), not from a duplicated route inside the app. `→ issue #48`
- **Q14 = A.** The frozen inventory runs **before** the design conversation, so
  the wireframe is drawn against what already exists. `→ issue #48`
- **Q15 = A.** `lock` refuses on a surface with a shipped embodiment and names
  `revise`. Same class of error as a `missed` verdict. (why: `lock` step 0
  already detects a shipped predecessor for chrome ground truth) `→ issue #48`
- **Q16 = A.** The mode is called **`revise`**. `→ issue #48`
- **Q17 = B.** The change ships gated on one real end-to-end run of `revise` on a
  shipped surface, with that run's behavior ledger attached. `→ issue #48`

### Risk contract

- **Must prevent:** an agent starting a repo's app against real, authoritative or
  vendor-connected data; a wireframe treated as a fidelity artifact or a lock
  target; a shipped behavior dropped without a dated sanction naming a person and
  quoting their reason.
- **Must recover:** nothing automatically.
- **Accepted failure:** a repo with no declared entrypoint falls back to mockup
  plus predecessor sweep, which is slower and weaker, and that cost is visible
  rather than silent. A frozen inventory that goes stale because the surface
  changed outside `revise` is caught by the next revision's diff, not
  automatically.
- **Unsupported:** surfaces whose app cannot be run locally at all; any repo whose
  declared entrypoint does not name its data source.
- **Evidence owed:** the structural validator, plus one real end-to-end `revise`
  run on a shipped surface with its behavior ledger and replay output attached to
  the PR.
- **Why:** the mode instructs agents to start real applications, and this pack's
  rules ship into a repo producing advisory insulin-dosing guidance.
- **Disposition:** copied verbatim into issue #48 at admission.

- ADR home: this repo has no `docs/adr/` and no OpenSpec, so the charter default
  applies: `docs/adr/adr-48-never-mock-a-shipped-surface.md`. `inline`

## Open questions

- None. Frontier empty as of 2026-08-19.

## Spawned tasks

- harmonic: narrow the `serve`/`fetch` prohibition per Q10, gated on a supervised
  no-vendor-contact run. Not yet filed.
- harmonic: committed generator + provenance-stamped synthetic `.db`. Gates any
  harmonic use of this rule. Not yet filed.
- Issue #48 is the durable home; frozen brief and risk contract copied into it.
- ADR written: `docs/adr/adr-48-never-mock-a-shipped-surface.md`.
- Push and open a PR for `ui-craft/predecessor-inventory` (Q3 = A). Operator's
  call to publish; not pushed.
