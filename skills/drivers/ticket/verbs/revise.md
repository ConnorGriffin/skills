# /ticket revise `<ticket-id>`

Action one review round on the ticket's open pull request. The session claims
`--verb revise`; it may resume another revise round, but it must not reuse a session
claimed by start or finalize. Always a single agent, even when the order was
chunked: the chunks merged long ago and the pull request is one diff.

## Procedure

1. **Reload context.** Read the ticket and its comments for the work order and the
   pull request link, then `gh pr view <url> --json state,reviews,comments` and
   `gh pr checks`. Pull request merged or closed: stop, and point at
   `/ticket finalize <ticket-id>` or the user.

   Locate the newest order with the same contract operation `start` used — every
   round re-locates fresh; nothing is cached from the round that opened this pull
   request. Under a legacy `WORK ORDER`, nothing more to admit. Under an
   `EXECUTION LOCK`, admission runs in two places, split by what each row needs.
   Here, with no checkout beyond the located comment itself, admit the
   checkout-independent rows of [start](start.md) step 5's matrix: recognized
   version and mode, grammar, delivery fields, and ownership. Model fit is not
   among them: `start` step 3 owns that check, and `revise` has no model-check
   step to re-run it in. The
   remaining rows — commit resolution, branch pin, change state, selection
   completeness, and unauthorized amendment — read the ticket branch and the
   pinned commit, which do not exist here yet; step 2 finishes admission against
   them immediately after it establishes the worktree, before this round
   proceeds any further. Whichever half a row falls in, the refusal is the same:
   name the row, stop, and route to `/ticket triage <ticket-id>`. The newest
   recognized lock always wins, which is what reconciles "reuses the same lock
   and pin" with a mid-round amendment: when nothing has changed since `start`,
   the newest lock is still the one it admitted, so this round reuses the same
   pin. When triage posted a newer lock since, authorizing an amendment or an
   expanded selection, that newer lock is now the newest and is what this round
   admits instead. When no newer lock exists, the newest lock is still the old
   one, pinning the old commit — so a source amendment with no newer lock
   refuses here on the same unauthorized-amendment row `start` defines, never on
   a comparison against "the lock that opened this pull request" as a separate,
   cached reference. `revise` never posts a lock itself.

2. **Worktree.** If the ticket's worktree still exists (verify with
   `git -C <control checkout> worktree list`), check it is on the pull request's
   head branch: `git -C <worktree> branch --show-current` must equal the pull
   request's `headRefName`. Match: work there. Mismatch: the worktree belongs to a
   different round or ticket state, so remove it if clean (run
   `<cbm-onboard-skill-directory>/scripts/cbm-teardown.sh <path>` while the checkout
   still exists, then `rm -f <path>/ORDER.md`, reporting and stopping if
   `git -C <worktree> status --short` is non-empty, then
   `git -C <control checkout> worktree remove <path>`, never forcing)
   and respin fresh. No worktree at all: same respin.

   ```sh
   python3 <spin-worktree-skill-directory>/scripts/spin-worktree.py \
     --repo <control checkout> \
     --pr <number> \
     --name <ticket-id-lowercased>
   ```

   Never fix review comments in the control checkout.

   Bind that worktree's graph identity per the skill page's graph-identity rule
   before step 4 reads any code, and report what it printed. Each round resolves it
   afresh, because the worktree it runs against may be the one this step respun.

   Now, from this worktree, finish the `EXECUTION LOCK` admission step 1 deferred:
   commit resolution, branch pin, change state, selection completeness, and
   unauthorized amendment, exactly as [start](start.md) step 5 runs them, all
   against this worktree specifically — never the control checkout, which never
   switches branches and may be on anything. A failing row here refuses the same
   way step 1's rows do: name the row, stop, and route to `/ticket triage
   <ticket-id>`. Skipping this half silently, or running it against the control
   checkout instead of this worktree, both leave the matrix unenforced; neither
   is acceptable. A legacy `WORK ORDER` has nothing further to admit.

3. **Read the standing decisions**, per the skill page's standing-decisions slot,
   before actioning the round. Absent, say so in one line and continue. This never
   refuses the round.

4. **Collect the round.** Read
   [drafting conventions](../references/drafting-conventions.md) before evaluating
   an order revision. Then collect unresolved review comments (human and automated),
   failing checks, and any new verification output CI posted. List them before
   touching code.

5. **Judge, then fix.** Ground every item and classify it with
   [references/review-actions.md](../references/review-actions.md). Never silently
   ignore one. What blocks is what breaks the order's Done when clause;
   [references/review-depth.md](../references/review-depth.md) governs that call,
   and the order's stamped depth (Full when any chunk was Full) sets how far to
   look. The order is still the contract.

   Under an `EXECUTION LOCK`, a review item is an ordinary fix only when it stays
   inside the located lock's `Selected tasks:` and `Acceptance anchors:`. An item
   that asks to touch the pinned source outside that selection is scope
   expansion: refuse it here rather than folding it in, name it in the round's
   status comment, and say it needs a newer lock from `/ticket triage
   <ticket-id>` before any round may act on it.

6. **Refresh mergeability.** Before handing the pull request back for human merge,
   `git fetch origin`, refresh `baseRefName` and `mergeStateStatus` with `gh pr
   view`, then rebase once onto `origin/<baseRefName>`. Do not retry the rebase. If
   GitHub reports a conflict or the rebase has a semantic conflict you cannot
   resolve safely, abort it and stop; surface the conflict to the human rather than
   force a resolution.

7. **Re-verify and re-review.** Re-run the order's verification command after the
   changes and rebase, same rules as `start`: the output must match the order's
   expectation. Re-read the repo's `AGENTS.md` or `CLAUDE.md` and audit the changes
   you are about to push against it, including any completion checklist it defines.
   Fix violations. A delegated `revise` worker returns its review-ready revised diff
   to its coordinator through the coordinator-recorded durable result locator,
   then stops at this boundary. Its coordinator dispatches `/review`, verifies the
   verdict, and resumes the same worker with actionable findings or a verified
   clean verdict. The worker must not launch a nested reviewer. A coordinator-run
   revise follows the profile route directly. Under `Profile: hardening`, re-run the repo's `Harden:` command
   with the same stop rule and three-pass cap as `start`, and run `/review` only
   when the stamped depth is Full. Under `Profile: none`, run `/review` at the
   order's stamped review depth. Fix confirmed findings and repeat verification if
   code changed.
   The literal invocation already granted this dispatch's transfer of the work
   order or task prompt plus the repository code, documentation, and UI fidelity
   evidence rendered from manufactured or synthetic fixtures (tracked in the
   repository or not, never real user, production, or patient data), so the
   coordinator does not re-ask. Credentials, secrets, patient data, `.env`, and
   real database contents are excluded.

8. **Push and respond.** Before pushing, update the reviewable change record. Outside
   an epic, update the active change record if its checklist moved, and update its
   decision record if a decision changed during review; its active change and deltas
   remain reviewable until the human merge, so do not fold or archive them. An epic
   child creates no per-child change record. Preserve the parent-plan bytes already
   carried by the branch, including grounded review fixes to that amendment; the
   parent epic's active change remains authoritative.

   **Preflight the outbound OpenSpec change.** Only an ordinary OpenSpec-backed
   ticket uses this gate. After the rebase and every active-change, checklist, and
   decision edit, run `git fetch origin` again immediately before:

   ```sh
   python3 <ticket-skill-directory>/scripts/ticket.py preflight-openspec \
     --repo <ticket-worktree> \
     --base-ref origin/<baseRefName>
   ```

   The earlier rebase fetch does not satisfy this final refresh. A ticket using
   another or no change-record convention, or an epic child, bypasses this gate
   unchanged. Fetch, ref, or preflight failure stops visibly; do not push. The gate
   never archives the authoritative change: finalization remains the sole
   authoritative archive owner.

   After the gate succeeds, push to the same branch. Reply to each addressed comment
   on the pull request, resolving or answering it.

9. **Status.** Comment on the ticket (attribution first) only if the round
   materially changed the plan. Routine fix-and-push rounds need no ticket comment.

## Refusals

* No open pull request on the ticket: nothing to revise, so route to
  `/ticket start <ticket-id>` or the user.
* The review asks for something the work order forbids: stop and surface the
  conflict to the user rather than choosing sides.
