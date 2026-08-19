# /ticket revise `<ticket-id>`

Action one review round on the ticket's open pull request. Runs per round, in any
session. Always a single agent, even when the order was chunked: the chunks merged
long ago and the pull request is one diff.

## Procedure

1. **Reload context.** Read the ticket and its comments for the work order and the
   pull request link, then `gh pr view <url> --json state,reviews,comments` and
   `gh pr checks`. Pull request merged or closed: stop, and point at
   `/ticket finalize <ticket-id>` or the user.

2. **Worktree.** If the ticket's worktree still exists (verify with
   `git -C <control checkout> worktree list`), check it is on the pull request's
   head branch: `git -C <worktree> branch --show-current` must equal the pull
   request's `headRefName`. Match: work there. Mismatch: the worktree belongs to a
   different round or ticket state, so remove it if clean
   (`git -C <control checkout> worktree remove <path>`, reporting and stopping if
   `git -C <worktree> status --short` is non-empty, never forcing) and respin fresh.
   No worktree at all: same respin.

   ```sh
   python3 <spin-worktree-skill-directory>/scripts/spin-worktree.py \
     --repo <control checkout> \
     --pr <number> \
     --name <ticket-id-lowercased>
   ```

   Never fix review comments in the control checkout.

3. **Read the standing decisions**, per the skill page's standing-decisions slot,
   before actioning the round. Absent, say so in one line and continue. This never
   refuses the round.

4. **Collect the round.** Unresolved review comments (human and automated), failing
   checks, and any new verification output CI posted. List them before touching
   code.

5. **Judge, then fix.** For each item: fix it, or push back with a reasoned reply.
   Never silently ignore one. What blocks is what breaks the order's Done when
   clause; [references/review-depth.md](../references/review-depth.md) governs that
   call, and the order's stamped depth (Full when any chunk was Full) sets how far
   to look. Scope discipline: a review comment that expands scope beyond the work
   order gets a reply naming it out of scope and, if it is real, a suggestion to
   file a ticket. The order is still the contract.

6. **Re-verify.** Re-run the order's verification command after changes, same rules
   as `start`: the output must match the order's expectation. Re-read the repo's
   `AGENTS.md` or `CLAUDE.md` and audit the changes you are about to push against
   it, including any completion checklist it defines. Fix violations before pushing.

7. **Push and respond.** Push to the same branch. Reply to each addressed comment on
   the pull request, resolving or answering it. Update the repo's change record if
   its checklist moved, and update its decision record if a decision changed during
   review.

8. **Status.** Comment on the ticket (attribution first) only if the round
   materially changed the plan. Routine fix-and-push rounds need no ticket comment.

## Refusals

* No open pull request on the ticket: nothing to revise, so route to
  `/ticket start <ticket-id>` or the user.
* The review asks for something the work order forbids: stop and surface the
  conflict to the user rather than choosing sides.
