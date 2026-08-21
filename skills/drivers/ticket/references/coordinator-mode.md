# Coordinator mode

Reached from `start` step 6, on a chunked order only. `/orchestrate`'s rules bind:
delegate the work, verify every result, never write the implementation yourself.
Its carve-out binds too, and this flow leans on it twice: small mechanical glue
stays with the coordinator, so a mechanical merge conflict (step 5) and a finding
whose chunk agent is already gone (step 8) are fixed in place and mentioned in the
report. Anything larger than mechanical goes back to a delegate.

What follows is what this skill adds on top. It replaces `start` steps 8 through
11, and rejoins that verb at step 12 when the last chunk has merged.

1. **One branch, one pull request, still.** The ticket branch from `start` step 4 is
   the trunk. Each chunk gets its own branch cut from it and merges back. Nothing
   chunk-related reaches the default branch directly.

2. **Spin a worktree per chunk**, from the ticket branch rather than from the remote
   default branch:

   ```sh
   git -C <control checkout> branch <ticket branch>-c<n> <ticket branch>
   python3 <spin-worktree-skill-directory>/scripts/spin-worktree.py \
     --repo <control checkout> \
     --branch <ticket branch>-c<n> \
     --name <ticket-id-lowercased>-c<n>
   ```

   Creating the chunk branch locally first starts it from the ticket branch's own
   tip, so the ticket branch does not need to be pushed. Spin parallel chunks'
   worktrees together, and serial ones only once their predecessor has merged into
   the ticket branch, because a serial chunk cut early misses the work it depends on.

3. **Dispatch one agent per chunk** at the tier its `Agent:` line names, with the
   working directory set to that chunk's worktree. The prompt is the sub-order fence
   verbatim, plus the worktree path and the branch name. Nothing else: a sub-order
   that needs coordinator commentary to be executable is a triage defect, and the fix
   is to say so, not to patch it in the prompt.

   `Surface lifecycle:` is part of that executable interface. Before dispatch,
   confirm every UI-affecting sub-order says `build` or `revise` and names the lock
   manifest or shipped behavior ledger/replay that mode consumes. On a rendered-
   surface chunk, `none`, a missing legacy field, or a missing contract is a triage
   defect. The worker loads the named UI Craft mode before implementing its `Do`
   section; non-UI chunks keep `none`.

   Once the dispatcher exposes a stable transcript id, claim each unique
   implementation-worker session through the shared claim rule, passing
   `--session <id>`, `--agent <agent>`, and `--project <chunk-worktree>`. The agent
   and project name the worker that did the work and its actual working directory,
   not the coordinator's. Keep identifiers in coordinator bookkeeping; they never
   enter sub-order prompts or published comments. If the dispatcher exposes no
   stable transcript id, report the omitted claim in one line and continue. Claim
   failures use the shared visible, non-blocking rule.

4. **Review each chunk as it lands**, at that sub-order's stamped depth, before
   merging it. Two things happen, in order, and neither substitutes for the other:

   a. Dispatch a reviewer agent at the tier
   [review-depth.md](review-depth.md) sets for that chunk, on the chunk's branch
   against the ticket branch. A chunk built by Sonnet is reviewed by Sonnet, a Haiku
   chunk by Sonnet, a Full-depth chunk by Opus. Findings go back to the chunk's own
   agent to fix.

   b. Verify the result yourself, as `/orchestrate` requires of every delegated
   result: read the diff, run the verification command, check the chunk's Done when
   clause. A failed verification retries once in the chunk's agent with the specific
   finding, then escalates one tier per the routing table. Same-session retries are
   not re-claimed; claim every fresh implementation escalation once, using the
   escalation's stable transcript id, agent, and chunk worktree. Review-only
   sessions are not claimed in this issue; role-aware review attribution belongs to
   ticket 77.

5. **Merge into the ticket branch** in the ticket's worktree, one chunk at a time,
   with `--no-ff`. A conflict between two chunks that declared disjoint ownership
   means the slice was wrong: resolve it yourself only when it is mechanical, and say
   so in the report; anything else goes back to the user as a slicing defect. After a
   chunk merges, remove its worktree and delete its branch
   (`git -C <control checkout> worktree remove <path>` then
   `git -C <control checkout> branch -D <chunk branch>`). Chunk branches are never
   pushed, so there is no remote branch to delete.

6. **Record the change yourself**, on the ticket branch, after the chunks have
   merged, per the skill page's change-record rule. Chunks never touch it, which is
   why parallel chunks cannot collide there.

7. **Run the verification command on the merged branch**, not per chunk. The order's
   expectation describes the whole ticket.

8. **Repo-rules audit, then whole-diff review, before the pull request.** Re-read the
   repo's `AGENTS.md` or `CLAUDE.md` and audit the merged diff against it rule by
   rule, including any completion checklist it defines, exactly as the flat path
   does; chunk agents each saw only their own slice, so nothing has audited the whole.
   Fix violations, then run `/review` on the ticket branch against the default
   branch, at the depth [review-depth.md](review-depth.md) sets for a whole diff.
   Findings route back to the chunk agent that owns the file when its session is
   still alive, and otherwise the coordinator fixes them and says so.
