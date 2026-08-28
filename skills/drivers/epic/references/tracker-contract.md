# The epic tracker contract

Four operations, and nothing else. Epic calls these; it never calls a tracker's
API directly, and it never reaches a second tracker when the first one is
unreachable. A tracker, authentication, or Git failure stops the current
operation visibly; epic never guesses or repairs authoritative state from a
local summary when a call fails.

One binding page supplies all four for one tracker.
[bindings/github-issues.md](../bindings/github-issues.md) is the reference
binding and ships with the skill.

## 1. Create a native child

* **Input:** the parent epic's id, a title, a body, and one type (`spike` or
  `build`), plus `deferred` when the child sits outside the epic's current
  destination.
* **Output:** the created child's id and URL, attached to the parent through the
  tracker's native parent-child relationship.
* **Failure:** the tracker rejects the creation, the parent id does not exist, or
  the transport fails. Epic stops, prints the body it was going to file so
  nothing is lost, and names what happened. It never substitutes prose for
  native structure.

## 2. Apply the epic protocol type labels

* **Input:** the four protocol labels (`epic`, `spike`, `build`, `deferred`) and
  the id of the issue receiving one.
* **Output:** confirmation the label exists and is attached. The bootstrap step
  creates all four idempotently before first use.
* **Failure:** a label cannot be created or attached (no permission, or the
  tracker disallows it). Epic reports this in one line and continues; it never
  removes, renames, or reconciles the independent `ticket:*` status axis while
  doing so.

## 3. Read the epic's children

* **Input:** the parent epic's id.
* **Output:** every child's id, title, state, type label, whether it carries
  `deferred`, and the merge state of any pull request that closed it.
* **Failure:** the parent id does not exist, or the transport fails. Epic stops
  and names the id and the transport that failed; it never proceeds on a partial
  read, and a local summary never substitutes for this read.

## 4. File a review follow-up as a native child

* **Input:** the originating ticket's epic (when any), a title, a body carrying
  evidence and desired outcome, and one type (`spike` or `build`).
* **Output:** the created child's id and URL, filed in-scope when the epic
  destination requires it, otherwise filed with its type plus `deferred`, and
  reported on the originating ticket.
* **Failure:** same as operation 1. This is operation 1 invoked from ticket's
  review-actions "Necessary follow-up" disposition, not a fifth operation.

## What a binding page supplies

One page, per operation:

1. The concrete command or tool call, with its inputs named.
2. What must be installed and authenticated for that call to work.
3. What the operation maps onto when the tracker has no equivalent (native
   parent-child structure is the usual case).
4. The markup comments and issue bodies are written in, since the binding owns
   markup and epic's templates do not.
5. The exact message the binding produces when its tracker or its transport is
   absent.

## Writing a binding for another tracker

One page, the four operations above, in the same order, with the five items
above filled in for each.

* A binding whose tracker or transport is absent stops with a clear message that
  names what is missing and how to supply it.
* It never falls back to a different tracker, and never invents a local
  substitute for a child issue.
* A binding that cannot implement an operation says so on the page. Create and
  read are load-bearing: a binding missing either one cannot run epic.
