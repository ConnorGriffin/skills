# Slicing a work order into chunks

Read during `triage`. Decides whether one order or several, how big each chunk
is, and what model tier each one names.

## The trait rubric

Slice when **two or more** of these hold. One or zero: the order stays flat.

| Trait | Fires when |
|---|---|
| Multiple targets or environments | The change lands in more than one deployment target, environment, or region |
| Live-resource import or tool port | Live resources are brought under the repo's control, or moved from one tool to another |
| Writes across a trust boundary | The change writes in more than one account, project, or trust boundary |
| Multiple deliverable artifacts | More than one shippable or independently reviewed thing: a library change plus its consumers, a workflow plus the scripts it calls, code plus a runbook, or a command plus the workflow and specification that consume it |
| Live run inside the ticket | Acceptance requires standing up and running the artifact before the pull request — real infrastructure, or a local harness the ticket must build first (a browser driver, a seeded database, an offline server) — so what the run exposes is corrected in the same session |
| Split-path evidence | Acceptance requires proving the same behavior on more than one code path that a single run cannot both exercise — a platform or feature-flag branch, or a re-implementation in another language held identical by test — so each path costs its own harness |
| Lockstep copies of one fact | One fact is obliged to appear in more than two encodings that no single tool checks together: a source of truth, a hand-maintained transcription, a fixture generator and the fixture it freezes, or one rule restated in separately installed artifacts that never see each other at run time |
| Lifecycle-gated surface revision | A shipped user-facing surface must first lock its visual contract, then implement it and prove it through a browser evidence matrix; the lock, implementation, and evidence each consume the same ticket's context |
| In-flight scope replacement | A new work order rejects a pull-request-sized implementation already on the ticket branch, and reconciling it and building the replacement are each projected at or above the 120k chunk floor |

The traits are proxies for context load, not for effort. A long-but-uniform change
(twenty near-identical grants in one target) fires nothing and stays flat, while a
short change that writes across two accounts and imports live resources fires
twice and gets sliced. The first four ask where the code lands. The fifth asks
whether the ticket also has to operate it, which costs a discovery-and-fix cycle
per surprise plus whatever the run itself takes. The sixth asks what it costs to
prove the change: a diff of two lines can owe two harnesses when the paths it
touches cannot both run at once, and building the second one is the work. The
seventh asks how many places one fact is written down: every encoding of that
fact costs its own pass, whether they are chained from a single source of truth
or restated independently of one another, and they drift because nothing checks
them together.

## Sizing

Every execution session carries roughly 90k of fixed overhead (skill load,
grounding, review) before it touches the work, which is what leaves a sub-120k
chunk mostly paying for itself.

These numbers describe what one agent building one piece of work costs, so only a
session claimed `--role worker` measures them. A coordinator's peak and a
reviewer's are recorded separately and tune nothing here. A coordinator over the
band on an otherwise-held slice is `coordination-degraded`; carry less in that
session, never cut more chunks.

* Target each chunk at a projected peak under 180k.
* Never slice below one pull-request-sized piece of work. A chunk that would peak
  under 120k is mostly overhead; fold it into a neighbour.
* Practical ceiling: four chunks. Promote to `/epic` only when more than four
  projected chunks leave at least one decision unsettled. Purely mechanical
  oversize is hand-split into serial `build` tickets instead: the epic apparatus
  is for fog, not bulk.

## Where these numbers came from

These thresholds were measured on one operator's own sessions, on one machine,
against that operator's repositories. The mechanism generalizes and the constants
may not: fixed overhead moves with how much a project's grounding costs, and the
degradation band moves with the model in use.

So another installation re-tunes rather than trusting them, and it re-tunes per
repository. This page carries no measured anchors of its own. Calibration accrues
in each repository's reviewer-memory store, which `finalize` appends a slicing
record to at the end of every finished ticket and `triage` reads before choosing a
shape. After a handful of tickets, that store holds this repository's own anchors
and shows whether the 180k target and the 120k floor are right on its work.

Moving the thresholds themselves is a change to this page, not to a store: the
180k target and the 120k floor are paired with constants in the ticket helper
(`scripts/ticket.py`), so a genuine move changes the prose and the constants
together. That is operator-initiated skills-repo work; `finalize` reports a
misprediction and proposes nothing.

## Chunk shape

Each chunk is a self-contained sub-order that a fresh agent can execute with only
the ticket and that sub-order in front of it. No chunk may say "as established in
chunk 1".

* **Mode** is `parallel` (no ordering constraint against other parallel chunks) or
  `serial after <n>` (needs another chunk's result on the branch first). Two chunks
  that touch the same file are serial, not parallel.
* **File ownership** is declared per chunk. Every chunk names the files or targets
  it owns, and two parallel chunks' ownership is disjoint, so they cannot collide.
* **Capability ownership** is declared per chunk. A chunk owns one coherent
  capability together with its named files or targets; every capability has exactly
  one owning chunk.
* **Shared-contract ownership** is explicit. Name every shared contract and give it
  exactly one owning chunk. Other chunks may rely on the stated shared contract,
  never on that chunk's private capability.
* **Parallel isolation** follows from that ownership. A parallel chunk must not
  implement, revise, or depend on another chunk's private capability; make it
  serial when that work or dependency is real.
* **Agent tier** comes from
  [the routing table](../../orchestrate/references/routing-table.md): classify the
  chunk into an area (exploration, hermetic implementation, documentation, review)
  and read the route off. Never name Fable, which is the coordinator tier only.
* **Review depth** comes from [review-depth.md](review-depth.md), stamped with its
  one-line reason.
* A ticket firing **live run inside the ticket** slices at the run: one chunk
  builds and tests the artifact against a stub, and a `serial after` chunk runs it
  with the operator and folds what the run exposes back into the code and the
  runbook.
* When **multiple deliverable artifacts**, **live run inside the ticket**, and
  **lockstep copies of one fact** all fire together, a server sub-order must not
  own both domain projection/association semantics and registry, concurrency, or
  cache-lifetime behavior, and a surface sub-order must not own both the shipped
  consumer state machine and its generated fixture/mirror/recovery-matrix
  evidence: slice into four — source/projection semantics, registry and
  lifecycle contract, shipped consumer, then generated evidence and live
  replay — folding a piece back into its neighbour only when it would fall
  below the 120k floor.

## Orchestrator tier

The order's `Open as:` names the tier the coordinator session must run at: the
**highest** tier any chunk names (haiku < sonnet < opus), and never Haiku, which
cannot review
([review-routing.md](../../orchestrate/references/review-routing.md)). The coordinator never launches
an agent smarter than itself.
