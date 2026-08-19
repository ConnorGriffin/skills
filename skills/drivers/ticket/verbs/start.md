# /ticket start `<ticket-id>`

Execute a locked work order in a fresh session. Ends at the open pull request.

## Procedure

1. **Fetch the order.** Use the contract's locate operation. None found: refuse,
   say "no work order on `<ticket-id>`; run /ticket triage `<ticket-id>`", and stop.
   The comment's `Execution:` line says `single agent` or `chunked`; an order with
   no `Execution:` line is a flat order.

2. **Model-check.** The order's `Open as:` line names a required model and effort. A
   session cannot reliably introspect its own reasoning effort from context, so do
   not guess it, and do not answer from memory of an earlier guess. State the model
   name this session's own system prompt reports, then ask the user in prose to
   confirm the effort level this session is running. Compare both against
   `Open as:`. Weaker on either axis: say so and stop, so the user relaunches
   correctly. Same or stronger on both: proceed. On a chunked order, also check every
   `SUB-ORDER`'s `Agent:` line against the confirmed model: the session must be at
   least as strong as the strongest chunk. Weaker than any one of them and the whole
   order is refused. Never run part of it, and never launch an agent smarter than the
   coordinator.

3. **Sufficiency check.** Read the order against the actual repo. If the repo has
   drifted since triage (files moved, the constraint it names is gone), stop and
   report the mismatch; the fix is a re-triage, not improvisation. On a chunked
   order, confirm the chunks' declared file and target ownership is still disjoint;
   an overlap that drift introduced is a re-triage, not a merge problem to solve
   later.

4. **Worktree and branch.** Never work in the control checkout. Reuse the worktree
   and branch triage cut, verifying with
   `git -C <worktree> branch --show-current`. Only cut fresh when triage's worktree
   is gone, with the same command shape triage used
   ([verbs/triage.md](triage.md), step 2). The helper refuses if the control
   checkout is dirty or the target path exists; surface that, and do not force it.
   Use the worktree path the helper printed as the working directory for every step
   below. Move the ticket to in progress.

5. **Chunked order: switch to coordinator mode.** If the `Execution:` line says
   `chunked`, load `/orchestrate` now, then follow
   [references/coordinator-mode.md](../references/coordinator-mode.md) instead of
   steps 7 through 10, and rejoin at step 11. Flat orders skip this and continue at
   step 6.

6. **Read the standing decisions**, per the skill page's standing-decisions slot,
   before implementing. Absent, say so in one line and continue. This never refuses
   the order.

7. **Implement.** Read the repo's `AGENTS.md` or `CLAUDE.md` first; its rules bind
   everything you write on this branch. Never add or edit one yourself; if the repo
   has none, work to the user's global standards. Follow the order's Do section.
   Match the repo's existing idioms, reading neighboring code first. Record the
   change where the repo already records changes, on the same branch, per the skill
   page's change-record rule.

   **Route by shape of the change.** User-interface work runs as `/ui-craft build`
   against the locked manifest from triage. A new module or interface loads
   `/codebase-design` vocabulary before the seam is cut. New behavior with testable
   acceptance criteria goes test-first through `/tdd`. CI or workflow-file changes
   read `/ci-design` first.

8. **Verification loop.** Run the order's `Verification:` command locally and
   iterate until its output matches the order's `Expectation:` line exactly, per the
   skill page's verification-step rule. Never fabricate the output.

9. **Repo-rules audit and adversarial review, before the pull request.** Re-read the
   repo's `AGENTS.md` or `CLAUDE.md`, which has decayed from context by now, and
   audit the full diff against it rule by rule, including any completion checklist
   it defines. Fix violations, then hand off to `/review` on the branch's changes
   since the default branch, with the work order as the spec: one axis checks the
   diff against the order, the other against the repo's documented conventions. Run
   it at the order's stamped `Review depth:`, reading
   [references/review-depth.md](../references/review-depth.md) for what each depth
   checks and what counts as blocking. Fix confirmed findings, re-run the
   verification loop if code changed, then review once more. Two rounds maximum;
   findings still open after round two go into the pull request body as known
   issues, never silently dropped.

10. **Fold the change record into the baseline in the order's last pull request.**
    When the pull request being opened is the order's final one (single-pull-request
    orders: the only one), the same diff completes whatever the repo's convention
    asks for at landing time. This lands before the pull request is opened or marked
    ready, never as a post-approval push: a push after approval invalidates the
    approval, and reducing approval churn outranks tidiness. If the last pull
    request is already approved and this was missed, leave it for a later sweep and
    flag it; do not push it onto the approved pull request.

11. **Open the pull request.** `gh pr create` against the default branch. The body
    follows an existing template when one exists, in this order: the repo's
    `.github/pull_request_template.md` (or its `PULL_REQUEST_TEMPLATE/` directory),
    then the organization default in the organization's `.github` repo. Keep the
    template's headings and checklist verbatim, fill its sections with the substance
    below, and tick only checklist items actually done. Add a section the template
    lacks only when required content has no home in it. Never discard or rewrite a
    template because it seems unsuitable: open the pull request with it filled as
    best as possible, and raise the mismatch to the user. Only when no template
    exists anywhere, write the body free-form. Either way the body carries what
    changed, the verification output in a fence, and a link to the ticket. When
    `/pr-body` is installed, score the body with it before opening. Then move the
    ticket to pending review and comment on it (attribution first) with the pull
    request link and a one-line status.

    **User-facing surface changes attach two more things, per the engineering
    charter:** paired mock-versus-build screenshots (headless, same fixture and
    viewports as the lock) and a fidelity ledger walking every lock-manifest term to
    met, re-settle, or blocked. Missing either is a blocking gap on the pull request,
    not a nit. Do not open it without them when the change touches a locked surface.

12. **Stop.** Report the pull request URL, the verification evidence, review
    findings fixed or carried, and anything from the order left undone and why. On a
    chunked order also report each chunk's outcome and tier. Do not merge, do not
    self-approve, and do not respond to reviews; that is `/ticket revise`.

## Refusals

* No work order (step 1), model mismatch (step 2), repo drift or overlapping chunk
  ownership (step 3).
* The order's classification is `manual`: nothing to execute, so say so.
* Verification cannot be run at all (no credentials, no access, no runnable suite):
  stop after implementation, open the pull request as a draft, and say which
  evidence is missing. Never fabricate expected output.
* A chunked order whose sub-orders are not independently executable: refuse the
  order and route back to `/ticket triage <ticket-id>`. Do not rewrite the slice
  in flight.
