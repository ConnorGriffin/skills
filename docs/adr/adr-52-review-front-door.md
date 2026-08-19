# ADR 52 — `/review` as a routing front door with a config route table

## Context

Review is not one activity. Changed code wants a standards-and-spec pass; a plan wants
adversarial reading before anything is built; a document wants named perspectives; pending
changes sometimes want a security pass; an infrastructure plan wants a blast-radius read
before an apply. Each of those already exists as its own skill, shipped here, shipped with
the agent, or installed privately.

Until now `/review` named exactly one of them, the standards-and-spec pass on changed
code, which `code-review` has since superseded with a per-item verdict that terminates a
round. So the pack has an entry point whose name promises the general case and whose
behavior delivers one specific case, while the other reviews are reachable only by
knowing their skill names.

`scope` already solved this shape for work that is not ready to build: classify the
dominant uncertainty, route to exactly one specialist, do none of the specialist's work.

The routes are not a fixed set. This pack ships four. An installation may register a
review type the pack has never heard of, including one whose skill cannot be published.
Hardcoding routes in the skill's prose would force every such installation to keep a
private copy of the front door, which is the divergence this pack is trying to remove.

## Decision

`/review` becomes the front door. It classifies the subject in front of it and routes to
exactly one review skill, doing no reviewing itself. Today's `review` skill retires into
it.

Routes are data. The skill reads a route table from config, where each row names the
route, the skill it invokes, and what it is for. Registering a review type is a row, not a
fork.

Three outcomes stay distinguishable: a registered route whose skill is installed runs; a
registered route whose skill is missing stops, names the skill, and says how to install
it; a subject that matches no route says exactly that. There is no fallback to a nearby
review.

## Consequences

A person types one command and reaches the right review, and the pack gains a place to put
the next review type without touching the front door's instructions.

The stop-on-missing rule is the load-bearing part. A silent downgrade would turn a
requested security review into a code review that reports clean, which is worse than no
review, because it produces a passing verdict nobody should trust. That failure mode is
why the missing-skill case is a stop rather than a degradation, and why "not installed"
and "not a route here" are reported as different things.

The config route table is a new artifact to keep correct: a row pointing at a skill that
was renamed produces a stop rather than a route, and the message must make that
diagnosable.

Retiring `review` breaks anyone invoking it for the changed-code case. They get the front
door instead, which routes them to `code-review`, so the path survives even though the
skill does not.
