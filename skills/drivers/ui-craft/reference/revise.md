# Mode: revise

Revise a surface the app already ships by changing the running app on a branch.
**Never rebuild that surface as a from-scratch mock.** In the app, a behavior
survives unless the diff deletes it; in a mock, absence has no representation.

The contract is the surface's frozen **behavior ledger** plus its replay script,
run against the built app. The branch is the visual artifact. Review screenshots
record what changed, but no lock manifest or fidelity ledger is pinned to an app
template.

Before changing CSS or JavaScript/TypeScript, read
[web-implementation.md](web-implementation.md); it governs web mechanics while this
mode's behavior ledger and rendered evidence remain binding.

This mode is for a shipped embodiment of the surface, including a new view inside
a shell that already ships. A wholly greenfield surface uses `lock`.

## Route map

- [Review mode](#review-mode)
- [0. Prove the app is safe to start](#0-prove-the-app-is-safe-to-start)
- [1. Establish the base](#1-establish-the-base)
- [2. Freeze shipped behavior before design](#2-freeze-shipped-behavior-before-design)
- [3. Choose convergent or divergent work](#3-choose-convergent-or-divergent-work)
- [4. Iterate the running app](#4-iterate-the-running-app)
- [5. Review and land](#5-review-and-land)

## Review mode

- **Interactive:** the human and agent may explore divergent wireframes together,
  then iterate the app branch live.
- **Headless (AgentFlow):** go straight to an app branch. Never start a divergent
  wireframe phase for a surface whose shell ships. If the work cannot be settled
  without that conversation, stop and return the decision rather than inventing
  it.

## 0. Prove the app is safe to start

Read the repo's `CLAUDE.md` / `AGENTS.md` before running any server. App-branch
iteration is allowed only when that file declares:

1. the exact safe dev-server entrypoint; and
2. the data source that entrypoint reads.

Resolve the named source before starting the process. For `revise`, it must be a
manufactured fixture or synthetic database. A command that may read real,
production or authoritative data, fetch from a vendor, select a database
implicitly, or leave the source ambiguous is unsafe. **Do not run it to discover
what it does.** This mode's stricter risk contract overrides any repo-scoped
real-data inversion used for other evidence.

Record the declaration path, quoted command, named data source, and source
provenance in the change's decision record.

- **No dev-server declaration:** record the accepted fallback and run
  `lock`'s mockup flow plus `behavior-sweep`'s predecessor inventory. This is the
  only path by which `lock` may accept a shipped surface. The record says that
  the result is weaker because absence is visible only through the predecessor
  pass. Fallback does not authorize starting the app; any live predecessor
  evidence must already satisfy a separately declared safe harness.
- **The app cannot run locally at all, or a declared entrypoint names no data
  source:** `revise` is unsupported. Do not start the app and do not improvise a
  new entrypoint. An incomplete declaration is not the same as no declaration.
- **The declaration is ambiguous:** stop. Ambiguity is not permission and is
  never resolved by a trial run.

## 1. Establish the base

Fetch the default branch, branch or create a worktree from its exact tip, and
record the base SHA. The revision changes the real app in place; never build a
duplicate route that carries a second implementation of the surface.

When live before/after comparison matters, use `spin-worktree` to serve the base
branch from a second worktree. Give the two servers distinct ports and the same
safe data bytes. A second route inside the revision branch is not a comparison:
it duplicates the surface and can drift with it.

Capture the base surface at every state, viewport and theme the change may touch.
Screenshots stay in the change's decision record or its external review evidence;
sensitive renders obey SKILL.md's publish rules.

## 2. Freeze shipped behavior before design

Run `behavior-sweep` against the **base app**, before discussing a replacement
layout or writing a wireframe. On the surface's first revision, make one full
source-and-live inventory and freeze it as:

- `mockups/<surface>.behavior.md`; and
- `frontend/<surface>-behavior.replay.mjs`, or the repo's equivalent test path.

The directory name does not turn the ledger into a mock: no mock artifact exists
on this path. The replay script has an app opener only and runs every story
against the built app. Create `mockups/INDEX.md` if absent and register the
shipped surface, ledger and replay path there.

On every later revision:

1. replay the frozen ledger against the base app;
2. inventory the base source and live surface again;
3. diff the observed inventory against the ledger; and
4. amend and re-freeze the ledger before design.

New shipped behavior becomes a STORY with a replay function. A ledger story no
longer present on the base is an unsanctioned retirement until a named person
rules it with the date and their quoted reason. This is how a stale inventory is
caught at the next revision rather than silently trusted.

No design conversation starts while a story is unreplayable, an observed
behavior has no story, or a retirement lacks its sanction. The QUESTION round in
`behavior-sweep` owns those decisions.

## 3. Choose convergent or divergent work

**Convergent work** changes the app branch directly: refinements within the
shipping surface's current information and interaction model, or a direction the
work order has already settled.

**Divergent work** may use throwaway wireframes, including for a new view inside
the shipping shell, under all of these constraints:

- human and agent work the wireframe together; it is never an unattended phase;
- it lives in the change's own decision record — its OpenSpec change folder when
  the repo uses OpenSpec, otherwise `docs/scope/<slug>/`;
- it never lives in `mockups/`;
- it says `WIREFRAME — NO FIDELITY CLAIM — NOT LOCKABLE` at its top;
- it may explore structure and interaction, but makes no claim to match the app;
  and
- the runnable wireframe is deleted when the change lands. Only screenshots and
  the decisions they evidence survive.

Do not run `lock` on the wireframe, produce a lock manifest for it, or cite it as
fidelity evidence. A wireframe is a conversation aid, not a second surface.

### Running the rounds

Interactive divergent work only. The headless rule above stands: a headless
session never opens this phase, and a direction it cannot settle is returned as
a decision rather than invented.

The constraints above say what a wireframe is. These say how the conversation
converges, so that iterating in the running app is never how direction gets
settled:

- **One question per round.** Each round narrows what the next may ask, and
  nothing ruled reopens. A round that asks two questions gets an answer to
  neither.
- **Options differ in concept, not decoration** — five ways to site a control,
  not five colors of one control. Render every option live under the coverage
  §1 already requires, plus the element sizes the option itself varies, and give
  each state its own specimen: a small tile at rest is not evidence about a
  large one being held.
- **Every option carries a stated cost, the recommended one included.** An
  option offered as free is one whose cost has not been found yet, and it wins
  the round on an omission.
- **Measure the claim instead of asserting it, and own a wrong measurement out
  loud.** A retracted number costs one round; an unretracted one is believed for
  the rest of the change.
- **The operator's eye outranks the measurement when the metric measures the
  wrong thing.** An area-blind contrast ratio is a correct number answering a
  question nobody asked. Say which of those is happening rather than arguing the
  number.
- **Build only after the direction is ruled.** That is what moves review from
  "is this right", which the rounds settle, to "is this broken", which the app
  branch and the frozen stories settle.

When the decisions settle, lift them into the app branch or worktree and continue
there. Re-run the behavior sweep against the base app immediately before the
lift, so the branch starts from a fresh frozen contract.

## 4. Iterate the running app

Serve the revision branch through the declared safe entrypoint and inspect it in
a real browser. Use the app's shipping tokens, components, chart library and data
shape; do not translate the wireframe's temporary styling into a new design
system.

Work in short, reviewable rounds:

1. change the app branch;
2. replay every frozen story against the built app;
3. render the affected states, viewports and themes;
4. compare them with the base-worktree renders; and
5. take the running branch to the human for the next decision in interactive
   mode.

The replay must report its applicable story count. Zero stories, a missing
driver, an unstubbed request, or a story that does not reach the requested state
is failure, never skip.

### Behavior changes

- **Preserved:** the existing story and replay function stay green.
- **Added:** add a STORY and replay function in the same change.
- **Changed:** amend the STORY, record the dated decision under the frozen
  header, and prove the old replay fails before the new one passes.
- **Retired:** require `sanction: <person> · <date> · "<their reason>"`, retain a
  permanent RETIRED entry, and replace the positive replay with an absence
  assertion that prints the sanction on every run. Record the premise the ruling
  reasoned from on the entry, so that assertion can assert it too
  (`behavior-sweep`).
- **Moved:** a behavior that changed which surface owns it owes the same
  ceremony as a removal, and lands as an amended STORY rather than a retirement
  — the behavior still ships, so it keeps its entry and its replay, and no
  sanction is owed. Name the fact, the surface it left, the surface it landed
  on, and update every story that reads it in the same change, so the next
  revision's inventory finds it where it now lives instead of reading its
  absence from the old surface as an unsanctioned retirement. A move is the case
  that looks like nothing happened: the app is right, the behavior is intact,
  and the stories still reading the old surface were not wrong when they were
  written and nobody was told they had become wrong.

A dropped, changed or moved behavior without that record blocks the revision.
There is no lock term to `resettle`; the ledger amendment is the decision
record.

A move, a duplication or a rename also widens what the round owes outside the
ledger, because each of them changes what an existing assertion means without
changing its text:

- **A second instance of an existing element under-specifies every selector that
  names it.** Once a fact renders twice, a locator meaning "the element for this
  item" matches both, and the locators do not all mean the same thing — some
  meant the first instance, some the second, some "wherever this lives now",
  readings that were indistinguishable while there was one copy. Re-read each
  one's intent; find-and-replace picks a reading for you, silently, and breaks a
  different set.
- **A surface that can be conditionally absent invalidates every assertion using
  it as a presence proxy.** Re-read them including the fallback paths that have
  never executed: a dead branch in a replay driver is invisible until the day the
  proxy starts failing, and it then runs against selectors the same change
  deleted.
- **A rename's blast radius is the repository, not the directory.** A name
  outlives the fact it names, and a consumer outside the swept directory surfaces
  as a type error inside a gate rather than anywhere near the edit.

## 5. Review and land

The PR evidence includes:

- the frozen behavior ledger, with the base SHA and data provenance;
- raw replay output against the built revision, including the story count and
  every retirement sanction;
- before/after renders from the base and revision worktrees for every affected
  state, viewport and theme; and
- the decision-record screenshots for any divergent wireframe, with the
  wireframe itself deleted.

Review the running app, not source alone. Run the repo persona sweep when one
exists, then `audit` and `polish` against the revision branch. A visual change is
judged against the stated decision and the before/after renders; it does not
invent a lock manifest after the fact.

Before landing, confirm:

- every frozen story replayed against the built app;
- for any round that moved a surface, the gates that replay those stories have
  actually run, launched by whoever can launch them. An agent whose sandbox
  cannot start a browser has no signal about the surface it just moved, and the
  suites that do run there staying green is not one;
- every added, changed or moved behavior is represented in the ledger;
- every retirement has a dated, named, quoted sanction, a recorded premise, and
  a loud absence test asserting both;
- no wireframe or duplicated comparison route survives; and
- the safe-start declaration and exact data source still match what produced the
  evidence.

The updated ledger and replay script run against the app from then on. A later
change made outside `revise` is not repaired automatically; the next revision's
base diff exposes it.
