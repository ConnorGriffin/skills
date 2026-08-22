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
| Multiple deliverable artifacts | More than one shippable thing: a library change plus its consumers, a workflow plus the scripts it calls, code plus a runbook |
| Live run inside the ticket | Acceptance requires standing up and running the artifact before the pull request — real infrastructure, or a local harness the ticket must build first (a browser driver, a seeded database, an offline server) — so what the run exposes is corrected in the same session |
| Split-path evidence | Acceptance requires proving the same behavior on more than one code path that a single run cannot both exercise — a platform or feature-flag branch, or a re-implementation in another language held identical by test — so each path costs its own harness |
| Lockstep copies of one fact | Adding one member to a closed set obliges edits in more than two encodings that no single tool checks together: a source of truth, a hand-maintained transcription, a fixture generator, and the committed fixture it freezes |
| Lifecycle-gated surface revision | A shipped user-facing surface must first lock its visual contract, then implement it and prove it through a browser evidence matrix; the lock, implementation, and evidence each consume the same ticket's context |

The traits are proxies for context load, not for effort. A long-but-uniform change
(twenty near-identical grants in one target) fires nothing and stays flat, while a
short change that writes across two accounts and imports live resources fires
twice and gets sliced. The first four ask where the code lands. The fifth asks
whether the ticket also has to operate it, which costs a discovery-and-fix cycle
per surprise plus whatever the run itself takes. The sixth asks what it costs to
prove the change: a diff of two lines can owe two harnesses when the paths it
touches cannot both run at once, and building the second one is the work. The
seventh asks how many places one fact is written down: a single new member of a
closed set costs a pass per encoding, and the encodings drift because nothing
checks them together.

## Anchor table

Calibration from real tickets. Peaks are the measured session maximum, read with
the helper's `scan` command, not estimates.

| Ticket | Work | Traits | Right shape | Actual |
|---|---|---|---|---|
| A | One configuration grant in one deployment target | none | flat, one agent | peaked 128k, one session |
| B | Bootstrap script, its tests, a CI job and a runbook, run live against the target host | multiple artifacts, live run | slice: build the artifact, then run and correct | flat; peaked 313k over 2 sessions |
| C | Routes across two environments and two accounts | multiple targets, cross-boundary writes | slice by target | 4 sessions, 275k to 408k |
| D | Port live networking into the repo's own tooling, with imports | multiple targets, import | slice; was not | 574k in one session |
| E | CI previewing every deployment target | multiple targets, multiple artifacts | slice | 359k plus a 313k resume |
| F | One new member of a closed behavioural taxonomy, wired through its server projection, a JS mirror, three fixture generators and a browser gate | multiple artifacts, live run, lockstep copies | slice: detector and its tests, then the surface and its fixtures | flat; peaked 503k over 4 sessions |
| 10 | Proof-bounded I:C history across an analyzer, server projections, generated fixtures, and a lifecycle-gated Diagnose revision | multiple artifacts, live run, lockstep copies, lifecycle-gated surface revision | slice into four serial chunks: analyzer, server contract, generated projections/evidence, then surface lock and browser evidence | 3 chunks; peaked 244k |

When a ticket's traits match an anchor row, take that row's shape. When it sits
between rows, say which two and pick the more conservative one.

## Sizing

Ground truth from mining 134 past sessions: 31 peaked above 180k, and every
execution session carries roughly 90k of fixed overhead (skill load, grounding,
review) before it touches the work.

* Target each chunk at a projected peak under 180k.
* Never slice below one pull-request-sized piece of work. A chunk that would peak
  under 120k is mostly overhead; fold it into a neighbour.
* Practical ceiling: four chunks. More than that means the ticket is really an
  epic and wants child tickets, not sub-orders.

## Where these numbers came from

Every figure on this page was measured on one operator's own sessions, on one
machine, against that operator's repositories. The mechanism generalizes and the
constants may not: fixed overhead moves with how much a project's grounding costs,
and the degradation band moves with the model in use.

So another installation re-tunes rather than trusting them. Run the helper's
`record` command at the end of each finished ticket, as `finalize` does. After a
handful of tickets, its verdicts show whether the 180k target and the 120k floor
are right on your work, and each misprediction arrives with a drafted amendment
against this page.

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

## Orchestrator tier

The order's `Open as:` names the tier the coordinator session must run at: the
**highest** tier any chunk names (haiku < sonnet < opus), and never Haiku, which
cannot review ([review-depth.md](review-depth.md)). The coordinator never launches
an agent smarter than itself.
