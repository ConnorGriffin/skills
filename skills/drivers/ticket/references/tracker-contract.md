# The tracker contract

Four operations, and nothing else. The verbs call these; they never call a
tracker's API directly, and they never reach a second tracker when the first one
is unreachable. A verb that cannot reach the contract stops and names what is
missing.

One binding page supplies all four for one tracker.
[bindings/github-issues.md](../bindings/github-issues.md) is the reference
binding and ships with the skill.

## 1. Read a ticket

* **Input:** a ticket id.
* **Output:** the ticket's title, its description body, and its comments in a
  known order, each comment carrying its body text and its creation time. A verb
  that needs newest-first order sorts by that time itself.
* **Failure:** the ticket does not exist, or the tracker is unreachable. The verb
  stops, names the ticket id, and names the transport that failed. It never
  proceeds on a partial read.

## 2. Post a comment on a ticket

* **Input:** a ticket id and one comment body, written by the skill in the markup
  the binding declares.
* **Output:** confirmation that the comment landed, and its locator when the
  tracker returns one.
* **Failure:** the post is rejected or the transport fails. The verb prints the
  comment body it was going to post, so nothing is lost, then stops. It never
  retries silently and never drops the content.

## 3. Move a ticket's status

* **Input:** a ticket id and one target state from this skill's vocabulary:
  triaged, in progress, pending review, or done.
* **Output:** the ticket's state after the move.
* **Failure:** the state does not exist in the tracker's workflow, the move is not
  permitted, or the transport fails. This is the one non-fatal operation: say so
  in one line and continue the verb. Never retry a failed move, and never
  substitute a different state to make the move succeed.

## 4. Locate the newest work order

* **Input:** a ticket id.
* **Output:** the body of the newest comment containing a fenced block that starts
  `WORK ORDER`, or nothing when no comment has one. Newest wins; older orders are
  superseded, never merged.
* **Failure:** nothing found means no execution. `start` and `revise` refuse and
  route to `/ticket triage <ticket-id>`. A transport failure is not the same
  answer as an absent order: report which one happened.

## What a binding page supplies

One page, per operation:

1. The concrete command or tool call, with its inputs named.
2. What must be installed and authenticated for that call to work.
3. What the operation maps onto when the tracker has no equivalent (status is the
   usual case).
4. The markup comments are written in, since the binding owns markup and the
   templates do not.
5. The exact message the binding produces when its tracker or its transport is
   absent.

## Writing a binding for another tracker

One page, the four operations above, in the same order, with the five items
above filled in for each.

* A binding whose tracker or transport is absent stops with a clear message that
  names what is missing and how to supply it.
* It never falls back to a different tracker, and never invents a local
  substitute for a ticket.
* A binding that cannot implement an operation says so on the page. Read and
  post are load-bearing: a binding missing either one cannot run the verbs.
