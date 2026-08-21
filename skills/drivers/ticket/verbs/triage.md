# /ticket triage `<ticket-id>`

Turn a ticket into a locked work order, or establish why it cannot be one yet.
Runs entirely in the ticket's worktree, and writes only to the tracker and to
scope and spec documents committed in that worktree.

## Procedure

1. **Read the ticket.** Use the contract's read operation for the description and
   every comment. Note the parent, the links, and any prior work order comment. If
   an order already exists, say so and ask whether to supersede it; a new order
   posted later wins.

2. **Cut or reuse the worktree.** Before any grounding or repo read, derive a short
   kebab slug from the ticket title, then:

   a. Numeric ticket id:

   ```sh
   python3 <spin-worktree-skill-directory>/scripts/spin-worktree.py \
     --repo <control checkout> \
     --issue <ticket-id> \
     --slug <slug> \
     --name <ticket-id>
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

   c. `<prefix>` is whatever `spin-worktree` resolves: its `--branch-prefix` flag,
   else its built-in default. Never invent a prefix here, and keep both paths on the
   same one so the branch name does not depend on which path ran.

   d. Use the worktree path the helper printed as the working directory for every
   step below. If the ticket's worktree already exists, verify it is on the
   ticket's branch (`git -C <worktree> branch --show-current`) and reuse it rather
   than respinning.

   e. The helper refuses on a dirty control checkout or an existing target path.
   Surface that refusal to the user; do not force past it.

3. **Identify the repo or repos.** From the ticket text, its parent, and its links.
   If the target repo does not exist yet, stop: repo scaffolding happens outside
   this skill. Post nothing, and tell the user which ticket has to land first.

4. **Read the standing decisions**, per the skill page's standing-decisions slot,
   before grounding in the repo. Absent, say so in one line and continue. This
   never refuses the ticket.

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
   step. Resolved answers go into the order.

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
   against what grounding found. It decides flat or chunked and, when chunked,
   sizes the chunks and names each one's mode, coherent capability ownership, file
   or target ownership, shared-contract ownership, agent tier, and the orchestrator
   tier. Every capability and shared contract has exactly one owning chunk. A
   parallel chunk must not implement, revise, or depend on another chunk's private
   capability; make that work serial when the dependency is real. Record which
   traits fired and which anchor row the ticket matches; the order carries that
   reasoning, so a wrong call is visible later.

9. **Stamp the review depth.** Read
   [references/review-depth.md](../references/review-depth.md) and stamp one depth
   with a one-line reason on the order, and on each sub-order when chunked. Check
   its sensitivity floor first; the floor overrides any judgment about how small
   the change looks.

10. **Draft the work order.** Apply
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

11. **Adversarial review, mandatory.** Every draft order gets reviewed before it is
    shown to the user or posted; there is no unreviewed path to step 12. Run
    `/plan-review` against the draft: it spawns cold reviewer agents with the
    five-axis rubric (grounding, acceptance, interface shape, scope, cost) and
    returns objections and a verdict. Review depth follows that skill's stakes
    tiering: an ordinary order gets one panel, and a load-bearing one ends only
    when a fresh cold pass returns no blocking objections.

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

    b. Instrument every round in the scope ledger: blockers found, each tagged
    `authoring` (present since the draft) or `injected` (introduced by a prior fix
    round). Injected blockers climbing across rounds is the rewrite-clean signal
    firing.

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

12. **Confirm, then post.** Show the user the draft. On approval, post it as one
    ticket comment through the contract's post operation: attribution quote block
    first, then the human summary, then the fenced order or sub-orders. One comment
    carries the whole order, chunked or not.

13. **Move the status** to triaged. Report a failed move; do not retry.

## Refusals

* The ticket is really a parent: triage the child, not the parent.
* Scope requires decisions only a human can make and the user is unavailable: post
  nothing, and list the open questions in the session.
