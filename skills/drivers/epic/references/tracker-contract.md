# The epic tracker contract

Four operations, and nothing else. `$epic` calls these; it never calls a
tracker's API directly, and it never reaches a second tracker when the first
one is unreachable. A verb that cannot reach the contract stops and names what
is missing.

One binding page supplies all four for one tracker.
[bindings/github-issues.md](../bindings/github-issues.md) is the default
binding and ships with the skill.

## 1. Create a native child issue

* **Input:** the epic id, a title, a body, and its type (`spike` or `build`),
  plus `deferred` when it applies.
* **Output:** the created child's id and URL, attached to the epic as a native
  child.
* **Failure:** the create is rejected or the transport fails. The verb reports
  the failure and does not treat the child as filed.

## 2. Apply type labels

* **Input:** a child id and one type (`spike` or `build`), plus the epic
  protocol labels (`epic`, `spike`, `build`, `deferred`) the binding must be
  able to create idempotently.
* **Output:** confirmation that the label is attached. The `ticket:*` status
  axis is independent and this operation must not remove, rename, or
  reconcile it.
* **Failure:** the label cannot be created or attached. Report it; do not
  infer the label is present.

## 3. Read the parent and its children, and their types

* **Input:** the epic id.
* **Output:** the epic's native child list, and for each child its state,
  state reason, type label (`spike` or `build`), `deferred` presence, and any
  closing pull request reference with that pull request's merge state.
* **Failure:** the epic does not exist, or the tracker is unreachable. The
  verb stops and names the id and the transport that failed. It never infers
  a completion predicate from a partial or stale read.

## 4. File a review follow-up as a native child

* **Input:** the epic id, a title, a body, and the follow-up's type (`spike`
  or `build`), plus `deferred` when the epic destination does not require it.
* **Output:** the created child's id and URL, attached to the epic as a
  native child, ready to report on the originating ticket.
* **Failure:** the create is rejected or the transport fails. The verb
  reports the failure and does not claim the follow-up was filed.

## What a binding page supplies

One page, per operation:

1. The concrete command or tool call, with its inputs named.
2. What must be installed and authenticated for that call to work.
3. What the operation maps onto when the tracker has no equivalent.
4. The exact message the binding produces when its tracker or its transport
   is absent.

## Writing a binding for another tracker

One page, the four operations above, in the same order, with the four items
above filled in for each.

* A binding whose tracker or transport is absent stops with a clear message
  that names what is missing and how to supply it.
* It never falls back to a different tracker, and never invents a local
  substitute for native structure.
* A binding that cannot implement an operation says so on the page. Create
  and read are load-bearing: a binding missing either one cannot run `$epic`.
