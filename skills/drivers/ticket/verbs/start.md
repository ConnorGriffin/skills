# /ticket start `<ticket-id>`

Execute a locked work order in a fresh session. Ends at the open pull request.

## Procedure

1. **Complete the shared opening.** Complete shared rules 1–2: read and summarize
   the ticket, then claim the session before locating the work order or reaching
   any later refusal. This session drives the ticket, so it claims itself with
   `--verb start --role coordinator` (the default role) on a flat and a chunked
   order alike. Use the shared claim command and its visible, non-blocking failure
   semantics; do not duplicate them here.

2. **Fetch the order.** Use the contract's locate operation. None found: refuse,
   say "no work order on `<ticket-id>`; run /ticket triage `<ticket-id>`", and stop.
   The comment's `Execution:` line says `single agent` or `chunked`; an order with
   no `Execution:` line is a flat order.

3. **Model-check.** On a flat order with `Session fit:`, a session whose system-prompt model is named in that paragraph at or above the selected rung proceeds directly to step 4, skipping the remainder of Model-check and without asking about model fit or effort. On a chunked order, take that same fast path only when every `SUB-ORDER` has exactly one `Session fit:` paragraph whose ladder is an ordered non-empty sequence of display-name rungs byte-identical across every `SUB-ORDER`, whose exactly one `selected Agent rung: <Rung>` annotation names exactly one rung in that paragraph, and whose coordinator system-prompt model is named at or above that selected rung in every paragraph. Otherwise, the order's `Open as:` line names a required model and effort. A session cannot reliably introspect its own reasoning effort from context, so do not guess it, and do not answer from memory of an earlier guess. State the model name this session's own system prompt reports, then ask the user in prose to confirm the effort level this session is running. Compare both against `Open as:`. Weaker on either axis: say so and stop, so the user relaunches correctly. Same or stronger on both: proceed. On a chunked order, also check every `SUB-ORDER`'s `Agent:` line against the confirmed model: the session must be at least as strong as the strongest chunk. Weaker than any one of them and the whole order is refused. Never run part of it, and never launch an agent smarter than the coordinator.

4. **Worktree and branch.** This is the first repository action after the shared
   opening. Never work in the control checkout. Reuse the worktree
   and branch triage cut, verifying with
   `git -C <worktree> branch --show-current`. Only cut fresh when triage's worktree
   is gone, with the same command shape triage used
   ([verbs/triage.md](triage.md), step 2). The helper refuses if the control
   checkout is dirty or the target path exists; surface that, and do not force it.
   Use the worktree path the helper printed as the working directory for every step
   below. Move the ticket to in progress. Then bind that worktree's graph identity
   per the skill page's graph-identity rule, before step 5 reads any code, and
   report what it printed: a fresh session resolves this from the checkout it just
   verified rather than inheriting triage's.

5. **Sufficiency check.** From the ticket worktree, read the order against the
   actual repo. If the repo has drifted since triage (files moved, the constraint
   it names is gone), stop and report the mismatch; the fix is a re-triage, not
   improvisation. On a chunked order, confirm the chunks' declared file and target
   ownership is still disjoint; an overlap that drift introduced is a re-triage,
   not a merge problem to solve later.

   Resolve the order's `Surface lifecycle:` before implementation. `build` requires
   the named locked manifest. `revise` requires the named shipped behavior ledger,
   replay, and repo-declared safe dev-server entrypoint plus fixture source. `none`
   selects no UI Craft mode. An unknown value or a named contract that is absent is
   drift and requires re-triage. For a legacy order posted before this slot existed,
   infer `build` only when it explicitly names a locked manifest; otherwise select
   no UI Craft mode. A legacy order that still asks to change a rendered surface
   without either contract is insufficient and requires re-triage. On a chunked
   order, apply the same check to every sub-order before switching to coordinator
   mode.

6. **Chunked order: switch to coordinator mode.** If the `Execution:` line says
   `chunked`, load `/orchestrate` now, then follow
   [references/coordinator-mode.md](../references/coordinator-mode.md) instead of
   steps 8 through 12, and rejoin at step 13. Flat orders skip this and continue at
   step 7.

7. **Read the standing decisions**, per the skill page's standing-decisions slot,
   before implementing. Absent, say so in one line and continue. This never refuses
   the order.

### Builder self-check

Before declaring the change ready, run each check below.

1. **External surface by execution.** Before coding against a CLI or API surface, run `--help` or a probe call against that surface; do not infer flags, arguments, or behavior from memory.
2. **Fail-first tests.** Before production edits, run every new test against the pre-change behavior or a deliberately broken variant and observe the expected failure. A fake that accepts every input or a mock of the function under test is not evidence.
3. **Boundaries by execution.** Prove a security or confinement claim by attempting the forbidden action in a real run; configuration inspection alone is not evidence.
4. **Post-fix sweep.** After each late fix, sweep its affected path for uncalled symbols, dead parameters, and prose that still describes the pre-fix behavior.

8. **Implement.** Read [drafting conventions](../references/drafting-conventions.md)
   with the locked order, then read the repo's `AGENTS.md` or `CLAUDE.md`; its rules
   bind everything you write on this branch. Never add or edit one yourself; if the
   repo has none, work to the user's global standards. Follow the order's Do section.
   Match the repo's existing idioms, reading neighboring code first. Record the
   change where the repo already records changes, on the same branch, per the skill
   page's change-record rule. An epic child creates no per-child change record: the
   parent epic's existing change record is authoritative, and implementation
   preserves the parent-plan bytes already committed by triage.

   **Route by shape of the change.** `Surface lifecycle: build` runs `/ui-craft
   build` against the named locked manifest. `Surface lifecycle: revise` runs
   `/ui-craft revise` against the named shipped behavior ledger and replay through
   the repo-declared safe dev-server entrypoint and fixture source. `Surface
   lifecycle: none` skips UI Craft. A new module or interface loads
   `/codebase-design` vocabulary before the seam is cut. With `Profile: none`, new
   behavior with testable acceptance criteria goes test-first through `/tdd`. With
   `Profile: hardening`, write tests through the public interface without `/tdd`.
   CI or workflow-file changes read `/ci-design` first.

9. **Verification loop.** Run the order's `Verification:` command locally and
   iterate until its output matches the order's `Expectation:` line exactly, per the
   skill page's verification-step rule. Never fabricate the output.

10. **Repo-rules audit and adversarial review, before the pull request.** An order
    with no `Profile:` line is `Profile: none`.

    A delegated `start` worker returns its review-ready implementation diff to its
    coordinator through the coordinator-recorded durable result locator, then
    stops at this boundary. Its coordinator dispatches `/review`, verifies the
    verdict, and resumes the same worker with actionable findings or a verified
    clean verdict. The worker must not launch a nested reviewer. A coordinator-run
    start follows the profile route below directly.

    **Profile: none.** Re-read the
   repo's `AGENTS.md` or `CLAUDE.md`, which has decayed from context by now, and
   audit the full diff against it rule by rule, including any completion checklist
   it defines. Fix violations, then hand off to `/review` on the branch's changes
   since the default branch, with the work order as the spec: one axis checks the
   diff against the order, the other against the repo's documented conventions. Run
   it at the order's stamped `Review depth:`, reading
   [references/review-depth.md](../references/review-depth.md) for what each depth
   checks and what counts as blocking. Classify every grounded finding with
   [references/review-actions.md](../references/review-actions.md). Fix confirmed
   findings, re-run the verification loop if code changed, then review once more.
   Two rounds maximum; findings still open after round two go into the pull request
   body as known issues, never silently dropped.
   The literal invocation already granted this dispatch's transfer of the work
   order or task prompt plus the repository code, documentation, and UI fidelity
   evidence rendered from manufactured or synthetic fixtures (tracked in the
   repository or not, never real user, production, or patient data), so the
   coordinator does not re-ask. Credentials, secrets, patient data, `.env`, and
   real database contents are excluded.

    **Profile: hardening.** Run `/clean` on the branch diff, then run the repo's
    `Harden:` command. Fix uncovered lines, surviving mutants, and high-CRAP
    functions, re-running until the command exits 0 and every survivor is killed by
    a public-interface test or listed as equivalent with a one-line reason in the
    pull request body. Stop after at most three passes and open the pull request as
    a draft naming the residue. A `Harden:` command that cannot run (tool missing,
    parse failure, wrong runtime) is an error: open a draft pull request, name the
    missing evidence, and never a pass. Targeted and Focused orders run no
    `/review`; Full orders run one `/review` round after hardening.

11. **Preserve the change record for merge.** Outside an epic, the active change
    and its deltas remain reviewable in the pull request. Do not fold or archive
    them before merge. An epic child creates no per-child change record and
   preserves the parent-plan bytes with implementation in the pull request. After
   a human merge, `finalize` leaves the parent active for epic-owned archive.

12. **Preflight the outbound OpenSpec change.** Only an ordinary OpenSpec-backed
   ticket uses this gate. After implementation, review, and all active-change fixes
   are complete, run `git fetch origin` immediately before the command, then run:

   ```sh
   python3 <ticket-skill-directory>/scripts/ticket.py preflight-openspec \
     --repo <ticket-worktree> \
     --base-ref refs/remotes/origin/HEAD
   ```

   The fetch refreshes the base that the command resolves locally. A ticket using
   another or no change-record convention, or an epic child, bypasses this gate
   unchanged. Fetch, ref, or preflight failure stops visibly; do not open the pull
   request. Finalization remains the sole authoritative archive owner.

13. **Open the pull request.** `gh pr create` against the default branch. The body
    follows an existing template when one exists, in this order: the repo's
    `.github/pull_request_template.md` (or its `PULL_REQUEST_TEMPLATE/` directory),
    then the organization default in the organization's `.github` repo. Keep the
    template's headings and checklist verbatim, fill its sections with the substance
    below, and tick only checklist items actually done. Add a section the template
    lacks only when required content has no home in it. Never discard or rewrite a
    template because it seems unsuitable: open the pull request with it filled as
    best as possible, and raise the mismatch to the user. Only when no template
    exists anywhere, write the body free-form. Either way the body carries what
    changed, the verification output in a fence, and a link to the ticket. Under
    `Profile: hardening`, it also carries the `Harden:` output in a fence, the
    survivor list with dispositions, and the QA script verbatim. When
    `/pr-body` is installed, score the body with it before opening. Then move the
    ticket to pending review and comment on it (attribution first) with the pull
    request link and a one-line status.

    **Surface evidence follows the lifecycle.** A `build` attaches paired
    mock-versus-build screenshots (same fixture and viewports as the lock) and a
    fidelity ledger walking every lock-manifest term to met, re-settle, or blocked.
    A `revise` attaches base-versus-revision before/after screenshots from the same
    safe fixture, the amended frozen behavior ledger, and raw replay output against
    the built revision. Missing lifecycle evidence is a blocking gap, not a nit;
    `revise` never invents a lock manifest or fidelity ledger after the fact.

14. **Stop.** Report the pull request URL, the verification evidence, review
    findings fixed or carried, and anything from the order left undone and why. On a
    chunked order also report each chunk's outcome and tier. Do not merge, do not
    self-approve, and do not respond to reviews; that is `/ticket revise`.

## Refusals

* No work order (step 2), model mismatch (step 3), repo drift or overlapping chunk
  ownership (step 5).
* The order's classification is `manual`: nothing to execute, so say so.
* Verification cannot be run at all (no credentials, no access, no runnable suite):
  stop after implementation, open the pull request as a draft, and say which
  evidence is missing. Never fabricate expected output.
* A chunked order whose sub-orders are not independently executable: refuse the
  order and route back to `/ticket triage <ticket-id>`. Do not rewrite the slice
  in flight.
