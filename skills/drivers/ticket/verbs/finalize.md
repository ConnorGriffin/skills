# /ticket finalize `<ticket-id>`

Close the loop after a human merged (or abandoned) the pull request. Nothing syncs
the code host back to the tracker; this verb is that sync.

## Procedure

1. **Verify the end state.** Read the ticket for the pull request link, then
   `gh pr view <n> --json state,mergedAt,mergeCommit`. Pull request still open:
   refuse, because finalize runs after a merge, not instead of one.

2. **Merged path.**

   a. Confirm the merge: an empty `mergedAt` means not merged, so back to step 1.

   b. Confirm the post-merge workflow succeeded (`gh run list` on the repo). If it
   failed, stop and report; the ticket is not done while the post-merge run is red.

   c. Comment on the ticket (attribution first): the merged pull request link, a
   one-line outcome, and the post-merge evidence.

   d. Move the ticket to done. Report a failed move; do not retry.

   e. Outside an epic, verify the change record landed in the ticket's last pull
   request, per the skill page's change-record rule. Missed: flag it in the report
   as sweep debt, never as a per-ticket follow-up pull request and never as a push
   to an approved pull request. An epic child neither verifies a per-child change
   record nor incurs sweep debt; the parent epic's existing change/archive flow is
   its record.

   f. Tear the worktree and branch down:

   ```sh
   <cbm-onboard-skill-directory>/scripts/cbm-teardown.sh <worktree path>
   git -C <control checkout> worktree remove <worktree path>
   git -C <control checkout> branch -D <ticket branch>
   git -C <control checkout> worktree prune
   ```

   A dirty worktree makes `worktree remove` fail. Report that and stop; never force
   it. Then check the remote branch with
   `git ls-remote --heads origin <ticket branch>` and delete it with
   `git push origin --delete <ticket branch>` only if it is still there, since the
   code host usually deletes it on merge.

3. **Record the actuals.** On the merged path only, after cleanup. Read the order's
   shape off the ticket comment (flat or chunked, chunk count, which rubric traits
   triage said fired, the stamped depths), then:

   ```sh
   python3 <ticket-skill-directory>/scripts/ticket.py record <ticket-id> \
     --verb <verb that ran, repeated> \
     --trait <trait that fired, repeated> \
     --depth <stamped depth> \
     [--chunked --chunks <n>]
   ```

   The helper appends one record under `~/.config/ticket/` and returns one verdict.
   A sandboxed session that cannot write that record sees the same one-line
   denial as the claim step, naming the path and the fix: rerun the same
   record command outside the sandbox or with escalated permissions.

   * `ok`: the shape matched what the ticket cost.
   * `under-sliced`: a flat order that peaked past the degradation band.
   * `still-degraded`: a chunked order whose chunks were themselves too big.
   * `over-sliced`: chunks that no single agent would have struggled with.
   * `coordination-degraded`: a chunked order whose chunks all held, but whose
     coordinator peaked past the degradation band.
   * `coordinator-only`: a chunked order where no implementation worker was
     measured, so its cost was recorded but chunk size was not measured.
   * `no-data`: no session claimed this ticket, so nothing measured it.

   The helper reads the sessions that claimed this ticket, so nothing is inferred
   from prose and there is nothing to narrow. A claimed session whose transcript
   has been deleted appears under `unreadable`: report it rather than treating it
   as a session that cost nothing.

   **Roles decide what counts.** This verb's own session claims itself under the
   shared rule's default, `--role coordinator`, like every session that drives a
   ticket rather than building or reviewing one chunk of it. A chunked order's
   slice-size judgment comes from the peaks of the sessions claimed `--role
   worker` and from nothing else. The coordinator's own peak and the reviewers'
   are recorded beside them, as `coordinator_peak` and `reviewer_peak`; the former
   can separately return `coordination-degraded` when every chunk worker held, but
   neither can make a chunked order read as under-sliced: coordinating more chunks
   costs the coordinator more, not less. A flat order is judged on its own
   execution peak, with review-only sessions excluded there too. Claims written
   before roles existed read back as `legacy` and are never guessed into a role,
   which is why a chunked ticket claimed entirely under legacy claims returns
   `coordinator-only`.
   `python3 <ticket-skill-directory>/scripts/ticket.py scan <ticket-id>` reports peak
   context per claimed session without recording anything, which is the way to look
   before committing a record.

   **On `under-sliced`, `still-degraded`, or `over-sliced`, report the misprediction
   and draft the amendment.** Say which rubric call was wrong and by how much, then
   write a concrete diff against
   [references/slicing.md](../references/slicing.md): a trait added or reworded, a
   threshold moved, a new anchor row with this ticket's measured peak. An amendment
   that moves a threshold moves it in both places, the prose and the helper's
   constants, or the two drift apart. Show it to the user; landing it is an ordinary
   pull request they approve. The skill never amends its own rubric, and never edits
   `references/slicing.md` itself.

   `no-data`, `coordinator-only`, and `coordination-degraded` are not
   mispredictions, and none drafts an amendment. `no-data` has two readings the
   report keeps apart: no session claimed the ticket, so it ran outside this
   machine's transcripts, or sessions claimed it and their transcripts are gone.
   `coordinator-only` means the ticket's cost was recorded but its chunk size was
   not measured, so say that plainly — the reason names how many worker claims
   existed and how many were readable, which is the difference between a forgotten
   `--role worker` and a lost transcript. Never report it as evidence that the
   chunks were the wrong size in either direction. `coordination-degraded` means
   the slice was right while the coordinating session was not: report the cost and
   advise carrying less in that session, with fewer review rounds held in its own
   context or a handoff between chunks, never more chunks.

4. **Abandoned path** (pull request closed unmerged, or the work cancelled): comment
   why, then on explicit user confirmation run the same teardown as step 2f. Never
   pick this path without the user confirming. Move the ticket wherever the user
   says, and never pick the terminal state yourself.

5. **Report.** The ticket's state, the comment link, the recorded verdict, and
   anything left open (a red post-merge run, a missing change record, a surviving
   branch or worktree).
