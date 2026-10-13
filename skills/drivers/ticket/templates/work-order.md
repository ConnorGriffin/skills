# Work order template

One ticket comment: attribution, a human summary, then one fence. The fence is the
lock: the only thing `start` executes, and it must stand alone for a fresh session.

The summary is for a teammate: one sentence on what the work gets us, a plain-language
bullet per major piece, and a "Not in this ticket" bullet naming sibling work. It
translates the fence; it is not a second spec.

```
EXECUTION LOCK v2 <ticket-id> <lock-id>
Source: <openspec <change-path>@<full-commit-oid> | repository-native <path>@<full-commit-oid> | inline>
Classification: <code | investigation | manual>
Repo: <org/repo>
Surface lifecycle: <none | build <lock doc> <screens> | revise <lock doc> <screens>>
Review depth: <focused | targeted | full> (<one-line reason>)
Profile: <none | hardening>
Verification: <the command, transcribed byte-exact from the repo's Test: entry>
Expectation: <what that command must report before the pull request opens>

Context
<2-5 bullets: what exists, what constrains the change, decisions already settled.
 Orientation only under a pinned Source; the pinned change is the authority.>

Do
<inline only: numbered steps naming files, targets, and what must not change.>

Done when
<observable acceptance. Under a pinned Source, only the verification expectation and
 the stop at the pull request; the pinned change owns its own acceptance.>

Risk contract
<Must prevent / Must recover / Accepted failure / Unsupported / Evidence owed, or
 "in <change-path>/proposal.md" when the pinned change carries it.>

Generated facts
<every count, path, version, or enumeration the order states, as
 `$ command` followed by its verbatim output.>

Expected diff
<closed allowlist of repository-relative paths. No escape clause.>

Boundaries
* Iterate the verification locally until it matches the expectation.
* Execute the pinned change's tasks or the inline Do steps; nothing more.
* Stop at the pull request. Do not merge. Do not touch <out-of-scope things>.
```

## Field rules

* **`<lock-id>`** is 1 for the ticket's first lock and one more than the highest posted
  for each lock that supersedes one. Newest by post time still wins.
* **`Source:`** pins exact bytes. `openspec` and `repository-native` name a path and the
  full commit OID read back after committing it; `inline` carries the whole plan in
  `Context`/`Do`/`Done when`. A legacy `WORK ORDER` fence reads as `inline`. Amending a
  pinned source means posting a newer lock.
* **`Surface lifecycle:`** is `none` when no rendered surface changes, `build` for a
  greenfield surface, and `revise` for a shipped one. Either way, it names the lock doc
  and the screens this ticket builds. **Each named screen must be locked:** its line
  under the lock doc's `Approved screens` ends in `locked <date>`. The doc-level
  `Status:` is a summary and stays `draft` until every screen locks, so it is never the
  check. A fix inside an existing lock names the screens it touches. `revise` also needs
  the repo's declared safe dev-server entrypoint and fixture source. One ticket never
  mixes `build` and `revise`, and triage never runs the design session itself.
* **`Profile: hardening`** adds a `QA script` after `Done when`: numbered
  Given/When/Then steps a human follows in the running app.
* **Generated facts** are pasted verbatim. To shorten output, change the command
  (`head`, `grep -m`); never edit the captured text.

## Before the draft leaves triage

* Verified facts are separate from intent, each with its evidence.
* Current behavior is stated separately from desired behavior.
* The caller-facing interface shape is described, or the change is said to be internal.
* Every value the order names has both a producer and a consumer in the order.
* Executable logic (a regex, a shell fragment, a query) lives in a committed, executed
  scratch test the order references, never as a literal in prose.
* Every `Done when` line is observable, and out-of-scope work is named in Boundaries.
