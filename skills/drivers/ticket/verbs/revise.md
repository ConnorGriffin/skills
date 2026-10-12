# /ticket revise `<ticket-id>`

Action one review round on the ticket's open pull request. The output is that round,
pushed and answered.

## Procedure

1. **Open and claim** per shared rules 1 and 2, with `--verb revise`.

2. **Reload.** Read the ticket for the pull request link, then
   `gh pr view <url> --json state,headRefName,baseRefName,reviews,comments` and
   `gh pr checks <url>`. Merged or closed: stop and point at `/ticket finalize`. No pull
   request: point at `/ticket start`.

3. **Worktree.** Reuse the ticket's worktree when `git -C <worktree> branch
   --show-current` equals `headRefName`. Otherwise remove it if `git status --short` is
   empty (stop and report if not; never force) and work in a fresh worktree on
   `headRefName`, fetched up to date from `origin`.

4. **Re-admit the lock.** Locate the newest lock fresh and run [start](start.md) step 2's
   checks against this worktree. A newer lock posted since start is the one this round
   works under; a source amendment with no newer lock refuses.

5. **Collect the round.** List every unresolved review comment (human and automated),
   failing check, and new CI output before touching code. Ground each item, then give it
   exactly one disposition:

   * **Fix:** it breaks the order's `Done when`, its verification, or a named repo rule.
   * **Follow-up:** real but outside the order. File an issue with evidence and a checked
     duplicate search, and keep it out of this pull request.
   * **Ask the maintainer:** a real choice remains.
   * **Discard:** reviewer preference; reply with why.

   A fix that needs the pinned source changed beyond what the lock pinned needs a
   newer lock from `/ticket triage` first. A review asking for something the order
   forbids goes to the user.

6. **Fix with the same worker.** When start delegated the build, resume that worker with
   `SendMessage` and the dispositioned list rather than starting a new one.

7. **Rebase once.** `git fetch origin`, then rebase onto `origin/<baseRefName>`. A
   conflict you cannot resolve safely: abort and surface it. Never retry.

8. **Verify and review.** Re-run the order's verification until it matches, audit the
   new changes against the repo's `AGENTS.md`/`CLAUDE.md`, and run one `/code-review` of
   them at the stamped depth (or the hardening rule). Update the change record if its
   checklist or a decision moved.

9. **Push.** OpenSpec tickets first `git fetch origin` and run start step 7's
   `preflight-openspec` with `--base-ref origin/<baseRefName>`; a failure stops before
   the push. Push the same branch and reply to each addressed comment. Comment on the
   ticket only when the round changed the plan.
