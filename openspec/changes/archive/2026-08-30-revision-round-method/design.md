# Design

## ADR harmonic-219 — Revision rounds bind through ui-craft

**Context.** The method was discovered in one repository's revision session, and
it could have been recorded in that repository's agent brief. That brief is read
by every agent working there, so the rules would bind immediately and could name
the repository's own gates, surfaces and file paths concretely.

But the failure the method prevents is not specific to that repository. It is the
shape of shipped-surface revision itself: direction settled by iterating in a
running app never converges, and a written record does not follow a behavior that
moves unless something makes it. Any repository revising a shipped surface through
`revise` meets both. Recording the method in one consuming repository leaves every
other one to rediscover it, and a second repository learning the same lesson would
produce a second, drifting copy.

**Decision.** The method lives in `ui-craft` — extending `revise` and
`behavior-sweep` rather than adding a skill or a reference page — and consuming
repositories' agent briefs get nothing. Each addition lands in the section that
already owns its neighboring rule, contributes only the residue that section does
not already state, and cites the existing rule rather than restating it.
Repository-specific names stay out of the skill text; the illustrating failures
are described by their shape.

**Consequences.** The rules bind wherever the pack is installed, and a consuming
repository revising a surface inherits them without an edit of its own. The cost
is generality: a repository whose gates, sandboxes or surfaces make one of these
obligations concrete has to translate it, and the skill text cannot name the
gate to run. That is the same trade every other rule in this pack makes.

The round method binds interactive divergent work only. `revise`'s headless rule
is unchanged and stands above it: a headless session goes straight to an app
branch, never opens a wireframe phase, and returns an unsettleable direction as a
decision instead of inventing one.

## ADR harmonic-219 — One page enumerates what a retirement owes

**Context.** Adding the premise obligation to a retirement exposed how many pages
already stated that contract. `revise`, `resettle` and `behavior-sweep` each
carried their own enumeration of the change set, and `build` carried its status
mapping. Two review rounds each surfaced one more copy than the round before:
the first found `revise` stale, the second found `resettle` stale. Both were
consistent with the others at the time they were written and went stale when a
fifth obligation arrived, which is the failure mode of every restated list.

**Decision.** `behavior-sweep` §5 enumerates what a retirement owes, once, and
every other page names the case and points at that list instead of repeating it.
`revise`'s Retired case and its before-landing check, and `resettle`'s post-lock
`retired` change set, now defer. `build` keeps its own concern — how a replay
result maps to a ledger status — because that is not the list.

**Consequences.** A new obligation lands in one place and every path inherits it,
which is what neither review round could rely on before. A reader of `revise` or
`resettle` takes one hop to see the full set, which is the cost. The test pins
the enumeration's home and asserts the sanction template appears on exactly one
page, so a page that re-grows its own copy fails rather than drifting quietly;
that guard was proven to fail before it was relied on.
