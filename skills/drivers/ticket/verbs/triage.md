# /ticket triage `<ticket-id>`

Turn a ticket into a locked work order, or say why it cannot be one yet. The output is
one artifact: the order, posted on the ticket after the user approves it.

## Procedure

1. **Read the ticket** through the tracker contract, with every comment. An existing
   order: say so and ask whether to supersede it. A parent ticket whose checklist tracks
   child issues is not triaged itself: triage the next open child instead.

2. **Cut or reuse the worktree** before reading the repo. Work in a fresh worktree off
   the up-to-date remote base: fetch `origin`, then cut a branch named
   `<id-lowercased>-<slug>` (a short kebab slug from the title) from
   `origin/<default branch>` into its own worktree, or use the harness's native worktree
   isolation. A reused worktree must be on the ticket's branch. Never force.

3. **Ground.** Follow shared rule 6 for each target repo. A target repo that does not
   exist yet stops triage: name the ticket that has to land first.

   * **Live state is checked live.** A claim about what exists now (a deployed resource,
     a secret, a required check) gets a read-only command run now, not a doc or comment.
   * **A bug is reproduced** before anything is drafted, and the reproduction goes in
     the order.
   * **Changed documented behavior** gets a grep for its terms across every doc, and the
     order lists the complete inventory.
   * **CI or workflow changes** read `/ci-design` first.

4. **Classify:** `code` (lands as a pull request), `investigation` (findings on the
   ticket, no pull request), or `manual` (a human does it; the order says what).

5. **Resolve the dominant uncertainty.** Name the one uncertainty that, once settled,
   makes the rest tractable, and handle it before drafting:

   | Uncertainty | Move |
   |---|---|
   | None: the decisions are settled or have obvious defaults | Say so in one line, name the defaults, and continue. |
   | A decision only the user can make | Ask in rounds: every question whose prerequisites are settled goes in one numbered round, each with options, costs, and a recommendation. |
   | A fact the docs or sources can answer | `/research`. |
   | A load-bearing assumption nobody has run | Spike the first hour (below). |
   | Behavior only running code can show | `/prototype`. |
   | What a surface should look like | `/ui-craft lock`. |
   | Too big for one session | Slice (below). |

   Record each settled decision where the repo records decisions (an OpenSpec
   `design.md` ADR section, or the order's Context). If the user is unavailable for a
   decision only they can make, post nothing and list the open questions.

6. **Spike the first hour** whenever the order rests on an assumption nobody has run.
   Execute its opening steps against the real artifacts: pass the parameter, run the
   tool once in each state it claims, remove the fixture and watch the fallback. Every
   claim of the form "X is honored by Y" gets one live probe. Findings amend the draft;
   the scratch work is never committed unless the order references it as a test.

7. **Slice when the work will not fit one session.** It will not fit when two or more of
   these traits fire, or when it projects past a ~180k-token peak: `multiple targets`,
   `live-resource import`, `cross-trust-boundary writes`, `multiple deliverables`,
   `live run inside the ticket`, `split-path evidence`, `lockstep copies`. File child
   issues, each a pull-request-sized piece with its own triage, and track them as a
   checklist on this ticket, which closes when every box is checked; a child projected
   under ~120k folds into a neighbour. A child whose outcome hangs on an unsettled
   decision waits behind a spike child that settles it. Record which traits fired.

8. **Stamp** `Review depth:` and `Profile:` per the skill page's review-depth section,
   checking the sensitivity floor first, and `Surface lifecycle:` per the template. A
   `build` or `revise` lifecycle must meet the template's `Surface lifecycle:` rule:
   every screen it names is locked in the lock doc, and `revise` has its safe start.
   When any of these is missing, name it and post no lock.

9. **Draft the order** from [the template](../templates/work-order.md) and run its
   before-the-draft checks.
   * **OpenSpec repo:** author the change on the ticket branch, run `openspec validate
     <change> --strict` until it passes, commit, read back `git rev-parse HEAD`, and pin
     `Source: openspec <change-path>@<that full OID>`.
   * **Another versioned plan artifact:** commit and pin it the same way as
     `repository-native`.
   * **Neither:** `Source: inline`.
   * An `investigation` worked in this session needs no lock; one dispatched to a
     worker gets an ordinary lock whose `Expected diff` names the findings files.

10. **Review the draft.** At Full depth, run `/plan-review` once, as an ordinary plan:
    one cold, fresh-context reviewer, one round. Reproduce each objection's claim before
    acting on it (run the regex, open the cited line) and drop the ones that fail. Fix
    what blocks; an objection that turns out to be an unsettled decision goes back to
    the user per step 5. Below Full depth, run the template's checks yourself.

11. **Confirm, then post.** Show the user the draft. On approval, post it as one comment
    (attribution, summary, fence) and move the ticket to triaged with its
    classification.

## Risk contract

Settle one for every bounded order. It lives in the OpenSpec change's `proposal.md`
when there is one, otherwise in the order.

* **Must prevent:** outcomes the work may never produce. Default: secret exposure,
  irreversible loss of authoritative data, silent incorrect success. Changing a default
  needs the user's decision.
* **Must recover:** failures that need automatic recovery.
* **Accepted failure:** a concrete failure and the consequence the user accepts. Rare,
  recoverable failures default to a clear stop with manual recovery.
* **Unsupported:** inputs or conditions the work does not promise to handle.
* **Evidence owed:** the behaviors and invariants that need a test or explicit check.

Price it from consequence, exposure, and recoverability, never from a target test
count. Reviewers test the work against this contract and do not raise it.
