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

## Round 3 — drafting halted, decisions reopened

Three review panels ran (cold, its delta re-check, a fresh cold pass). Blocking
counts by round: 4 authoring, then 2 injected by the round-1 fixes, then 4 more of
which 2 were injected by the round-2 fixes. Injected blockers climbing across
rounds is the rewrite-clean signal, and the findings below are unsettled decisions
rather than undiscovered typos, so drafting stopped at the cap per
`skills/drivers/ticket/verbs/triage.md` step 12.

### Newly measured, and it reprices Q1

`ORDER.md` left untracked in a worker's worktree breaks worktree teardown. Verified
live: with an untracked `ORDER.md` present, `git worktree remove` exits 128 with
"contains modified or untracked files, use --force to delete it". This repo forbids
the force: `skills/drivers/ticket/verbs/finalize.md:144` ("A dirty worktree makes
`worktree remove` fail. Report that and stop; never force it") and
`skills/drivers/ticket/verbs/revise.md:21-22` (stop when `status --short` is
non-empty, never force). So every chunked ticket would stop-and-report at chunk
teardown and again at finalization.

This was not known when Q1 was settled and it materially reprices option A. The
file now needs an owner for its deletion, or it needs to not be in the worktree.

### Also confirmed, and dependent on the Q1 re-decision

- A delegated `start`, `triage`, or `revise` worker is an adapter-dispatched
  write-mode worker (`verbs/start.md:98`, `verbs/triage.md:220`,
  `verbs/revise.md:66`). A delegated `start` worker executes a FLAT order, so the
  round-2 boundary claiming flat orders are never dispatched is false as written.
- The inventory's stop-and-report escape clause is scoped to "write-mode
  dispatchers" while the inventory itself lists "pages stating a prompt-file rule".
  Different sets; a correct implementer would halt on the mismatch.
- Appendix item 3's grep misses the phrase "positional prompt", so
  `skills/tools/code-review/SKILL.md:195-199` and
  `skills/drivers/orchestrate/references/dispatch-claude.md:56-61` were absent. The
  order's claim that dispatch-claude.md states no prompt rule was a grep artifact.
- Done-when bullet 1 ("the only page in the repo that states them") is
  unsatisfiable against step 4c's spec delta and step 5's behavior test, which must
  both carry the clause text.

## Round 4 — Q4 settled, order rewritten clean

- Q4 settled: A, made deterministic (`inline`). The durable order is deleted by the
  teardown steps themselves, not after a successful dispatch. Teardown is the exact
  path that fails today, so putting the delete there covers a dead coordinator, an
  abandoned worker, and a crashed dispatch alike; a delete on the happy path would
  not. One fact, one implementation: there is no second delete on the collect-result
  path.
- The three teardown sites, all already existing: chunk teardown
  (`skills/drivers/ticket/references/coordinator-mode.md` step 5), ticket teardown
  (`skills/drivers/ticket/verbs/finalize.md` step 4), and the stale-worktree respin
  (`skills/drivers/ticket/verbs/revise.md` step 2, which stops when
  `status --short` is non-empty). The delete precedes `git worktree remove` and that
  cleanliness check.
- Measured (`inline`): deleting the file unblocks teardown (`git worktree remove`
  exits 0). An *ignored* `ORDER.md` also does not block teardown and is invisible to
  `status --short`, but that route was rejected: it would require a committed
  `.gitignore` entry in every consuming repo, and it would hide the file from the
  pre-merge diff read that is the never-committed rule's only enforcement.
- Consequence accepted (`inline`): the allowlist grows to six skill pages, adding
  `verbs/finalize.md` and `verbs/revise.md`. Larger than the change first looked,
  and each page is evidenced rather than speculative.
- Settled (`inline`): a delegated `start`, `triage`, or `revise` worker is an
  ordinary adapter-dispatched write-mode worker and gets an `ORDER.md`. Only a flat
  fence executed directly by the `/ticket start` session does not.

## Round 5 — three-panel cap reached

The final cold panel returned three blockers and two notes, all verified and all
fixed. None reopened a decision; each was a precision defect in the contract's own
wording, with a determinate correction:

- `fence-less` and `write-mode`/`read-mode` appear nowhere else in the pack
  (`grep -rn 'fence-less' skills/` returns nothing; `write-mode` hits only an
  unrelated ADR filename). Clause 1a now defines both terms against the adapters'
  real `--sandbox` values at first use.
- The coverage hole that mattered: a delegated `start` worker's prompt carries a
  flat work-order fence, so it was neither "a sub-order fence" nor "fence-less",
  and neither producer of the standing instruction fired on the pack's most common
  write-mode dispatch. Clause 1b now branches on "a chunk sub-order fence" versus
  "every other write-mode dispatch".
- A delegated `triage` or `revise` prompt has no `Done when` heading, so 1b now
  says "the order's acceptance list"; only the sub-order fence boilerplate names
  `Done when` literally.
- Clause 1d bound resumes to `ORDER.md` for read-only reviewers, which 1f gives no
  such file. Now scoped to write-mode workers.
- Done-when bullet 1 forbade the very teardown edits bullet 3 mandates. Its
  carve-out now names all four: the three teardown sites carry clause 1h
  operationally, the fence boilerplate is the worker-facing instruction, and the
  spec delta and test are the record and its evidence.

Panel counts: 4 authoring blockers, then 2 injected, then 4 (2 injected), then 3.
The three-panel cap is now spent. The final fixes carry no fresh cold pass, which
is stated to the operator at approval rather than papered over.

## Open questions

_None. The order awaits operator approval before posting._

## Spawned tasks

_None yet._
