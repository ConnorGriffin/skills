# The planning-stack flow

How work moves from an idea to merged code in the skills pack, as of the
planning-stack rework (epic #133, archived at
`openspec/changes/archive/epic-rework/`).

## The shape in one paragraph

An epic is a GitHub issue with child tickets and a ledger file. Each child
ticket becomes a stamped work order at triage, gets built by a Codex or Claude
worker in its own worktree, gets a Full-depth review before any PR opens, and
merges on green CI through the PR-body gate. You can run this attended (one
session per ticket) or hand a whole subtree to a home session that runs the
loop itself in parallel waves.

## The lifecycle of one ticket

1. **File.** A child issue under the epic, labeled `build` or `spike`.
2. **Triage.** A drafter agent writes the work order in a fresh checkout of
   main, following `skills/drivers/ticket/references/drafting-conventions.md`.
   A cold reviewer from the review routing tries to break it. Three panels is the cap; after
   that, mechanical findings get fixed in place by the coordinator and
   judgment findings come to you.
3. **Stamp.** The converged order is posted on the issue with a `Session fit`
   paragraph (the routing ladder plus "proceed without asking"), and the issue
   gets `ticket:triaged`. A start session named in that paragraph never asks
   about model fit or effort.
4. **Build.** A worker runs in a dedicated worktree with the order embedded in
   its prompt, plus the builder self-check (verify surfaces by running them,
   prove tests red first, test boundaries by attempting the forbidden action,
   sweep for orphans after late fixes). It commits signed-off and stops before
   any PR.
5. **Review.** A read-only reviewer does a Full-depth pass against the
   order. Findings loop back to the same worker; the coordinator re-verifies
   everything itself (chain rerun, mutation checks on pins).
6. **Ship.** PR body through the scorer and the voice judge, PR opens, merge
   on green CI, issue auto-closes, worktree removed, ledger updated.

## Delegated mode and waves

The epic skill (`skills/drivers/epic/SKILL.md`, "Delegated execution") lets
you hand a locked subtree to the home session, which then runs steps 2 through
6 itself. Entry needs your explicit delegation and settled rulings; any new
decision returns the subtree to you; the delegation is per-subtree and
revocable.

Delegated work runs in waves, not serially:

* The coordinator draws a conflict map over the queue's expected files first.
* Read-only work (drafts, reviews, judges) always fans out in parallel.
* Builds fan out in per-issue worktrees; only merges that touch a shared file
  (usually a shared test module) serialize, each rebasing before merge.
* Before any fan-out or build dispatch, the checkout is verified to sit at the
  origin tip. One stale commit once poisoned seven drafts at the same time.
* Results are collected from durable outputs (state files, worker stdout,
  posted comments), never by waiting on a notification. This is orchestrate's
  "Collect child results" section.

## Who runs what

Roles, not models, define the flow: a drafter writes orders, a builder
implements them, cold and Full-depth reviewers try to break both, and a voice
judge checks PR bodies. Which model fills each role comes from the routing
table (`skills/drivers/orchestrate/references/routing-table.md`):

* Each area row names a route and an escalation ladder, mixing Codex and
  Claude models by benchmarked score, with field notes from real sessions
  beside the scores.
* Reviewer selection for code-review and plan-review comes from
  `review-routing.md` beside the table: routine work maps from Focused or
  Targeted depth, load-bearing from Full.
* A Claude-only setup works throughout: every row's ladder carries a Claude
  rung, and the presence/headroom gate falls back to Claude-only mode
  automatically when Codex is absent, unknown, or rate-limited. An operator
  can also direct the reverse (Codex-first) as a session preference; the
  session-fit paragraph stamped on each order records whichever policy
  applies, so start sessions never re-ask.
* All dispatch goes through the pack adapters (`codex-worker.py`,
  `claude-worker.py`): prompt text passed positionally from a scratch file,
  one state file per dispatch, resume and verify through the same state file.
  The built-in Agent tool and background agents are banned for pack-defined
  dispatch (ADR 149).

## The rules that shape everything

* One authority per fact. A rule lives in exactly one document; consumers cite
  it. Review blocks any surviving second copy.
* Canonical prose is byte-pinned: tests compare the raw bytes of a section
  between unique full-heading-line anchors. A pin must fail when its block
  drifts; every new pin is proven red before the production edit.
* The over-engineering criterion: this is a one-person process, so machinery
  guarding states your setup never reaches is a defect, not safety. The
  trust-boundary rule does not apply to your own edits of your own artifacts.
* Field evidence from real sessions is first-class provenance for routing,
  beside benchmarks. A field note that contradicts a score owes an area
  replay, which can be filed and deferred.
* Depth floor: Full review when a change alters contract semantics; Targeted
  for relocations, citation repoints, and additive paragraphs nothing depends
  on.
* Mechanical review findings (wrong anchor, missing string, nondeterministic
  command) get fixed in place by the coordinator without a new round, recorded
  in an audit ledger; judgment findings still go through the panel or you.

## What you actually type

* `/epic` to open or resume an epic; the ledger under `openspec/changes/` is
  the resumable state and the home session is its sole writer.
* `/ticket triage|start|revise|finalize <id>` to run one ticket attended.
* A delegation sentence ("run this subtree yourself") to enter delegated mode.
* Rulings when asked. Everything else is comments, labels, PRs, and ledger
  commits the flow produces on its own.

## Where to look when something is off

* The ledger's `Status next:` line is the single resume point.
* Worker state files and stdout live under the session scratchpad; a silent
  dispatch is checked with the adapter's `verify` before it is reported live.
* The issue thread carries the order, its amendments, and session-fit; the PR
  body carries what merged and what the evidence does not show.
