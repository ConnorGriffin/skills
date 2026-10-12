# Design

## ADR 300 — Drop codebase-memory

The pack no longer ships `codebase-memory` or `cbm-onboard`. Agents rarely reached
for the graph tools over ordinary search and file reads, and the index cost about
29 GB on disk. The discovery hooks, the installer, the onboarding and teardown
scripts, `.cbmignore`, and the profile's code-discovery paragraph go with them.
This supersedes ADR 65, which made the code-discovery skill the owner of its
activation. The ticket rewrite below removes the ticket skill's graph-identity rule.

## ADR 300 — Replace orchestrate with native subagents

The pack no longer owns model dispatch. Claude Code's native subagents take a
model, effort, tools allowlist, and worktree isolation per dispatch, and
`SendMessage` resumes the same worker, which covers what `codex-worker.py`,
`claude-worker.py`, and `worker_lifecycle.py` were built for. This supersedes
ADR 149 (pack-owned model dispatch) and ADR 150 (shared worker lifecycle module).

Skills that dispatched through the adapters now dispatch read-only native subagents
with the model named on the dispatch and resume the same subagent on retry. The
coordinator rules live in a short "Delegating to subagents" section of
`profile/base.md`: coordinate rather than implement when the work is large, name
the model, keep explorers read-only without Bash, isolate implementers in a
worktree, demand full verify output, retry once then escalate, and have the
coordinator dispatch reviewers and resume the same worker. Codex work goes through
the codex plugin (`/codex:rescue`, `/codex:review`) or a direct request to Codex.
The empirically benchmarked routing table is not carried forward.

## ADR 300 — Remove persona-review

The pack no longer convenes persona panels. `persona-review`, the review front
door's `personas` route, plan-review's load-bearing persona panel, and UI Craft's
`consensus` mode and its `init` persona-panel step are removed. A load-bearing plan
review ends on a fresh cold pass with no blocking objections, or at the
three-panel cap. UI Craft's critique and lock walkthroughs keep their built-in user
archetypes and any personas a repository defines; those are single-reviewer
walkthroughs, not panels.

## ADR 300 — Fold scope and preflight into ticket triage

`scope` and `preflight` are deleted as standalone skills. Their surviving behavior
— resolving open decisions, the risk contract, and the generated-facts appendix —
belongs to `/ticket triage`, and other skills point there.

## ADR 300 — Slim ticket lifecycle

The ticket skill is cut from about 2,300 lines of prose to under 600, shaped as one
artifact per stage with a human at each gate: triage produces a locked work order the
user approves, start produces a pull request, revise produces a pushed review round,
and finalize closes the ticket after a human merges. Triage absorbs scope (name the
dominant uncertainty; ask the user in batched rounds, research, spike, or prototype)
and preflight (facts come from a command run now; spike the first hour of any unrun
assumption), keeps the three review depths and their sensitivity floor, and runs one
cold `/plan-review` round only at Full depth. Start reviews with one `/code-review`
pass and delegates through native subagents. Chunked orders, coordinator mode, session
fit and model admission, persona panels, multi-round lock panels, the graph identity,
and the per-ticket scope ledger are gone, because native subagents and the shorter
lifecycle cover them and instructions this long were not being read in full. The
`ticket.py` script keeps all four subcommands, since the slim prose still uses each;
its chunked-verdict code stays as working, tested behavior with no prose caller. The
lock keeps its `EXECUTION LOCK v2` header and pinned-source admission, so existing
locks remain readable.

## ADR 300 — Remove epic

The pack no longer ships `epic`. Multi-session work is now child issues that triage
files and tracks as a checklist on the parent ticket; each child is an ordinary ticket
with its own work order and change record, and an unsettled decision waits behind a
spike child. The epic planning branch, parent-plan pins, shared parent change, and
epic-child carve-outs in the ticket skill go with it, because they existed only to
coordinate work that one checklist and independent tickets now carry. This supersedes
ADR 143. Active change 273's finalization delta still mentions epic children; that
clause becomes inert and is left to that change.
