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

Two shapes. **Flat** is the default: one fence, one agent. **Chunked** is for
orders the slicing rubric sliced ([references/slicing.md](../references/slicing.md)):
one header fence plus one fence per sub-order, all in the same comment. Every order
of either shape carries a `Review depth:` line
([references/review-depth.md](../references/review-depth.md)).

Every fence also carries `Surface lifecycle:`. Use `none` when no rendered surface
changes, `build` for a greenfield or accepted-fallback lock, and `revise` for a
shipped surface whose behavior ledger and replay remain its contract. The chunked
header carries the one active lifecycle across the whole diff (`none` only when all
chunks say `none`); each sub-order names its own route so the fence remains
executable without coordinator commentary. One ticket does not mix `build` and
`revise`: split those into separate tickets rather than inventing a fourth state.

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
WORK ORDER <ticket-id>: <ticket summary>
Open as: <model> / <effort>.
Execution: single agent.

Classification: <code | investigation | manual>
Surface lifecycle: <none | build | revise>
Repo(s): <org/repo> (branch from the default branch)
Verification: <the command that verifies this change>
Expectation: <what that command must report before the pull request opens>
Review depth: <focused | targeted | full> (<one-line reason>)

Context
<2-5 bullets: what exists today, what constrains this change, decisions already made
 (from the scoping interview or repo history) that the implementation must respect>

Do
<numbered, concrete steps: files, targets, resources, workflows. Name what to create,
 what to modify, and what must not change.>

Done when
<observable acceptance: verification output, CI green, specific behavior. Not "works".>

Boundaries
* Iterate the verification step locally; open the pull request when it matches the expectation.
* Record the change where this repo already records changes.
* Stop at the pull request. Do not merge. Do not touch <explicitly out-of-scope things>.
```

---

## Chunked

Same comment, same attribution and summary. The summary gains one bullet naming how
the work is split and why. Then the header fence, then each sub-order fence in
execution order.

## Work order

```
WORK ORDER <ticket-id>: <ticket summary>
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

Why sliced
<the rubric traits that fired, one line each, and the anchor row this matches>

Context
<2-5 bullets shared by every chunk: what exists today, what constrains the change,
 decisions already made that all chunks must respect. Chunks repeat what they need;
 this section is not a substitute for a sub-order standing alone.>

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

Context
<everything this chunk needs to stand alone in a fresh agent. Never "as established
 in chunk 1".>

Do
<numbered, concrete steps scoped to this chunk only>

Done when
<observable acceptance for this chunk alone>

Boundaries
* Touch only <files/targets this chunk owns>. Another chunk owns <the rest>.
* A parallel chunk must not implement, revise, or depend on this chunk's private
  capability. Name any shared contract and its one owning sub-order instead.
* Do not record the change; the coordinator owns that.
* Commit on this chunk's branch. Do not open a pull request, do not merge.
```
