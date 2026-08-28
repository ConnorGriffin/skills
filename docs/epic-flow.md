# The planning-stack flow

This is the operator's path from an idea to merged code. The flow has two levels:

- An epic holds uncertainty and decisions in one active OpenSpec change; its child tickets hold live work state.
- A child ticket becomes a locked work order, is implemented and reviewed, and stops at an open pull request until a human merges it.

The primary contracts are [`epic`](../skills/drivers/epic/SKILL.md), [`ticket`](../skills/drivers/ticket/SKILL.md), and [`orchestrate`](../skills/drivers/orchestrate/SKILL.md). GitHub Issues are the reference tracker binding; see [`github-issues.md`](../skills/drivers/ticket/bindings/github-issues.md).

## OpenSpec change lifecycle

- **Before merge:** an ordinary ticket keeps its active change and deltas in the pull request for review; it does not fold or archive them.
- **After merge:** `/ticket finalize` verifies the human merge and CI, follows `operations.archive.guidance`, verifies archive JSON and strict validation, commits and pushes the archive on `main`, then verifies post-push CI before it comments completion or moves the ticket to done.
- **Epic children:** they create no child change and leave their parent epic's active change and archive ownership untouched.

## The map from idea to merge

1. Start or resume an epic when the effort needs multiple sessions, decisions, spikes, or independently shippable builds.
2. Record the epic in `openspec/changes/<epic-slug>/`. Its `proposal.md`, `design.md`, and `tasks.md` are authoritative: tasks link child issues in checked implementation sequence, while the tracker keeps their live type, status, dependencies, and deferral.
3. Keep imprecise concerns as named open questions in `design.md`; record a decision there or promote the question to a spike. File a build only when no open spike or named open question can invalidate its outcome, constraints, or acceptance criteria.
4. Run `/ticket triage <id>` on each build ticket. Triage grounds the ticket, runs `/scope`, chooses flat or chunked execution, stamps review depth and session fit, and posts one locked work order comment.
5. Run `/ticket start <id>` in a fresh session. It executes the work order, verifies the result, reviews the change, and opens the pull request.
6. Run `/ticket revise <id>` once per review round when the open pull request needs changes. It reloads the order, fixes and verifies the round, rebases once, and pushes the same branch.
7. A human reviews and merges the pull request after green CI and passed review. Agents do not merge, self-approve, or answer reviews outside `revise`.
8. Run `/ticket finalize <id>` after the human merge. It verifies the post-merge workflow, comments the outcome, moves the ticket to done, records measured cost, and tears down the ticket worktree.

An epic closes only after its live GitHub state proves that no spike child is open, every build child has a merged closing pull request or is closed `NOT_PLANNED`, and no deferred child remains open; then close the epic issue.

## One ticket in detail

### File

File a GitHub Issue under the epic when the work is a native child. Use a `spike` child for research, interview, mockup, or a human prerequisite. Use a `build` child for bounded implementation. Actual dependencies use native `blocked-by` edges. A follow-up needed for the epic destination is an in-scope child; work outside the destination can be a deferred native child.

The epic home session keeps the active change coherent and stays at planning altitude. `proposal.md`, `design.md`, and `tasks.md` hold durable planning state; live GitHub is authoritative for child work state. Pointer-only notes are deliberately omitted: owning skills and repository rules remain discoverable at their authoritative homes.

### Triage

Run `/ticket triage <id>`. The procedure first reads the issue, parent, links, and comments, then cuts or reuses the ticket worktree before grounding in the repository. It reads standing decisions when configured, repository decisions and change records, documentation, recent history, related pull requests, and the judging CI workflows.

Triage then:

- Classifies the ticket as `code`, `investigation`, or `manual`.
- Runs `/scope` unconditionally after grounding and classification. Resolved decisions go into the order. A human-only unresolved decision means nothing is posted until the operator answers through the scope interview.
- Resolves the surface lifecycle. `none` changes no rendered surface; `build` requires a locked `/ui-craft` manifest; `revise` requires a shipped behavior ledger, replay, safe dev-server entrypoint, and fixture source.
- Chooses a flat or chunked order using the slicing rubric. A chunked order gives every capability and shared contract exactly one owning chunk and declares file or target ownership and serial dependencies.
- Stamps `Focused`, `Targeted`, or `Full` review depth with a one-line reason.
- Stamps `Profile: hardening` only when the target repository declares a `Harden:` command and the user or ticket requests that profile. Otherwise it stamps `Profile: none`.
- Drafts the work order from the template and drafting conventions. Each fenced order is self-sufficient, names concrete targets, states what must not change, and names a verification command and expectation.
- Runs mandatory adversarial `/plan-review` before showing or posting the draft. The review checks grounding, acceptance, interface shape, scope and risk, and cost. Ordinary orders use one panel. Load-bearing plans continue until a fresh cold pass has no blocking objections, with a hard cap of three panels.

After the operator confirms the draft, triage posts one attributed comment with the complete work order, then moves the issue to `ticket:triaged`. For a `code` ticket the GitHub binding also attaches the `build` label. The work order is the execution lock: `start` and `revise` scan comments newest-first and use the newest fenced `WORK ORDER`; no order means no execution.

### Stamp and session fit

The stamp is not only a model name. It records the execution shape, selected review depth, profile, surface lifecycle, expected diff, verification contract, and a `Session fit:` paragraph copied from the selected routing-table row. A flat order carries the row's ladder. A chunked order carries the same ladder in each sub-order and exactly one `selected Agent rung` per sub-order.

`start` proceeds without asking about model fit or effort when the current session is named in the stamped fit at or above the selected rung. Otherwise the session must compare its own system-prompt model and confirmed effort with the order's `Open as:` requirement. A weaker model or effort stops the run. For a chunked order, the coordinator must also be at least as strong as the strongest chunk agent.

### Build

Run `/ticket start <id>` in a fresh session. It claims the session as the ticket's `coordinator`, locates the newest order, checks the model contract, reuses the triage worktree, moves the issue to in progress, and binds that worktree's Codebase Memory identity before reading code. A fresh session does not rely on triage memory. If the order no longer matches the repository or its chunks overlap, it stops for re-triage.

The builder follows the order's `Do` section and repository rules. Before declaring readiness it probes external CLI or API surfaces, runs new tests against the pre-change behavior, proves boundary claims by execution, and sweeps affected paths after late fixes. It runs the order's verification command until its output matches the stated expectation. It records the repository's existing change convention on the same branch.

### Review

For the normal profile, `start` audits the full diff against repository rules, then invokes `/review`, which routes to `code-review`. Code review checks two closed enumerations side by side:

- Standards checks the documented repository rules plus divergent copies, unfalsifiable behavior claims, and guards for unreachable states or missing trust-boundary guards.
- Spec checks the originating ticket or plan's acceptance criteria and any `Must prevent`, `Must recover`, and `Evidence owed` entries.

Each axis reports a verdict for every enumerated item. A finding needs a traced failure scenario. Review is capped at three rounds on one enumeration. A fix must be derived from the code and its documents, not from the finding text alone, and a re-review checks the fix as new attack surface. See [`code-review/SKILL.md`](../skills/tools/code-review/SKILL.md).

The stamped depth controls how far the review looks:

- `Focused` checks the exact requested change and that nothing else moved.
- `Targeted` checks changed behavior end to end and the repository rules that govern it.
- `Full` checks the whole diff, every defined check, and adversarial concerns.

Authentication, authorization, identity, secrets, destructive or irreversible operations, and organization-wide shared behavior force `Full`. For inherited workflow machinery, contract-semantic changes are `Full`; pure relocation, citation repoints, and additive paragraphs with no dependent behavior are `Targeted`. The floor overrides a small-looking change. A whole diff assembled from chunks is `Targeted`, or `Full` if any chunk was `Full`. A finding blocks only when it breaks the order's `Done when` clause, verification expectation, or a named repository rule.

Under `Profile: hardening`, `start` runs `/clean` and the repository's `Harden:` command instead. Focused and Targeted orders do not run `/review`; Full orders run one review round after hardening. Hardening can run at most three passes, and a missing or non-runnable hardening command is an error, not a pass. See [`review-depth.md`](../skills/drivers/ticket/references/review-depth.md).

### Ship

It opens the pull request against the default branch with the repository or organization template when available. The body contains what changed, the verification output, and the ticket link. It then moves the issue to pending review and comments the pull request link. UI work also carries the required mock-versus-build or base-versus-revision evidence and its corresponding ledger. Missing lifecycle evidence blocks the handoff.

Opening the pull request ends `start`. Human merge is the boundary.

### Revise and finalize

Run `/ticket revise <id>` for one round on an open pull request. It reloads the ticket, order, pull request reviews, and checks; reuses or respins the correct worktree; collects every unresolved comment and failure; fixes only grounded items within the order; re-verifies; re-audits; rebases once onto the current base; pushes the same branch; and responds to addressed pull request comments. It does not revise an already merged or closed pull request.

After a human merge, run `/ticket finalize <id>`. It performs the applicable OpenSpec lifecycle above, then tears down the worktree and branch and records actual session cost. The cost verdict can identify a good slice, under-slicing, over-slicing, degraded chunks, degraded coordination, missing data, or unreadable transcripts. Under- or over-slicing produces an amendment proposal for the rubric; the skill does not silently edit the rubric.

## Delegated execution and waves

Delegation is explicit and revocable. The home session may take a locked epic subtree when every order is stamped or every needed ruling is settled. A newly opened decision returns that subtree to attended mode. The home session keeps the parent change coherent.

Delegated triage uses the existing `/ticket triage` interface. Delegated builds use `/ticket start`. The home session collects worker comments, pull requests, and worktree results; it does not invent a parallel lifecycle.

Before each wave, the coordinator:

- Draws a conflict map from queued expected diffs.
- Verifies the shared checkout equals the current origin default-branch tip.
- Verifies each target worktree is at or descends from that tip before a build or review dispatch.
- Writes complete prompts to coordinator-owned session scratch, uses one state file per dispatch, and records a durable result locator.

Read-only drafts and reviews fan out in parallel. Builds use per-issue worktrees. Write-bearing triage and builds serialize only when expected diffs overlap. Chunks that touch a shared surface merge one at a time, rebasing when needed. A chunked ticket still ends with one ticket branch and one pull request.

For a chunked ticket, the ticket branch is the trunk. Each chunk branch starts from that trunk, implements only its independently executable sub-order, is reviewed at its stamped depth, and merges back with `--no-ff`. Parallel chunk worktrees are created together. Serial chunks are created only after the predecessor merges, so they include the dependency. The coordinator verifies each chunk, merges it, removes its chunk worktree, records the change itself after all chunks merge, runs the whole-ticket verification, and reviews the merged diff before opening the one pull request. See [`coordinator-mode.md`](../skills/drivers/ticket/references/coordinator-mode.md).

All delegated results are verified by the coordinator. A failed result gets one same-session retry. Under a Claude parent, a second failure escalates one tier along the selected ladder; at the top, the failure is surfaced. A Codex UI parent's v0 route stops with `NO_VALIDATED_ROUTE` after the same-session retry. There are no unbounded retries, tier skips, or silent route changes.

## Roles and model routing

Roles describe the work, and the routing table selects a model for that area. The table is benchmarked as of 2026-08-03 and says to re-benchmark when a new model ships. It gives these initial routes and ladders:

| Work area | Initial route | Escalation ladder |
| --- | --- | --- |
| Exploration or codebase mapping | Luna for bounded lookups, Sonnet for full-system maps | Luna, Sonnet, Opus |
| Hermetic implementation | Terra | Terra, Sonnet, Opus |
| Plan or spec writing | Terra | Terra, Sol, Opus |
| Prototyping, including UI mockups | Sol | Sol, Opus, none |
| Novel-solution brainstorming | Terra, or Opus when novelty is the deliverable | Terra, Opus, none |
| Documentation writing | Haiku, with Luna as an equal-scored alternate | Haiku, Opus, Sol |
| Code review | Luna for routine PRs, Opus for load-bearing or safety review | Luna, Sonnet, Opus, or Opus directly for load-bearing |

The table's bans and qualifications also apply. Never delegate to Fable. Luna is banned for UI mockups. Haiku is not used for exploration whose citations will not be independently verified, and Haiku never reviews. GPT-5.5, GPT-5.4, and GPT-5.4-Mini are light-pass plan or review probes only where the table explicitly permits them; GPT-5.4 is a viable plan alternate, while GPT-5.4-Mini is not a review choice.

Review routing has its own precedence. With a work order, Focused and Targeted are routine and Full is load-bearing. Without one, the sensitivity floor judges the stakes. `code-review` uses Luna with usable Codex for routine review, then Claude-only Sonnet when Codex is absent, unknown, at 5% or less headroom, or rate-limited. Load-bearing `code-review` uses Opus directly. `plan-review` uses Terra with usable Codex for routine review, then Claude-only Opus on absent, unknown, low-headroom, or rate-limited Codex. Load-bearing `plan-review` uses Opus directly. Reviewer selection never comes from the builder tier and never borrows a fallback from another row. See [`review-routing.md`](../skills/drivers/orchestrate/references/review-routing.md).

The Codex headroom gate runs when `/orchestrate` is invoked. A Claude parent checks for both CLIs, probes Codex with a Luna read-only run, and enters Claude-only mode when headroom is unknown, at most 5%, or the probe is rate-limited. A Codex UI parent stops dispatching in that condition and does not switch to Claude workers. If neither CLI exists, the coordinator cannot dispatch. Claude-only routing uses the Claude rungs in each applicable row.

Every delegation names the selected adapter, model, and effort. Dispatch goes through the pack's `claude-worker.py` or `codex-worker.py`, never the built-in Agent tool, Workflow tool, or background-agent machinery. Both adapters default effort to `medium`, and the coordinator may set the effort explicitly. The routing table's Codex benchmark used medium effort; no per-model default is treated as a benchmark result. These rules are the accepted decision in [`adr-149-pack-owned-model-dispatch.md`](adr/adr-149-pack-owned-model-dispatch.md).

## Load-bearing rules

- One authority owns each fact. The epic proposal, design, and tasks own durable epic planning. The ticket comment owns the executable work order. Live GitHub owns child work state.
- A work order is the only entry to execution. It must be the newest fenced `WORK ORDER` comment and must be self-sufficient for a fresh session.
- Canonical prose is byte-pinned. A canonical constant is the bytes strictly between named opening and closing full-heading-line anchors. Compare raw bytes with `Path.read_bytes()`, not normalized text. Generated-facts appendices pair deterministic commands with their complete literal output.
- Review depth is stamped at triage, has a sensitivity floor, and never downgrades. Missing depth defaults to Targeted as a triage defect.
- Session fit is part of the lock. A start session does not guess its own effort or silently accept a weaker model. A chunked coordinator cannot be weaker than its strongest chunk.
- Worktree identity is strict. One ticket uses one branch and worktree through its lifecycle. Chunk agents use per-chunk worktrees, and the control checkout is never edited, cleaned, stashed, or substituted.
- The expected diff is a closed allowlist of repository-relative paths. It has no escape clause.
- Review findings need evidence and a failure scenario. Taste is not blocking. A finding outside the order becomes a follow-up or is discarded, never a silent scope expansion.
- Human merge is required. Green CI and passed review permit a human merge; they do not authorize an agent to merge.

The byte-pinning, expected-diff, prompt, and evidence mechanics are specified in [`drafting-conventions.md`](../skills/drivers/ticket/references/drafting-conventions.md).

## What the operator types and what runs

The operator types `/epic` to open or resume an epic, files or answers tracked issues, and runs the four ticket verbs:

- `/ticket triage <id>` locks a ticket.
- `/ticket start <id>` builds to an open pull request.
- `/ticket revise <id>` handles one review round.
- `/ticket finalize <id>` closes the loop after human merge.

The operator may explicitly say to delegate a settled epic subtree. The operator also supplies decisions that `/scope` identifies as human-only and reviews and merges pull requests.

The procedures automatically claim sessions, cut or reuse worktrees, bind graph identity, read and post through the tracker contract, move ticket labels, run mandatory plan and code review dispatches, verify worker results, create chunk waves, write and collect adapter state, run verification commands, open pull requests, and record finalize actuals. Those actions remain subject to visible failure reporting. A failed status move is non-fatal and is not retried. A tracker, authentication, or Git failure stops the operation that needs it.

## Where to look when something is off

- Read the active change's proposal, design, and tasks for planning context, then check live GitHub for child work state.
- The ticket's issue comments contain the newest work order, amendments, and session fit. If no order is found, return to `/ticket triage <id>`.
- The pull request contains the implementation evidence, verification output, review conversation, and known residue. Use `/ticket revise <id>` for an open pull request, not manual patching in the control checkout.
- A silent or unfinished delegated worker is diagnosed from its named adapter state, launcher stdout, worktree or branch, or posted comment. Use the adapter's scoped `verify`; do not search for or stop unknown processes.
- A stale or overlapping target is a preflight failure. Refresh from the origin default-branch tip and re-triage when the order no longer matches the tree.
- A model or effort mismatch is a launch failure. Compare the session's actual model and confirmed effort to the stamped `Session fit` or `Open as` line.
- A review dispute is resolved against the order's `Done when` clause, the stamped depth, and the cited repository rule. Reopen scope only when evidence changes a settled risk assumption.
- A failed post-merge workflow blocks finalization. For ordinary OpenSpec changes, an archive, validation, commit, push, or post-push-CI failure also blocks finalization before completion is posted or the ticket moves to done.
- A finalize verdict of under-sliced, over-sliced, or still-degraded calls for a proposed amendment to `references/slicing.md`; `finalize` does not edit that rubric itself.

For complete mechanics, start with [`ticket/SKILL.md`](../skills/drivers/ticket/SKILL.md), then the verb page for the current phase. For orchestration, read [`orchestrate/SKILL.md`](../skills/drivers/orchestrate/SKILL.md) and its routing references. For planning objections, read [`plan-review/SKILL.md`](../skills/tools/plan-review/SKILL.md).
