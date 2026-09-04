---
name: preflight
description: Use when a plan, spec, work order, or process doc is drafted and about to enter review or execution — grounds its facts, spikes its first hour, and single-sources its rules so review rounds start deep instead of shallow.
---

# Preflight

Run this on a draft **before** `plan-review`, not instead of it. Preflight edits
the plan; review only objects to it.

The premise is measured. One load-bearing process document took ten cold
adversarial rounds and roughly sixty-two objections to reach a clean pass, and a
post-mortem of those objections found four preventable classes:

- **About half were hand-typed facts** — counts, paths, URL params, state
  enumerations — written from memory and wrong.
- **Fix rounds minted new contradictions**, because the same rule was restated in
  several sections and a patch desynced them.
- **Serial generalist panels each found one stratum**; the single parallel
  specialized round found the most.
- **The deepest bugs were only findable by executing the plan's first steps** — a
  URL param the page silently ignored, a comparison instrument that could only
  render one state, a fixture whose absence degraded quietly instead of failing.

Three of the four are cheaper to prevent than to review. That's preflight: three
moves, in order.

## 1. Generated-facts appendix

**Every count, path, URL param, enumeration, version, or config value the plan
states must be produced by a command.** The appendix records `command → output`
pairs; the plan's prose cites the appendix entry rather than repeating the
figure from memory. A hand-typed fact is a defect, not a rounding error — the
reviewer's job then becomes checking the command, which is cheap, instead of
re-deriving the number, which is a round.

- An enumeration needs the command that enumerates it — `grep -c` per event
  type, an `ls` of the fixture directory, a `--help` dump, a schema query. "The
  six states" is a claim; the command that prints six is the fact.
- Re-run the appendix after any edit that touches a cited figure. A stale
  appendix is worse than none, because it reads as grounded.
- **A fact about *behavior* — what a param does, whether an endpoint honors a
  flag — is not a grep.** It belongs to move 2. Do not let a grep that finds the
  param's name stand in for evidence that anything reads it.

### Verbatim command output

Every `command → output` evidence block is pasted verbatim from an actual command
run. To abbreviate output, change the command so it produces the shorter output
(for example, `grep -m` or `head`); never edit the captured output, insert
ellipses, or drop matches. Manual edits are prohibited and require a **BLOCKED**
verdict on their own.

## 2. First-hour spike

Before any reviewer sees the draft, **execute the plan's opening steps against
the real artifacts for the effort needed to establish its admitted behavior.** Open the page and pass the
param. List the network fetches. Run the instrument once, in each state it
claims to compare. Delete the fixture and watch what the fallback actually does.

The rule that catches the expensive class: **every claim of the form "X is
addressable / served / discovered / honored by Y" gets one live probe.** Those
claims are the ones that read as obviously true and are silently false, and no
amount of reading finds them.

Findings amend the plan before review starts. The scratch work is throwaway — a
worktree, a scratchpad script, a curl log — and is never committed; the plan
cites what the spike established, not the scratch.

## 3. Single-source rules

**Each rule or constraint is stated normatively in exactly one place.** Every
other mention points at that place instead of restating it. This is what stops a
fix round from minting a contradiction: a patch can only desync a rule that
exists in two voices.

Before the doc leaves preflight — **and again after every later fix round** —
grep each rule that appears in two or more places and reconcile it down to one
normative statement plus references. Late rounds are when this decays fastest,
because that's when patches are landing under time pressure.

## Hand-back

Preflight returns the grounded plan to its caller, with the generated-facts appendix
and the spike's findings attached. The caller continues its next authorized step,
which may be `plan-review`; preflight itself does not claim the parent workflow ended.

Recommend that review's **first** round be three to five **parallel specialized
lenses** rather than one generalist pass — machinery-interaction, cold-executor
simulation, inventory verification, and domain judgment. Serial generalist
rounds each surface one stratum and then repeat each other; parallel lenses
surface the strata at once, which is what a preflighted plan needs, since the
shallow findings are already gone.
