# Design

## ADR 300 — Drop codebase-memory

The pack no longer ships `codebase-memory` or `cbm-onboard`. Agents rarely reached
for the graph tools over ordinary search and file reads, and the index cost about
29 GB on disk. The discovery hooks, the installer, the onboarding and teardown
scripts, `.cbmignore`, and the profile's code-discovery paragraph go with them.
This supersedes ADR 65, which made the code-discovery skill the owner of its
activation. The ticket skill's graph-identity rule is removed by the ticket
rewrite that follows under this issue.

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
belongs to `/ticket triage`, and other skills point there. Until the ticket rewrite
under this issue lands, triage still names `/scope`; that residue is accepted and
tracked in `tasks.md`.
