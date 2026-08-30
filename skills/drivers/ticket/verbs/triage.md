# /ticket triage `<ticket-id>`

Turn a ticket into a locked work order, or establish why it cannot be one yet.
Runs in the ticket's worktree. Outside an epic it writes the tracker and the
applicable scope and spec documents there. An **epic child** creates no per-child
change record. Its review instrumentation stays in untracked session scratch, while
any required parent-plan amendment is committed in the child worktree and travels
with the implementation pull request; the parent epic retains archive ownership.

Use the shared selected-ticket mutation boundary. Keep grounding broad and
read-only. When a distinct external prerequisite would otherwise contradict a
recorded destination, constraint, acceptance criterion, risk, or sequence, cite
that clause, disclose the exact external target and mutation, and stop before
mutation until a subsequent operator response explicitly authorizes the previously
disclosed target and exact mutation.

## Procedure

1. **Read the ticket.** Use the contract's read operation for the description and
   every comment. Note the parent, the links, and any prior work order comment. If
   an order already exists, say so and ask whether to supersede it; a new order
   posted later wins. A non-null parent is only an epic-child candidate: read that
   parent through the tracker contract and select the epic-child lifecycle only
   when its labels include the `epic` label. A missing parent or a parent without
   `epic` leaves this as an ordinary ticket.

2. **Cut or reuse the worktree.** Verify an epic-child draft first. Before any
   grounding or repo read, derive a short kebab slug from the ticket title.

   For a fresh epic-child worktree, treat the issue-body draft as untrusted input.
   Require exactly one `Parent plan base: <parent-plan branch>@<pinned full commit>`
   field, with an unprefixed remote branch name and a full commit. Then run:

   ```sh
   git -C <control checkout> fetch origin
   git -C <control checkout> rev-parse origin/<parent-plan branch>
   ```

   Require the resolved commit to equal the pinned full commit exactly. Resolve the
   branch only as `origin/<parent-plan branch>`; never accept a local branch or an
   abbreviated commit. A missing or mismatched value is a stale draft: post nothing,
   create no worktree, and return to the attended epic session for a new issue-body
   draft and pin.

   Then cut or reuse the worktree:

   a. Numeric ticket id:

   ```sh
   python3 <spin-worktree-skill-directory>/scripts/spin-worktree.py \
     --repo <control checkout> \
     --issue <ticket-id> \
     --slug <slug> \
     --name <ticket-id> \
     [--base <parent-plan branch>]
   ```

   b. Non-numeric ticket id: create the branch ref from the remote default branch
   first, without switching the control checkout, then spin the worktree onto it:

   ```sh
   git -C <control checkout> fetch origin
   git -C <control checkout> branch <prefix>/<ticket-id-lowercased>-<slug> origin/<default branch>
   python3 <spin-worktree-skill-directory>/scripts/spin-worktree.py \
     --repo <control checkout> \
     --branch <prefix>/<ticket-id-lowercased>-<slug> \
     --name <ticket-id-lowercased>
   ```

   For an epic child, the bracketed `--base <parent-plan branch>` is required and
   receives the same unprefixed branch name verified above. For an ordinary ticket,
   omit it.

   c. `<prefix>` is whatever `spin-worktree` resolves: its `--branch-prefix` flag,
   then `branchPrefix` in `~/.config/spin-worktree/config.json`, else no prefix.
   When no prefix resolves, omit `<prefix>/` entirely. Never invent a prefix here,
   and keep both paths on the same one so the branch name does not depend on which
   path ran.

   d. Use the worktree path the helper printed as the working directory for every
   step below. If the ticket's worktree already exists, verify it is on the
   ticket's branch (`git -C <worktree> branch --show-current`) and reuse it rather
   than respinning.

   e. A dirty control checkout is valid: leave its files untouched and spin from
   it directly. Never search the existing task worktrees for a clean substitute.
   The helper still refuses an existing target path; surface that refusal to the
   user rather than forcing past it.

   f. Bind that worktree's graph identity before grounding, per the skill page's
   graph-identity rule, and report what it printed. A reused worktree gets the same
   check: the identity is recomputed here every session, never remembered from the
   run that cut it.

3. **Identify the repo or repos.** From the ticket text, its parent, and its links.
   If the target repo does not exist yet, stop: repo scaffolding happens outside
   this skill. Post nothing, and tell the user which ticket has to land first.

4. **Read the standing decisions**, per the skill page's standing-decisions slot,
   before grounding in the repo. Absent, say so in one line and continue. This
   never refuses the ticket.

   Then, for each target repo, run:

   ```sh
   python3 <reviewer-memory-skill-directory>/scripts/memory.py ensure <repo>
   ```

   Read the store index path it names, following links only where relevant to the
   ticket. When it reports an empty bundle, say so in one line and continue. Keep
   the index and store content in worker prompts only; never copy them into the
   work order, a tracker comment, a pull request body, or the target repository.
   Obey the [reviewer-memory failure rule](../../../tools/reviewer-memory/SKILL.md#failure-rule),
   including its not-installed carve-out.

5. **Ground.** In each target repo:

   a. The repo's own change and decision records, active and archived.

   b. `docs/` (architecture, runbooks), `README`, `CONTRIBUTING`, and the repo's
   `AGENTS.md` or `CLAUDE.md`.

   c. `git log --oneline -30`, plus recent pull requests touching the same area.

   d. The CI workflows that will judge the change.

   Record what the repo already decided that constrains this ticket.

   **Verify live state live, never from docs or ticket comments.** Any claim the
   order depends on about what exists right now (a deployed resource, repository
   secrets, required checks) gets checked against the live source: run the
   read-only describe, hit the API, list the state. Repo docs and prior ticket
   comments both go stale, in opposite directions: one measured triage found the
   repo claiming a production target did not exist while a ticket comment claimed
   the platform work was done, and both were part right. A wrong premise here
   poisons every downstream decision in the order.

   **When the change alters documented behavior, build a closed document
   inventory.** Grep the repo for the behavior's terms (the command, the setting,
   the promise) across all docs, templates, and comments. Never sample the docs you
   already know about. The order lists the inventory, so review checks it for
   completeness instead of discovering documents one per round; one measured review
   leaked one stale document per round for four rounds because each pass sampled
   instead of searching.

   **Route the grounding by ticket shape.** A bug report is reproduced before
   anything is drafted, and the reproduction goes into the order. A ticket touching
   CI or a workflow file reads `/ci-design` before the order is drafted.

6. **Classify.** One of:

   * `code`: lands as a pull request.
   * `investigation`: the deliverable is findings on the ticket, no pull request.
   * `manual`: human-only operational work. Triage still grounds and scopes it, but
     the order says what a human does, not what an agent implements.

7. **Run `/scope`, always, unconditionally.** After grounding and classification,
   invoke it with the ticket summary and what grounding found. It classifies the
   dominant uncertainty and routes it, and its interview is the only interface for
   putting decisions to the user. Never present findings and free-form questions
   instead. A single missing fact with no judgment attached (a hostname, a version)
   is the only exception. When nothing is genuinely uncertain, scope says so and
   returns without asking anything; that outcome is the pass signal, not a wasted
   step. Resolved answers go into the order. The epic issue-body draft enters this
   ordinary grounding, scope, and mandatory-review path; it is never executable by
   itself. For an epic child, every `/scope`
   specialist keeps its instrumentation in untracked session scratch outside the branch, discards it
   after the final order, and creates no scope ledger or docs/scope state. `/epic` alone owns the
   proposal, design, and tasks. If triage discovers a required parent-plan
   amendment, edit and commit it in the child worktree, include those paths and
   acceptance effects in mandatory review, and carry it into the order that will
   govern the implementation pull request. This is still the parent active change,
   not a per-child change record.

   **Resolve the surface lifecycle.** Every order and sub-order gets one closed
   `Surface lifecycle:` value:

   * `none` when it changes no rendered surface.
   * `build` for a greenfield surface after `/ui-craft lock`, or for UI Craft's
     explicit shipped-surface fallback. Name the lock manifest; on fallback also
     name the predecessor behavior ledger and replay.
   * `revise` for a shipped surface. Run UI Craft's setup/router during triage,
     confirm its safe-start declaration and manufactured data source, and name the
     frozen behavior ledger and replay that execution will use. Triage records the
     route but does not start the app or implement the revision.

   A UI Craft refusal or ambiguous route blocks the order. In a chunked order the
   header carries the one non-`none` lifecycle active across the whole diff and
   every sub-order carries its own; an affected sub-order must repeat the contract
   paths it needs to stand alone. If chunks would mix `build` and `revise`, split
   them into separate tickets instead of adding another lifecycle value.

8. **Decide the shape: flat or chunked.** Read
   [references/slicing.md](../references/slicing.md) and run its trait rubric
   against what grounding found. The rubric carries the traits and the thresholds;
   this repo's own anchors live in its reviewer-memory slicing records, so read
   those for the shapes and measured peaks the traits are calibrated against here,
   and say when a nearby record contradicts the call the rubric points at. The
   rubric decides flat or chunked and, when chunked,
   sizes the chunks and names each one's mode, coherent capability ownership, file
   or target ownership, shared-contract ownership, agent tier, and the orchestrator
   tier. Every capability and shared contract has exactly one owning chunk. A
   parallel chunk must not implement, revise, or depend on another chunk's private
   capability; make that work serial when the dependency is real. Record which
   traits fired and which reviewer-memory anchor or record the ticket matches, or
   that the store held no nearby anchor; the order carries that reasoning, so a
   wrong call is visible later.

9. **Stamp the review depth.** Read
   [references/review-depth.md](../references/review-depth.md) and stamp one depth
   with a one-line reason on the order, and on each sub-order when chunked. Check
   its sensitivity floor first; the floor overrides any judgment about how small
   the change looks.

10. **Stamp the profile.** Read the target repo's `CLAUDE.md` or `AGENTS.md` repo
    facts for a `Harden:` line. When the user or ticket asks for the hardening
    profile and that line exists, stamp `Profile: hardening` and write the QA script
    from the acceptance criteria. When the line is absent, stamp `Profile: none`,
    say so in the order's Context, and continue with the default workflow. Stamp
    `Profile: none` on every chunked order: the profile is flat-only.

11. **Draft the work order.** Read
    [drafting conventions](../references/drafting-conventions.md), apply
    [references/brief-quality.md](../references/brief-quality.md), then fill
    [templates/work-order.md](../templates/work-order.md), the flat shape or the
    chunked shape per step 8, and run that page's two authoring checks before the
    draft leaves this step. Each fenced block must be self-sufficient for a fresh
    session: a competent agent with only the ticket and that one block should
    produce the right change. Name files and targets concretely. State what must
    not change. Set the verification command and its expectation. In a chunked
    order, no sub-order may reference another sub-order's content. Every chunk
    names its coherent capability and its files or targets; every capability and
    shared contract has exactly one owning chunk, so parallel chunks cannot collide
    or depend on private capability. Check that every fence's `Surface lifecycle:`
    value matches the route and contract artifacts settled in step 7.

For a flat order, copy the already-selected execution row's `Ladder` value from [`routing-table.md`](../../orchestrate/references/routing-table.md) into the template's `Session fit:` paragraph, keeping each model's display name and ladder order.

### Chunked session fit

For a chunked order, select one coordinator execution row with the same grounded, fail-closed classification rule that selects a flat order's execution row. Copy that row's `Ladder` value into exactly one `Session fit:` paragraph in every sub-order fence, keeping each model's display name and ladder order, and annotate each paragraph with exactly one `selected Agent rung: <Rung>`. A missing, duplicate, malformed, unresolved, or ineligible ladder or selected rung returns through `/scope` and produces no draft or comment.

12. **Adversarial review, mandatory.** Every draft order gets reviewed before it is
    shown to the user or posted; there is no unreviewed path to step 13. A
    delegated `triage` worker returns its review-ready draft to its coordinator
    through the coordinator-recorded durable result locator, then stops at this
    boundary. Its coordinator dispatches `/plan-review`, verifies the verdict, and
    resumes the same worker with actionable findings or a verified clean verdict.
    The worker must not launch a nested reviewer. A coordinator-run triage runs
    `/plan-review` against the draft directly: it spawns cold reviewer agents with the
    five-axis rubric (grounding, acceptance, interface shape, scope, cost) and
    returns objections and a verdict. Review depth follows that skill's stakes
    tiering: an ordinary order gets one panel, and a load-bearing one ends only
    when a fresh cold pass returns no blocking objections.
    The ticket skill page's `## Delegation authority` section covers this mandatory
    `/plan-review`.

    When the stamped profile is hardening, run `/plan-review` only on Full-depth
    orders. Default-workflow orders keep this review unconditionally.

    Triage-specific additions on top of that skill:

    a. Verify every finding against ground truth (the repo, a provider's source,
    live state) before acting on it, and carry verified facts forward in each next
    reviewer's prompt so settled points do not re-litigate. This gate is
    structural, not advisory: no objection reaches a fix round until its factual
    claims are reproduced (execute the regex, parse the shell, open the cited
    file), and the fix-round prompt carries the evidence per objection. A claim
    that fails reproduction is recorded as refuted and never forwarded. One
    measured review forwarded a single unverified reviewer claim; it got baked into
    the order and cost a full round to retract.

    b. Outside an epic child, instrument every round in the scope ledger:
    blockers found, each tagged `authoring` (present since the draft) or
    `injected` (introduced by a prior fix round). For an epic child, keep the same
    instrumentation in untracked session scratch outside the branch and discard it after the final
    order; create no scope ledger or docs/scope state. The reviewed parent-plan amendment from
    step 7 is the only planning artifact this child branch may write. Injected blockers climbing
    across rounds is the rewrite-clean signal firing.

    c. Reviewers get the facts already verified live this session and the user's
    settled decisions, marked do-not-re-litigate.

    d. Each objection states the claim or gap, the evidence (file and line, or the
    live query), why it breaks the build if unfixed, and the cheapest fix, marked
    **blocks posting** or **note**. Anything that would not change what gets built
    is discarded rather than reported. Taste is not an objection. An empty list on a
    sound order is a successful review.

    e. Chunked orders get one more axis: does each sub-order stand alone in a fresh
    agent; does every capability and shared contract have exactly one owning chunk;
    are two parallel chunks' file, target, and capability ownership disjoint; and
    does the serial ordering reflect a real dependency rather than habit. A chunk
    failing any of those is a blocking objection.

    Hard cap at three review panels regardless of tier. Blocking objections still
    arriving at the cap mean the order has unsettled decisions, not undiscovered
    typos: route them through `/scope` (step 7) and stop drafting until it resolves
    them. When rounds accumulate, rewrite the order clean instead of patching it; in
    one measured run, roughly a third of late findings were defects the patches
    themselves introduced. Stop earlier when a round yields only wording polish,
    because the executing agent grounds in the same repo and resolves polish itself.

13. **Confirm, then post.** Show the user the draft. On approval, post it as one
   ticket comment through the contract's post operation: attribution quote block
   first, then the human summary, then the fenced order or sub-orders. One comment
   carries the whole order, chunked or not. For an epic child, this is the only
   fenced `WORK ORDER` and the only execution lock; the issue-body draft never
   substitutes for it.

14. **Move the status** to triaged, passing the classification from step 6. Report
    a failed move; do not retry. A failed code classification `build` creation or
    attachment retains the posted work order but prevents `ticket:triaged`.

## Refusals

* The ticket is really a parent: triage the child, not the parent.
* Scope requires decisions only a human can make and the user is unavailable: post
  nothing, and list the open questions in the session.
