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
