# /ticket finalize `<ticket-id>`

Close the loop after a human merged (or abandoned) the pull request. Nothing syncs
the code host back to the tracker; this verb is that sync. Its fresh session claims
`--verb finalize` and never reuses the session that ran start or revise.

## Procedure

1. **Verify the end state.** Read the ticket for the pull request link, then
   `gh pr view <n> --json state,mergedAt,mergeCommit`. Pull request still open:
   refuse, because finalize runs after a merge, not instead of one.

2. **Merged path.**

   a. Confirm the merge: an empty `mergedAt` means not merged, so back to step 1.

   b. Confirm the post-merge workflow succeeded (`gh run list` on the repo). If it
   failed, stop and report; the ticket is not done while the post-merge run is red.

   c. **Archive an ordinary OpenSpec change after the verified merge.** Follow
   `operations.archive.guidance` exactly. In this repository, start from a clean
   `main` checkout updated to `origin/main`, run
   `openspec archive <change-name> --json --yes`, verify its archive JSON, run
   `openspec validate --all --strict`, create a Signed-off-by archive commit, push
   `main` directly, and verify the post-push workflow succeeded. OpenSpec is
   Git-unaware: this verb trusts the verified GitHub merge state and adds no
   enforcement layer. An archive, validation, commit, push, or post-push workflow
   failure stops finalization before the completion comment and done transition.
   An epic child creates no child change record, skips this ordinary-change archive
   procedure, and leaves the parent active and unarchived for the parent epic's
   archive guidance.

   d. Comment on the ticket (attribution first): the merged pull request link, a
   one-line outcome, the post-merge evidence, and, for an ordinary change, the
   completed archive evidence.

   e. Move the ticket to done. Report a failed move; do not retry.

3. **Record the actuals.** On the merged path only. When record needs a target
   worktree, do this before cleanup; otherwise it may follow cleanup. Read the
   order's shape off the ticket comment (flat or chunked, chunk count, which rubric
   traits triage said fired, the stamped depths), then:

   ```sh
   python3 <ticket-skill-directory>/scripts/ticket.py record <ticket-id> \
     --verb <verb that ran, repeated> \
     --trait <trait that fired, repeated> \
     --depth <stamped depth> \
     [--chunked --chunks <n>] \
     [--project <target-worktree>]
   ```

   When the ticket ran outside the coordinator's own checkout, pass its target
   worktree through `--project` on both `record` and any preceding `scan`:

   ```sh
   python3 <ticket-skill-directory>/scripts/ticket.py scan <ticket-id> \
     --project <target-worktree>
   ```

   Record before removing that target worktree in step 4, so its repository
   identity is still available to the helper.

   The helper prints one JSON record and returns one verdict. The existing next
   step appends those same captured bytes to reviewer memory.

   Retain a successful record command's standard output in `record_json` and
   print it once for the coordinator. Then pipe those same captured bytes, without
   rerunning `record`, into reviewer memory:

   ```sh
   printf '%s\n' "$record_json" |
     python3 <reviewer-memory-skill-directory>/scripts/memory.py append-slicing <repo>
   ```

   `<repo>` is the ticket's target repository, matching the repository identity
   resolved from `--project` when that option is present. Obey the
   [reviewer-memory failure rule](../../../tools/reviewer-memory/SKILL.md#failure-rule),
   including its not-installed carve-out.

   Keep the record and store content local; never copy them into a tracker comment,
   work order, pull request body, or target-repository file.

   * `ok`: the shape matched what the ticket cost.
   * `under-sliced`: a flat order that peaked past the degradation band.
   * `still-degraded`: a chunked order whose chunks were themselves too big.
   * `over-sliced`: chunks that no single agent would have struggled with.
   * `coordination-degraded`: a chunked order whose chunks all held, but whose
     coordinator peaked past the degradation band.
   * `coordinator-only`: a chunked order where no implementation worker was
     measured, so its cost was recorded but chunk size was not measured.
   * `unmeasurable`: claimed sessions supplied no usable peak, so no slicing
     call was made.
   * `no-data`: no session claimed this ticket, so nothing measured it.

   The helper reads the sessions that claimed this ticket, so nothing is inferred
   from prose and there is nothing to narrow. A claimed session whose transcript
   has been deleted appears under `unreadable`: report it rather than treating it
   as a session that cost nothing.

   **Role and lifecycle verb decide what counts.** This verb's own session claims
   `--verb finalize --role coordinator`, like every session that drives a ticket
   rather than building or reviewing one chunk of it. A chunked order's
   slice-size judgment comes from the peaks of the sessions claimed `--role
   worker` and from nothing else. The coordinator's own peak and the reviewers'
   are recorded beside them, as `coordinator_peak` and `reviewer_peak`; the former
   can separately return `coordination-degraded` when every chunk worker held, but
   neither can make a chunked order read as under-sliced: coordinating more chunks
   costs the coordinator more, not less. A flat order is judged only from measurable
   non-reviewer sessions claimed `--verb start`; triage, revise, finalize, and
   reviewer costs remain visible as overhead and never change that verdict. Claims
   written before lifecycle verbs existed read back with verb `legacy` and are never
   guessed into a phase. Attributable claims without measurable eligible start
   evidence return `unmeasurable`, while no attributable claim remains `no-data`.
   Because a transcript is the measurement unit, every lifecycle verb runs in its
   own session; only same-verb resumes reuse a claim. Claims written before roles
   existed also keep role `legacy`, which is why a chunked ticket claimed entirely
   under legacy roles returns `coordinator-only`.
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

   `no-data`, `unmeasurable`, `coordinator-only`, and `coordination-degraded` are not
   mispredictions, and none drafts an amendment. `no-data` has two readings the
   report keeps apart: no session claimed the ticket, so it ran outside this
   machine's transcripts, or claims for another repository were excluded.
   `unmeasurable` means this repository had claims but no measurable eligible start
   execution on a flat order, or their transcripts or Codex rollouts supplied no
   usable peak; say which reason the helper names.
   `coordinator-only` means the ticket's cost was recorded but its chunk size was
   not measured, so say that plainly — the reason names how many worker claims
   existed and how many were readable, which is the difference between a forgotten
   `--role worker` and a lost transcript. Never report it as evidence that the
   chunks were the wrong size in either direction. `coordination-degraded` means
   the slice was right while the coordinating session was not: report the cost and
   advise carrying less in that session, with fewer review rounds held in its own
   context or a handoff between chunks, never more chunks.

4. **Tear the worktree and branch down.** On the merged path only, after recording
   actuals:

   ```sh
   <cbm-onboard-skill-directory>/scripts/cbm-teardown.sh <worktree path>
   rm -f <worktree path>/ORDER.md
   git -C <control checkout> worktree remove <worktree path>
   git -C <control checkout> branch -D <ticket branch>
   git -C <control checkout> worktree prune
   ```

   A dirty worktree makes `worktree remove` fail. Report that and stop; never force
   it. Then check the remote branch with
   `git ls-remote --heads origin <ticket branch>` and delete it with
   `git push origin --delete <ticket branch>` only if it is still there, since the
   code host usually deletes it on merge.

5. **Abandoned path** (pull request closed unmerged, or the work cancelled): comment
   why, then on explicit user confirmation run the same teardown as step 4. Never
   pick this path without the user confirming. Move the ticket wherever the user
   says, and never pick the terminal state yourself.

6. **Report.** The ticket's state, the comment link, the recorded verdict, and
   anything left open (a red post-merge or post-push run, a failed archive, a
   surviving branch or worktree).
