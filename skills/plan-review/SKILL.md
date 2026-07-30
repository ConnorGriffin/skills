---
name: plan-review
description: Adversarially review a plan, work order, spec, or agent brief before anything gets built. Use when the user wants a plan reviewed, stress-tested, audited, or countersigned, says "plan review" or "poke holes in this plan", or wants a pre-build check on an issue/brief/PRD.
---

# Plan review

Review a plan the way a cold, skeptical engineer would — **before** a line of it
is built. The premise: a couple of adversarial cycles on a plan is cheaper than
fixing the built thing after the fact.

The subject can be anything plan-shaped: a GitHub issue, an agent work order, a
PRD, a design doc, a chat-message plan. If the user didn't point at one, ask
what to review — don't guess.

**Read-only.** A plan review never edits code and never fixes the plan itself.
It produces objections and a verdict; revising the plan is the author's job.

## Cold means cold

The reviewer must have no stake in the plan. If this session authored or
co-authored the plan (or is unsure), do not review it yourself — spawn a
separate cold subagent per plan with only the plan's location, the rubric, and
read access to the repo. Self-review by the author reliably misses what a cold
reader catches, no matter how honestly the author tries to re-derive.

## The rubric

Judge the plan on exactly these five axes. For axes 3 and 4, ground in the
project's engineering standards document (a charter, architecture guide, or
design doc the repo or your global instructions provide) when one exists; the
definitions below are the fallback.

1. **Grounding.** Every factual claim the plan makes about the current system
   must be verifiable in the code. Verify every load-bearing claim yourself —
   open the files. A plan built on a wrong "currently, X does Y" fails in the
   worst way: confidently.
2. **Acceptance.** Criteria must be observable through the public interface and
   complete enough that meeting them means *done*. Flag criteria that are
   untestable, vague ("works correctly"), or that smuggle in unstated work.
3. **Interface shape.** The front door the plan proposes must be far simpler
   than the implementation behind it. Run the deletion test on any new module
   (if removing it would just move complexity around, it shouldn't exist). No
   seam before the second caller exists. A plan that never says what the
   interface looks like is itself an objection — that decision made implicitly
   at build time is how shallow modules happen.
4. **Scope and complexity budget.** Out-of-scope must be explicit. An edge
   case earns handling only if it is reachable from inputs the acceptance
   criteria describe — speculative hardening is a defect in a plan, not a
   virtue. The right change is the smallest one that meets acceptance.
5. **Cost.** Is the effort implied by the plan sane for the ask? Flag a plan
   whose blast radius (files touched, migrations, new machinery) is out of
   proportion to its outcome.

## The cycle

1. **Cold read + grounding pass.** Read the plan, then the code it touches.
   Verify claims before forming opinions.
2. **Objections.** Report a numbered list. Each objection: the claim or gap,
   the evidence (file:line where relevant), why it breaks the build if
   unfixed, and the cheapest fix. Mark each **blocks countersign** or
   **note** — notes should be rare; if it wouldn't change what gets built,
   discard it rather than reporting it. Taste is not an objection.
3. **Wait for the revision or answers**, then have the same reviewer re-check
   the deltas. **Treat every delta as new attack surface**, not as a checkbox:
   revisions routinely introduce fresh defects (a fix that patches the
   objected hole and opens a different one), and objections whose "cheapest
   fix" was applied verbatim still need verifying against the real machinery.
4. **Terminate by stakes, not by pass count.**
   - **Ordinary plan** (modest blast radius, downstream review exists as a
     backstop): one panel. If it drew blood, fix and have the same reviewer
     re-verify the deltas; then done. Plan review here only needs to catch
     what is *expensive* to catch later, not everything.
   - **Load-bearing or hard-to-reverse plan** (standards, machinery other
     agents inherit, migrations — anywhere a miss propagates): the review
     ends only when a **fresh cold pass returns no blocking objections**.
     The objecting reviewer's own re-verification never terminates — a
     reviewer verifying fixes to their own objections is anchored on them.
     After each revision cycle converges, launch a new reviewer with no
     context from the previous ones, told the plan already survived review
     so shallow objections are gone — dig for what earlier passes miss:
     interactions with machinery the plan doesn't mention, contradictions
     between the plan's own decided constraints, and claims that are subtly
     rather than obviously wrong. Its objections loop back through step 3.
     A clean fresh pass ends the review: state **countersigned** plainly.
5. **Hard cap: three panels.** Adversarial reviewers rarely return
   empty-handed, so as real defects deplete, late panels drift toward
   plausible-but-marginal objections — and every revision cycle is new
   attack surface. Blocking objections still arriving at the cap mean the
   plan has unsettled decisions, not undiscovered typos: take those
   decisions to the user directly. Say so and stop.

## Calibration

The failure mode of adversarial review is inventing work. Every objection must
trace to one of the five axes; "I would have done it differently" traces to
none of them. An empty objection list on a sound plan is a successful review —
countersign it and stop.
