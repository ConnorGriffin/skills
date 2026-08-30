# Work order template

Post as one ticket comment. The quote block, the human summary, and the headings
sit outside the fence. The fence is the executable brief and must stand alone.

The binding decides the comment's markup ([the tracker contract](../references/tracker-contract.md)).
The shapes below are written in markdown, which is what the GitHub issues binding
posts; another binding converts the same substance to its own markup and keeps the
fence a fence.

The human summary comes before the fenced order and is written for a teammate, not
an agent: lead with what the work gets us in one sentence, then short plain-English
bullets (one per major piece of the order, stating what happens and why in domain
terms, no file paths or resource type names), and close with a "not in this ticket"
bullet naming the sibling work. Match the order's substance exactly; it is a
translation, not a second spec.

## The execution lock

Every posted order is an **EXECUTION LOCK v2** envelope: `Source:` names where the
durable plan lives and at what exact commit, and the fence itself carries only what
that source cannot — explicit human authorization to execute, which revision is
authorized, session and model fit, execution shape and chunk ownership,
verification, review depth, the expected diff, and the stop-at-pull-request
ceiling. `<lock-id>` on the version line is a plain positive integer, unique within
the ticket: 1 for that ticket's first lock, and one more than the highest
`<lock-id>` already posted on it for every lock that supersedes a prior one. A
legacy `WORK ORDER` carries no `<lock-id>`, so it contributes no number to that
maximum: the first lock superseding a legacy order is that ticket's first lock and
reads 1. It exists so a reader can tell two locks
on the same ticket apart; it plays no role in which comment is newest — that is
comment post time, per [the tracker contract](../references/tracker-contract.md).
The envelope has one grammar and three source modes:

* **`openspec <change-path>@<full-commit-oid>`** — the plan is an OpenSpec change on
  the ticket branch at that full commit. `Selected tasks:` and
  `Acceptance anchors:` are plain positional numbers (no inline ID markers, no
  hashes) resolved against the pinned commit's `tasks.md` checklist and spec-delta
  requirements. Whole-change ownership is a property of the ticket, not of each
  fence: an ordinary ticket owns its whole change, an epic child owns a subset of
  its shared parent change, and a flat lock's own `Selected tasks:` reads `all`
  (ordinary) or that subset (epic child). A chunked lock's header `Selected tasks:`
  reads the same value, and its sub-locks partition it: each sub-lock's own
  `Selected tasks:` and `Acceptance anchors:` are a disjoint slice of the header's
  selection, and the sub-locks together cover exactly what the header selected —
  no more, no less.
* **`repository-native <path>@<full-commit-oid>`** — the plan is some other versioned,
  reviewable artifact this repository already keeps (a design doc, a checklist) at
  that exact commit. `Selected tasks:` and `Acceptance anchors:` are that artifact's
  own positional numbering, resolved the same way.
* **`inline`** — there is no durable plan record; the fence carries today's full
  `Context` / `Do` / `Done when` payload verbatim as its body, unchanged from the
  pre-lock work order. `Selected tasks:` and `Acceptance anchors:` do not apply and
  are omitted.

`openspec` and `repository-native` both pin exact bytes; a consumer resolves the
commit, confirms the selected tasks and anchors exist at those bytes, and refuses
rather than substituting the branch head or a nearby commit. Amending the pinned
source after the lock is posted requires posting a newer lock; nothing re-derives
authorization from an unpinned edit.

Two shapes. **Flat** is the default: one fence, one agent. **Chunked** is for
orders the slicing rubric sliced ([references/slicing.md](../references/slicing.md)):
one header fence plus one sub-lock fence per sub-order, all in the same comment.
Every fence of either shape carries a `Review depth:` line
([references/review-depth.md](../references/review-depth.md)).

Every fence also carries `Surface lifecycle:`. Use `none` when no rendered surface
changes, `build` for a greenfield or accepted-fallback lock, and `revise` for a
shipped surface whose behavior ledger and replay remain its contract. The chunked
header carries the one active lifecycle across the whole diff (`none` only when all
chunks say `none`); each sub-lock names its own route so the fence remains
executable without coordinator commentary. One ticket does not mix `build` and
`revise`: split those into separate tickets rather than inventing a fourth state.

Every flat and chunked-header fence also carries `Profile:`. Use `hardening` only
for a flat order whose target repo declares `Harden:`; use `none` otherwise,
including every chunked order. A `QA script` follows `Done when` in the flat
fence only when the profile is `hardening`: numbered Given/When/Then steps a
human follows in the running app to confirm that clause.

## Two authoring checks before the draft leaves triage

* **Wiring table.** Every value the order names (an environment variable, an input,
  an output, a file, a flag) has both a producer and a consumer stated in the order.
  Anything named once is a defect in the draft, not a detail for the implementer. In
  one measured review, all six round-one blockers were this single class: a thing
  named in one place with no counterpart anywhere.
* **Executable logic is spiked, not prosed.** When the order depends on executable
  logic (a regex, a shell fragment, a workflow expression, a query), write the
  artifact in the worktree now, run it, commit it, and have the order reference it. A
  scratch file with a table test is enough. Prose in the order states intent; the
  literal lives only in executed code. An order that pins literals in markdown is an
  implementation nothing can compile, and review rounds against it find defects one
  at a time that a test run finds at once.

---

## Flat

> Written by an AI agent operating for `<operator>`. Verify before relying on it.

## Summary

`<one sentence: what the work gets us>`

* `<plain-English bullet per major piece: what happens and why>`
* `<...>`
* Not in this ticket: `<sibling work, with ticket ids>`

## Work order

Before filling either shape, apply
[brief quality](../references/brief-quality.md). It is a drafting checklist, not
an extra ticket-comment format.

```
EXECUTION LOCK v2 <ticket-id> <lock-id>
Source: <openspec <change-path>@<full-commit-oid> | repository-native <path>@<full-commit-oid> | inline>
Open as: <model> / <effort>.
Session fit: <selected execution row's Ladder value, with each model's display name in ladder order>. A Claude or Codex session whose system-prompt model is named in this paragraph at or above the selected rung proceeds directly to step 4, skipping the remainder of Model-check and without asking about model fit or effort.
Execution: single agent.

Classification: <code | investigation | manual>
Surface lifecycle: <none | build | revise>
Repo(s): <org/repo> (branch from the default branch)
Verification: <the command that verifies this change>
Expectation: <what that command must report before the pull request opens>
Review depth: <focused | targeted | full> (<one-line reason>)
Profile: <none | hardening>

Drafting conventions: Read `skills/drivers/ticket/references/drafting-conventions.md` before acting on this order.

Selected tasks: <all (ordinary ticket) or the epic-child's owned subset, as positional numbers from the pinned source's numbered tasks; omit when Source is inline>
Acceptance anchors: <positional requirement/scenario numbers from the pinned source that this lock selects; omit when Source is inline>

Context
<2-5 bullets: what exists today, what constrains this change, decisions already made
 (from the scoping interview or repo history) that the implementation must respect.
 Present for every Source; for openspec and repository-native, this is orientation
 only — the pinned source is the authority, not a restatement of it.>

Do
<present only when Source is inline: numbered, concrete steps: files, targets,
 resources, workflows. Name what to create, what to modify, and what must not
 change. For openspec and repository-native, the pinned source's tasks are the Do
 steps; nothing here duplicates them.>

Done when
<observable acceptance: verification output, CI green, specific behavior. Not
 "works". For openspec and repository-native, this is the lock's own delivery
 acceptance only — the verification command's expectation and the
 stop-at-pull-request condition — never a restatement of the pinned source's own
 acceptance criteria; that criteria lives at the pinned commit, and only the
 executing agent's later verification checks it.>

Expected diff
<closed allowlist of repository-relative paths this order may touch. No escape
 clause: a path not listed here is out of scope, whichever Source mode is active.>

QA script
<present only when Profile is hardening: a human follows these numbered steps in
 the running app to confirm Done when.>
1. Given <starting state and fixture>
2. When <human action>
3. Then <observable acceptance>

Boundaries
* Iterate the verification step locally; open the pull request when it matches the expectation.
* Execute the selected tasks and acceptance anchors only (openspec, repository-native) or the Do steps only (inline); do not expand scope beyond the pinned source.
* Record the change where this repo already records changes.
* Stop at the pull request. Do not merge. Do not touch <explicitly out-of-scope things>.
```

---

## Chunked

Same comment, same attribution and summary. The summary gains one bullet naming how
the work is split and why. Then the header fence, then each sub-lock fence in
execution order.

## Work order

```
EXECUTION LOCK v2 <ticket-id> <lock-id>
Source: <openspec <change-path>@<full-commit-oid> | repository-native <path>@<full-commit-oid> | inline>
Open as: <orchestrator model> / <effort>.
Execution: chunked, <n> sub-orders (<n> parallel, <n> serial).
Launch: open a session at the model above and run `/ticket start <ticket-id>`.
        It loads /orchestrate and coordinates the sub-orders itself.

Classification: <code | investigation | manual>
Surface lifecycle: <none | build | revise>
Repo(s): <org/repo> (one ticket branch, one pull request)
Verification: <the command that verifies the merged branch>
Expectation: <what that command must report before the pull request opens>
Review depth (whole diff): <targeted | full> (<one-line reason>)
Profile: <none | hardening>

Drafting conventions: Read `skills/drivers/ticket/references/drafting-conventions.md` before acting on this order.

Why sliced
<the rubric traits that fired, one line each, and the anchor row this matches>

Selected tasks: <all (ordinary ticket) or the epic-child's owned subset, as positional numbers from the pinned source's numbered tasks — the whole selection every sub-lock below partitions; omit when Source is inline>
Acceptance anchors: <positional requirement/scenario numbers from the pinned source that this lock selects — the whole selection every sub-lock below partitions; omit when Source is inline>

Context
<2-5 bullets shared by every chunk: what exists today, what constrains the change,
 decisions already made that all chunks must respect. Chunks repeat what they need;
 this section is not a substitute for a sub-lock standing alone. Present for every
 Source; for openspec and repository-native this is orientation, not a restatement
 of the pinned tasks.>

Done when (whole ticket)
<observable acceptance for the merged branch, not per chunk>

Boundaries
* One ticket branch, one pull request. Chunks land on per-chunk branches cut from it
  and merge back.
* Only the coordinator records the change.
* Stop at the pull request. Do not merge. Do not touch <explicitly out-of-scope things>.
```

```
SUB-ORDER 1/<n> <ticket-id>: <chunk title>
Mode: parallel | serial after <n>
Agent: <haiku | sonnet | opus>
Surface lifecycle: <none | build | revise>
Review depth: <focused | targeted | full> (<one-line reason>)
Capability owned: <one coherent capability; exactly one sub-order owns it>
Shared contracts owned: <none | each named contract this sub-order owns>

Drafting conventions: Read `skills/drivers/ticket/references/drafting-conventions.md` before acting on this order.

Selected tasks: <this sub-order's disjoint positional slice of the header's Selected tasks; every sibling sub-lock's slice is disjoint from this one, and together they cover the header's whole selection; omit when the header's Source is inline>
Acceptance anchors: <this sub-order's disjoint positional slice of the header's Acceptance anchors, on the same terms; omit when the header's Source is inline>

Context
<everything this chunk needs to stand alone in a fresh agent. Never "as established
 in chunk 1". For openspec and repository-native, this is orientation onto the
 pinned source's selected tasks, never a restatement of them.>

### Session fit

Session fit: <the selected execution row's Ladder value, with each model's display name in ladder order>; selected Agent rung: <Rung>. A Claude or Codex coordinator whose system-prompt model is named in this paragraph at or above the selected Agent rung proceeds directly to step 4, skipping the remainder of Model-check and without asking about model fit or effort.

### Builder self-check

Before declaring the change ready, run each check below.

1. **External surface by execution.** Before coding against a CLI or API surface, run `--help` or a probe call against that surface; do not infer flags, arguments, or behavior from memory.
2. **Fail-first tests.** Before production edits, run every new test against the pre-change behavior or a deliberately broken variant and observe the expected failure. A fake that accepts every input or a mock of the function under test is not evidence.
3. **Boundaries by execution.** Prove a security or confinement claim by attempting the forbidden action in a real run; configuration inspection alone is not evidence.
4. **Post-fix sweep.** After each late fix, sweep its affected path for uncalled symbols, dead parameters, and prose that still describes the pre-fix behavior.

Do
<present only when the header's Source is inline: numbered, concrete steps scoped
 to this chunk only. For openspec and repository-native, this sub-lock's Selected
 tasks are the Do steps; nothing here duplicates them.>

Done when
<observable acceptance for this chunk alone. Under the header's openspec or
 repository-native Source, this is the lock's own delivery acceptance only —
 verification and stop-at-pull-request — never a restatement of the pinned
 source's acceptance criteria for this sub-lock's selected tasks.>

Expected diff
<this sub-order's closed allowlist of repository-relative paths. No escape clause,
 and disjoint from every parallel sub-order's allowlist.>

Boundaries
* Re-read `ORDER.md` before each commit and again before declaring the work done;
  `Done when` is closed, so when it is met stop and report, and propose any further
  improvement rather than making it. If `ORDER.md` cannot be found or read, stop and
  report rather than continuing from memory.
* Touch only <files/targets this chunk owns>. Another chunk owns <the rest>.
* Execute the selected tasks and acceptance anchors only (openspec, repository-native) or the Do steps only (inline); do not expand scope beyond the pinned source.
* A parallel chunk must not implement, revise, or depend on this chunk's private
  capability. Name any shared contract and its one owning sub-order instead.
* Do not record the change; the coordinator owns that.
* Commit on this chunk's branch. Do not open a pull request, do not merge.
```
