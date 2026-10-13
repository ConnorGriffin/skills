# /ticket start `<ticket-id>`

Build to the locked order in a fresh session. The output is one open pull request.

## Procedure

1. **Open and claim** per shared rules 1 and 2, before locating the order.

2. **Locate and admit the lock.** Use the tracker's locate operation. No order: refuse
   with "no work order on `<ticket-id>`; run /ticket triage `<ticket-id>`" and stop.
   Then, from the ticket worktree, every check below must pass; any failure names the
   check, refuses, and routes to `/ticket triage <ticket-id>`. Never fall back to an
   older comment and never patch a field from one.

   * The fence is `EXECUTION LOCK v2` (or a legacy `WORK ORDER`, read as `inline`), with
     a `Source:` mode of `openspec`, `repository-native`, or `inline`.
   * `Verification:`, `Expectation:`, and `Expected diff` are present and non-empty.
   * **Pinned sources only:** `git cat-file -e <oid>^{commit}` resolves the full OID;
     `git ls-tree <oid> -- <path>` finds the source; `git merge-base --is-ancestor <oid>
     HEAD` holds (never substitute the branch head for the pin).
   * **Pinned sources only:** `git diff <oid> HEAD -- <path>` shows nothing but
     `tasks.md` checkbox ticks. Any other edit is an amendment that needs a newer lock.
   * **`openspec` only:** the change is active, not archived, and
     `openspec validate <change> --strict` passes at the pinned tree.
   * The `Surface lifecycle:` contract still meets the template's rule: every screen it
     names is locked in the lock doc, and `revise` has its safe start.
   * The classification is not `manual`; a manual order has nothing to execute.

3. **Reuse the worktree** triage cut, confirming `git -C <worktree> branch
   --show-current`. Respin it the way triage did only when it is gone. Move the ticket to
   in progress.

4. **Build.** Read the repo's `AGENTS.md`/`CLAUDE.md`; its rules bind every line on this
   branch. Execute the pinned tasks or the `Do` steps and nothing outside `Expected diff`.
   * New behavior with testable acceptance goes test-first through `/tdd`, with a test
     that fails for the right reason before the fix.
   * `Surface lifecycle: build` runs `/ui-craft build` against the lock doc; `revise`
     runs `/ui-craft revise` against the lock doc and its must-survive list.
   * A new module or interface loads `/codebase-design` first; CI changes read
     `/ci-design`.
   * Probe a CLI or API with `--help` or a real call before coding against it, and
     prove a security or confinement claim by attempting the forbidden action.
   * Tick `tasks.md` as each item is done and verified.

5. **Verify until it matches.** Run `Verification:` locally and iterate until the output
   matches `Expectation:`. CI is the check of record, not the loop. When it cannot run
   at all (no credentials, no runnable suite), stop building, open the pull request as a
   draft, and name the missing evidence. Never fabricate output.

6. **Review once.** Re-read the repo's `AGENTS.md`/`CLAUDE.md` and audit the full diff
   against it. Then run one `/code-review` of the branch since the default branch at the
   stamped depth, with the order as the spec; it dispatches its own fresh-context
   reviewer. Fix each confirmed finding, re-run step 5 if code changed, and carry
   anything still open into the pull request body as known issues. Under
   `Profile: hardening`, follow the skill page's hardening rule instead.

7. **Prove the change applies** (OpenSpec tickets only; other conventions skip this).
   Run `git fetch origin`, then:

   ```sh
   python3 <ticket-skill-directory>/scripts/ticket.py preflight-openspec \
     --repo <ticket-worktree> --base-ref refs/remotes/origin/HEAD
   ```

   It archives the change in a disposable copy of the current baseline. A failure stops
   here; fix the delta rather than opening the pull request.

8. **Open the pull request** with `gh pr create` against the default branch. Use the
   repo's pull-request template when it has one, keeping its headings and ticking only
   what was done. Write the body for the human who merges, in the app's own domain
   terms: what changed, why, and what to check, never a tour of file names. Add the
   verification output in a fence and a link to the ticket. UI work attaches its
   lifecycle evidence: a render per approved screen, frame, and state plus the precheck
   output for `build`; before/after render pairs, the must-survive checks, and the
   precheck output for `revise`. Move the ticket to
   pending review and comment the pull request link on it.

9. **Stop.** Report the pull request URL, the verification evidence, the review findings
   fixed or carried, and anything left undone. Do not merge, approve, or answer reviews;
   that is `/ticket revise`.
