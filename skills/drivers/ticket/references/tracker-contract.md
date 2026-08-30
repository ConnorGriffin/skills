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
  triaged, in progress, pending review, or done. A move to `triaged` also receives
  triage's classification: `code`, `investigation`, or `manual`.
* **Output:** the ticket's state after the move.
* **Classification rule:** for a code classification, the binding first ensures
  the `build` label exists and is attached, then applies `ticket:triaged`. For
  `investigation` and `manual`, it neither creates nor attaches `build`, and applies
  only the status transition. Type labels and `ticket:*` status remain independent.
* **Failure:** the state does not exist in the tracker's workflow, the move is not
  permitted, or the transport fails. A `code` path that cannot create or attach
  `build` is this operation's one non-fatal status failure: report it in one line,
  retain any posted work order, and do not apply the later `ticket:triaged` label.
  Never retry a failed move, and never substitute a different state to make the move
  succeed.

## 4. Locate the newest work order

* **Input:** a ticket id.
* **Output:** the body of the newest comment whose fence header starts
  `EXECUTION LOCK v2` (flat lock or chunked header) or the legacy `WORK ORDER`, or
  nothing when no comment has either header. Newest wins across both protocols by
  comment time, regardless of which protocol is newer; older orders of either
  protocol are superseded, never merged, and no field is ever merged from an older
  comment into a newer one, protocol boundary or not. This operation matches on
  the fence header alone; it does not parse or validate the `EXECUTION LOCK`
  version or `Source:` mode inside the fence.
* **Admission is the consumer's job, and it fails closed.** `start` and `revise`
  parse the located comment before acting on it. An unrecognized `EXECUTION LOCK`
  version, or a `Source:` mode this protocol does not define, refuses execution
  and routes to `/ticket triage <ticket-id>`; it never falls back to an older
  comment, located or not; and this operation is not consulted again to find one.
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
