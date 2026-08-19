# ADR 51 — Workflow and tool categories inside `skills/`

## Context

The pack holds two kinds of skill under one flat directory. Some skills route to, or
drive, other skills: `scope` classifies uncertainty and hands off, `orchestrate` delegates
every piece of work, `wayfinder` charts an effort and hands subtrees onward. Others do one
job themselves: `spin-worktree` cuts a worktree, `drive-local-webapp` drives a browser,
`pr-body` scores a body. A reader browsing `skills/` cannot tell which is which without
opening the skill, and the README table carries the distinction only implicitly.

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

Skills live in category folders inside `skills/`: `skills/workflows/<name>` for skills
that route to or drive other skills, and `skills/tools/<name>` for skills that do one job
themselves. The move is mechanical; no skill's instructions change in the same diff.

## Consequences

The directory listing now answers the question the README answered before, and the install
CLI keeps first-class discovery rather than falling back to a recursive scan. The name
collision with orchestration scripts never arises.

Every path in the repository moves once. `scripts/validate.py` gains a category level in
its skill root and expected set, CI's compile step follows the helper, and relative links
into `docs/` gain a level. Anyone with a pinned path into `skills/<name>/` breaks at the
same moment, which is why the move lands alone rather than alongside new skills.

The categories are a judgment, not a schema. A skill that both routes and does work sits
in `workflows/`, because the routing is the part a reader needs to find.
