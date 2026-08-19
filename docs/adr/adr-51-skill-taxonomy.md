# ADR 51 — Front doors, drivers, and tools inside `skills/`

## Context

The pack holds three kinds of skill under one flat directory, and the flat listing hides
which is which. Front doors classify uncertainty and route to another skill: `scope`
classifies the dominant uncertainty in work not ready to build and routes to a specialist
skill, and `review` classifies which kind of review and routes onward. Drivers
orchestrate other skills and do work themselves: `wayfinder` charts a large effort as a
map of decision tickets and hands clear subtrees onward as build issues, `implement` and
`ui-craft` run their procedures and delegate subgoals, `orchestrate` delegates but is
chosen by the operator knowing what that means. Tools do one job themselves, chosen either
by the operator or invoked from a driver: `code-review` scores a diff, `plan-review`
audits plans, `tdd` runs tests, `spin-worktree` cuts a worktree, `pr-body` scores a body.

The original framing split on whether a skill "routes to or drives other skills" versus
"does one job". That rule admits most of the pack, because almost every non-trivial skill
names another; the boundary dissolves. A working test is who chooses the skill. A front
door is chosen because the operator cannot yet choose. A driver is chosen deliberately. A
tool is chosen for its one job.

Three ways to express the distinction were considered.

A top-level `workflows/` directory beside `skills/` reads well, but two facts count
against it. The install CLI treats `skills/` and its subdirectories as standard discovery
locations, walking a container up to three levels, which covers a catalog with one or two
category levels; a top-level directory of a different name is reached only by the
last-resort recursive scan. And `.claude/workflows/` already denotes orchestration
scripts, a different artifact entirely, so the name is taken in the reader's mind before
this pack uses it.

Category folders inside `skills/` land in a layout the installer already supports, at the
cost of rewriting every path in the README, `scripts/validate.py`, CI, and the cross-skill
and cross-doc relative links.

Metadata only, with frontmatter declaring a kind and the README grouping accordingly,
costs nothing and moves nothing, but leaves the directory listing as uninformative as it
is today.

## Decision

Skills live in category folders inside `skills/`, three siblings one level deep:

* `skills/workflows/<name>` holds a front door: the skill you invoke when you do not yet
  know which skill the work needs. It classifies the subject and routes to another skill,
  doing none of that skill's work. Members: `scope` and `review`.
* `skills/drivers/<name>` holds a multi-phase procedure that calls other skills by name
  to do its work, but is chosen by the operator, not by a router: `wayfinder`,
  `implement`, `ui-craft`, `orchestrate`, `ticket`, `openspec-adopt`.
* `skills/tools/<name>` holds a skill that does one job itself, whether or not another
  skill invokes it: `code-review`, `plan-review`, `persona-review`, `tdd`, `prototype`,
  `research`, `preflight`, `handoff`, `pr-body`, `say-less`, `spin-worktree`,
  `drive-local-webapp`, `cbm-onboard`, `ci-design`, `codebase-design`,
  `domain-modeling`, `writing-for-agents`.

The distinguishing test is who chooses the skill, not whether it invokes others. A front
door is chosen because the operator cannot choose; a driver is chosen deliberately and
then calls what it needs; a tool does its one job. The move is mechanical; no skill's
instructions change in the same diff.

## Consequences

The directory listing now answers the question the README answered before, and the install
CLI keeps first-class discovery rather than falling back to a recursive scan. The name
collision with orchestration scripts never arises.

Every path in the repository moves once. `scripts/validate.py` gains a category level in
its skill root and expected set, CI's compile step follows the helper, and relative links
into `docs/` gain a level. Anyone with a pinned path into `skills/<name>/` breaks at the
same moment, which is why the move lands alone rather than alongside new skills.

The categories are a judgment, not a schema. A skill that both routes and does work
sits in `drivers/` unless it is invoked out of uncertainty, which would make it a front
door. `workflows/` stays deliberately small; a category with one plausible member is a
sign the rule, not the member, needs revisiting.
