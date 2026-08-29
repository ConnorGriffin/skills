# 255 — Compaction-proof worker orders

Scope ledger. Routed from `/ticket triage 255` to interview mode: a concrete plan
exists in the issue body, with open decisions about where the durable order lives
and how far the rule reaches.

## Decisions

- Settled by grounding (`inline`): the issue's floated follow-on, a ~180k peak as
  the Codex chunk-size ceiling, is already a shipped requirement in
  `openspec/specs/ticket-workflow/spec.md` ("target each worker chunk below the
  180k-token peak band"). Out of scope for this ticket; do not restate it.
- Settled by grounding (`inline`): mechanical git exclusion of an order file is
  rejected. Verified live on git 2.50.1 that a linked worktree's own
  `$GIT_DIR/info/exclude` is never read; only the shared `.git/info/exclude`
  applies, and it silences the control checkout too. Excluding the file is
  therefore shared-state mutation across every worktree, not a worktree-local act.
- Settled by grounding (`inline`): the issue's "worktree `AGENTS.md`" option is
  rejected as a general rule. A target repo may already track a root `AGENTS.md`
  (this one does), so writing the order there dirties a tracked file and invites
  committing it.
- Settled by grounding (`inline`): today the complete prompt bytes are written to
  coordinator session scratch (`skills/drivers/orchestrate/SKILL.md` "Collect child
  results", `skills/drivers/ticket/references/coordinator-mode.md`). That location
  is coordinator-side, so a worker that compacts cannot reach it. This is the gap.
- Measured (`inline`): the worker sandboxes restrict writes, not reads. Both
  adapters configure only `filesystem.allowWrite`/`denyWrite`
  (`skills/drivers/orchestrate/scripts/claude-worker.py:91-104`), and the #149 probe
  log (`docs/scope/149-probes/run-log.md`) shows a sandboxed worker listing and
  reading while writes outside its cwd are refused. So a durable order is readable
  from either inside or outside the working copy; readability does not decide Q1.

- Q1 settled: A (`inline`). The durable order lives inside the worker's own
  working copy at the fixed root name `ORDER.md`. A compacted worker can find a
  fixed name by listing its cwd; it cannot recover an absolute path it was told
  once. Readability did not decide this (both places are readable).
- Q2 settled: A (`inline`). The rule binds every pack-owned write-mode dispatch,
  so its single home is Orchestrate's pack-wide `## Collect child results`
  contract. The issue body proposed ticket's drafting conventions as the home;
  that is the wrong layer for a pack-wide rule, so the pointer direction is
  reversed from the issue body and drafting conventions points at Orchestrate.
- Q3 settled: A (`inline`). A worker that cannot read its durable order stops and
  reports; the coordinator writes it again and resumes that same worker.
- Settled: minimum mechanism (`inline`). Operator called the interview
  over-engineered for the change. No git exclusion, no new coordinator gate, no
  new template field: the convention is prose in one home plus a behavior test.
- REOPENED then re-settled (`inline`), round 1 cold review, on evidence: the
  standing re-read line cannot be appended by the coordinator. A chunk's prompt is
  fixed as "the sub-order fence verbatim, followed only by that chunk's worktree
  path, branch name, `root_path`, and `project` ... and never coordinator
  commentary" (`skills/drivers/ticket/references/coordinator-mode.md:71-76`), and
  the fence must stay "executable without coordinator commentary"
  (`skills/drivers/ticket/templates/work-order.md:29`). The instruction still has
  to live inside the durable file, because `ORDER.md` is the prompt bytes and an
  instruction carried only in a preamble dies at the compaction it exists to
  survive. So it goes in the work-order template's fence boilerplate, and
  `skills/drivers/ticket/templates/work-order.md` joins the allowlist. This
  reverses the earlier "the template needs no new field" reading, which rested on
  a coordinator-appends assumption the evidence refuted.
- Settled (`inline`), round 1 cold review: ticket chunk dispatch is currently the
  pack's only write-mode dispatch; every other pack dispatcher runs
  `--sandbox read-only`. The rule still belongs in the pack-wide contract so a
  future write-mode dispatcher inherits it, but ticket is its only consumer today.
- Settled (`inline`), round 1 cold review: a coordinator that cannot write
  `ORDER.md` into the worker's cwd reports the dispatch unavailable and does not
  start the worker. Without this, a sandboxed coordinator (the Codex
  `workspace-write` case already documented at
  `skills/drivers/ticket/SKILL.md:120-125`) silently produces exactly the
  must-prevent outcome: a worker running with no durable order.
- Settled (`inline`): the original-prompt-only worker-input rule
  (`openspec/specs/planning-and-review/spec.md`) is left intact. `ORDER.md` is the
  same bytes as the original prompt, placed at dispatch, not new material
  introduced mid-session, so it is not a second exception alongside the research
  source handoff.

### Risk contract

- **Must prevent:** a worker reporting done while its durable order was never
  written, or while it silently drifted past the order's closed acceptance list.
- **Must recover:** nothing automatically.
- **Accepted failure:** the durable order is missing or unreadable at re-read
  time. The worker stops and reports; the coordinator writes it again and resumes
  that same worker.
- **Unsupported:** any mechanical guarantee that the file is never committed or
  pushed. The order's own text and the diff the coordinator already reads before
  merging are the whole enforcement. Git-level exclusion is explicitly rejected
  above as shared-state mutation.
- **Evidence owed:** a behavior test pinning the convention text in its single
  home.
- **Why:** a prose-contract change to a single-operator public skill pack; the
  failure mode is visible drift, recoverable by rerunning the work.
- **Disposition:** inline.

## Open questions

_None. The frontier is empty; every question above is settled in `Decisions`._

## Spawned tasks

_None yet._
