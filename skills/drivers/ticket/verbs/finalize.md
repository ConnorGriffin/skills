# /ticket finalize `<ticket-id>`

Close the loop after a human merged (or abandoned) the pull request. Nothing syncs the
code host back to the tracker; this verb is that sync.

## Procedure

1. **Open and claim** per shared rules 1 and 2, with `--verb finalize`.

2. **Verify the merge.** `gh pr view <n> --json state,mergedAt,mergeCommit`. Still open:
   refuse; finalize follows a merge, never replaces one. Closed unmerged: go to step 7.
   Then confirm the post-merge workflow is green with `gh run list`; a red run stops here.

3. **Archive through a reviewed pull request** (OpenSpec changes only). The archive takes two
   finalizations, because a human merges it. Scan the ticket's comments newest-first for
   `Archive PR: <url>`.

   * **None yet.** Follow the repo's `operations.archive.guidance`: in a sibling archive
     checkout of an updated `main`, cut an archive branch, run `openspec archive
     <change> --json --yes`, run `openspec validate --all --strict`, commit with
     `Signed-off-by`, push the branch, and open a pull request against `main`. Never push
     an archive commit to `main`. Comment on the ticket with the merged pull request, the
     post-merge evidence, and a line `Archive PR: <url>`, then stop: the ticket is not
     done. Any failure stops here and leaves the branch and checkout for the operator.
   * **Found.** `gh pr view <archive-pr> --json state,mergedAt`. Open: report it pending
     human review and stop. Closed unmerged: stop for operator direction; never open a
     replacement. Merged: confirm its post-merge run is green, then continue.

4. **Close the ticket.** Comment the merged pull request, a one-line outcome, the
   post-merge evidence, and the merged archive pull request when there is one. Move the
   ticket to done.

5. **Record what it cost**, before removing the worktree:

   ```sh
   python3 <ticket-skill-directory>/scripts/ticket.py record <ticket-id> \
     --verb <each verb that ran> [--trait <each trait triage recorded>] \
     --depth <stamped depth> [--project <ticket worktree>]
   ```

   Print a successful record command's standard output once. Keep the record local;
   never copy it into a tracker comment, work order, pull request body, or the repo.

   Report the verdict. `under-sliced` means a flat order peaked past the ~180k band: say
   which traits triage read and what peak contradicted the call. `no-data` and
   `unmeasurable` mean nothing usable was claimed; say which. Never edit the slicing rule
   or propose a change to it here.
   `ticket.py scan <ticket-id>` shows per-session peaks without recording anything.

6. **Tear down.**

   ```sh
   git -C <control checkout> worktree remove <worktree path>
   git -C <control checkout> branch -D <ticket branch>
   git -C <control checkout> worktree prune
   ```

   A dirty worktree makes `worktree remove` fail: report it and stop, never force.
   Delete the remote branch with `git push origin --delete <ticket branch>` only if
   `git ls-remote --heads origin <ticket branch>` still lists it. Retire the archive
   checkout and its branch the same way.

7. **Abandoned path** (closed unmerged, or cancelled): comment why, then tear down per
   step 6 (without the archive checkout) and move the ticket only after the user
   confirms and names the state. Never choose the terminal state yourself.

8. **Report** the ticket's state, the comment link, the recorded verdict, and anything
   left open: a red run, a failed or pending archive, a surviving branch or worktree.
