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

## Evidence v2

When the reviewed plan has a durable locator and immutable revision, follow [the shared
envelope reference](../../../docs/evidence/envelope-v2.md): an objection may `revises`
its affected revision-scoped criterion; the revision may `revises` that objection; a
reproduction or refutation uses a verification link only to an admissible claim,
criterion, decision, finding, fix, or verification; and the verdict may
`derives_from` the revision and govern the check. Preserve the cold-review sequence
and three-panel cap. An
unrevised chat plan has no eligible authority, so emit nothing.

## Cold means cold

The reviewer must have no stake in the plan. If this session authored or
co-authored the plan (or is unsure), do not review it yourself — spawn a
separate cold subagent per plan with only the plan's location, the rubric, and
read access to the repo. Self-review by the author reliably misses what a cold
reader catches, no matter how honestly the author tries to re-derive.

## Delegation authority

Invoking this skill authorizes every sub-agent dispatch that this procedure marks mandatory, including a mandatory nested review skill. Do not ask again solely because a session-level preference says "do not spawn agents"; apply that preference to discretionary delegation only. An explicit task-level refusal of this required review or revocation of delegation overrides this authorization: stop and state that the requested workflow cannot run without its required independent review.

## The rubric

Judge the plan on exactly these five axes. For axes 3 and 4, ground in the
project's engineering standards document (a charter, architecture guide, or
design doc the repo or your global instructions provide) when one exists; the
definitions below are the fallback.

1. **Grounding.** Every factual claim the plan makes about the current system
   must be verifiable in the code. Verify every load-bearing claim yourself —
   open the files. A plan built on a wrong "currently, X does Y" fails in the
   worst way: confidently. A fact inherited from a prior ticket, plan, or
   session is an unverified claim, not a given: reground counts, statuses, and
   behavior against the current system. One measured plan carried a secret
   count of 6 from its predecessor when the real count was 8, and the same
   session lost three rounds to an assumed decrypt failure mode nobody ran.
2. **Acceptance.** Criteria must be observable through the public interface and
   complete enough that meeting them means *done*. Flag criteria that are
   untestable, vague ("works correctly"), or that smuggle in unstated work.
3. **Interface shape.** The front door the plan proposes must be far simpler
   than the implementation behind it. Run the deletion test on any new module
   (if removing it would just move complexity around, it shouldn't exist). No
   seam before the second caller exists. A plan that never says what the
   interface looks like is itself an objection — that decision made implicitly
   at build time is how shallow modules happen.
4. **Scope, risk contract, and complexity budget.** Out-of-scope must be explicit.
   For bounded work, load the admitted
   [risk contract](../../workflows/scope/SKILL.md#risk-contract). Missing risk decisions block
   countersign only when the build would otherwise have to invent failure handling,
   recovery, or evidence obligations. An edge case earns handling only if it is
   reachable from inputs the acceptance criteria describe **and** its contracted
   outcome requires handling. A scenario covered by `Accepted failure` or
   `Unsupported` is not an objection unless the plan claims stronger behavior. If
   evidence changes the assumed likelihood, consequence, or recoverability, object
   that the risk decision must reopen; do not silently prescribe hardening. Require
   evidence only for acceptance criteria, must-prevent outcomes, enforced invariants,
   and observed regressions — never for a target test count or an exhaustive failure
   matrix. The right change is the smallest one that meets acceptance and the risk
   contract.
5. **Cost.** Is the effort implied by the plan sane for the ask? Flag a plan
   whose blast radius (files touched, migrations, new machinery) is out of
   proportion to its outcome.

## The cycle

0. **Triage: demand the spike first.** Before the cold pass, skim for pinned
   executable literals (regexes, shell fragments, workflow expressions,
   queries) and for assertions about specific tool or API behavior (exit
   codes, matching semantics, config interplay). If either is present, the
   first objection is to demand the spike — an executed artifact the plan
   references — rather than reviewing the prose version. One measured review
   spent its first round correcting pinned literals and its second correcting
   the corrections, so the cost lands whether or not the demand is made early.

   The same rule extends past executable literals to **facts**. A hand-typed
   count, path, param name, version, or enumeration is an automatic first
   objection: demand the generated-facts appendix — `command → output` pairs the
   prose cites, which the `preflight` skill produces — rather than reviewing the
   prose figures, because verifying a number by hand costs a round and re-costs
   it every time the plan is edited. In one measured review of a load-bearing
   process document, roughly half of sixty-two objections across ten rounds were
   figures written from memory and wrong. A load-bearing plan that arrives with
   no preflight at all is sent through it before the cold pass, not reviewed as
   drafted.
1. **Cold read + grounding pass.** Read the plan, then the code it touches.
   Verify claims before forming opinions. A literal in the plan — a regex, a
   shell fragment, a workflow expression, a query — is verified by executing
   it against real inputs, never by reading it; prose reasoning about
   executable text is where confident wrong claims live. If step 0 already demanded
   a spike, this pass reviews the spike's artifact, not the literal.
2. **Objections.** Report a numbered list. Each objection: the claim or gap,
   the evidence (file:line where relevant), why it breaks the build if
   unfixed, and the cheapest fix. Mark each **blocks countersign** or
   **note** — notes should be rare; if it wouldn't change what gets built,
   discard it rather than reporting it. Taste is not an objection.
3. **Verify objections before they travel.** An objection is a claim, not a
   fact. Before any objection reaches the plan's author or a fix round, the
   session running the review reproduces its factual assertions: execute the
   regex, parse the shell, open the file at the cited line. An objection
   whose claim fails reproduction is recorded as refuted and goes back to
   the reviewer, never forward to the author (a false reviewer claim that
   reaches a fix round gets baked into the plan and costs a full round to
   retract — one measured review paid that exact price). An objection
   whose claim cannot be reproduced cheaply is forwarded marked unverified,
   and the author treats it as a question, not an instruction.
4. **Wait for the revision or answers**, then have the same reviewer re-check
   the deltas. **Treat every delta as new attack surface**, not as a checkbox:
   revisions routinely introduce fresh defects (a fix that patches the
   objected hole and opens a different one), and objections whose "cheapest
   fix" was applied verbatim still need verifying against the real machinery.
5. **Terminate by stakes, not by pass count.**
   - **Ordinary plan** (modest blast radius, downstream review exists as a
     backstop): one panel. If it drew blood, fix and have the same reviewer
     re-verify the deltas; then done. Plan review here only needs to catch
     what is *expensive* to catch later, not everything.
   - **Load-bearing or hard-to-reverse plan** (standards, machinery other
     agents inherit, migrations — anywhere a miss propagates): convene the
     persona panel via the `persona-review` skill when it is installed, and
     feed its panel verdict into the objection list alongside the cold pass's
     own (the panel's memory writes are proposed records surfaced at close,
     user-approved — the review itself still edits nothing). Without that
     skill installed, this step is a no-op and the review proceeds on the
     fresh cold pass alone. The review still ends only when a **fresh cold
     pass returns no blocking objections**; whichever termination path gets
     there — a clean fresh pass or the three-panel cap — is what runs the
     panel's deferred close approval pass.
     The objecting reviewer's own re-verification never terminates — a
     reviewer verifying fixes to their own objections is anchored on them.
     After each revision cycle converges, launch a new reviewer with no
     context from the previous ones, told the plan already survived review
     so shallow objections are gone — dig for what earlier passes miss:
     interactions with machinery the plan doesn't mention, contradictions
     between the plan's own decided constraints, and claims that are subtly
     rather than obviously wrong. Its objections loop back through steps 3
     and 4.
     A clean fresh pass ends the review: state **countersigned** plainly.
6. **Hard cap: three panels.** Adversarial reviewers rarely return
   empty-handed, so as real defects deplete, late panels drift toward
   plausible-but-marginal objections — and every revision cycle is new
   attack surface. Blocking objections still arriving at the cap mean the
   plan has unsettled decisions, not undiscovered typos: take those
   decisions to the user directly. Say so and stop.

## Executable logic belongs in a spike, not in prose

A plan that pins executable logic as prose literals — exact regexes, shell
fragments, workflow expressions — is an implementation written in a medium
nothing executes, and every review round of such a plan mints new falsifiable
surface faster than review retires it. So the objection comes at triage, on
sight of the first pinned literal, not after a round has been spent correcting
one: the logic belongs in an executed artifact (a scratch file with a test,
built and run in the plan's worktree) that the plan references, and the prose
version of it is not reviewed at all. One measured review spent four of its
seven rounds on
defects in prose-specified regex, shell, and workflow expressions that a
compiler or one table test would have caught in seconds.

## Calibration

The failure mode of adversarial review is inventing work. Every objection must
trace to one of the five axes; "I would have done it differently" traces to
none of them. An empty objection list on a sound plan is a successful review —
countersign it and stop.
