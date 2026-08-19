---
name: review
description: Front door for review of any kind — code, a plan, a document that needs named reviewer perspectives, or pending changes with a security question. Classifies the subject in front of it and routes to exactly one review skill; does no reviewing itself. Use for 'review this', '/review', or any request to review a PR, diff, plan, spec, brief, document, or security-sensitive change.
---

# Review

Front door for review, the way `scope` is the front door for work that isn't ready to
build. Classify what is in front of it, announce the route, invoke that route's
skill. This skill does none of the reviewing itself — the standards-and-spec pass it
used to run now lives in `code-review`.

## Routes

Routes are data, not prose, layered from two files:

- **Shipped:** [`routes.json`](routes.json) in this directory. Four rows ship today:
  - `code` → `code-review` — changed code against the repo's documented standards and
    the originating issue.
  - `plan` → `plan-review` — a plan, spec, work order, or agent brief, before anything
    is built.
  - `personas` → `persona-review` — a document that needs named reviewer
    perspectives.
  - `security` → the security review that ships with the agent — pending changes
    carrying a security question.
- **Operator:** `~/.config/review/routes.json`. A row whose `route` matches a shipped
  row replaces it; any other `route` extends the table. See *Registering a review
  type* below.

## Process

1. **Classify.** Read what's in front of you — a diff, a document, the user's own
   words — and pick the route whose `for` text matches it.
2. **Announce.** Say the route in one line before invoking anything: "routing to
   `code-review`" or equivalent. This is how the caller knows which review ran, not a
   request for approval.
3. **Invoke.** Call that route's skill (or, for `security`, the agent's built-in
   security review) and stop. Nothing here re-runs the review or second-guesses its
   output.

## Ambiguity

Matching `scope`: pick a route and announce it. Ask exactly **one** framing question
only when the subject genuinely admits two routes — a spec with code already written
against it, say. Never ask when the subject is clearly one thing; a clear subject
paired with a manufactured question is stalling, not scoping.

## The stop rule

A registered route whose skill is missing **stops** and reports what is missing and
how to install it. It never runs a nearby review instead. This is the load-bearing
rule in this skill: a missing `security` route that silently becomes a `code` review
produces a passing verdict nobody should trust, which is worse than no review at all.

Route resolution decides this mechanically — see *Resolving a route* below — and its
answer is final, not a suggestion to route around.

The **not-a-route** case reads differently from **not-installed**, on purpose: one
means "review has no idea what that is," the other means "review knows what that is
and can't reach it yet." Conflating them either hides a real gap behind "not
supported," or manufactures support behind a name nobody registered.

## Resolving a route

`scripts/resolve_route.py` makes the outcomes above machine-decidable instead of
judgment calls:

```
python3 scripts/resolve_route.py <route>
python3 scripts/resolve_route.py --list
```

Exit statuses:

- **0 — installed.** The route is registered and its skill was found (or, for an
  `agent-builtin` row, ships with the agent — presence not verified on disk).
- **3 — registered but missing.** The route is registered, its skill is a `skill`
  kind, and no skill directory was found. The message names the skill and, for a
  skill this pack ships, the install command; for one it doesn't ship, the row's
  source file instead. It never names another route.
- **4 — not a route.** The name matches no row. The message lists the registered
  route names.
- **2 — malformed config.** `~/.config/review/routes.json` is not valid JSON, or a
  row is missing a field or carries an unknown `kind`. Names the file and the
  problem. This exit is never returned for the three outcomes above.

`--list` prints every registered row as `route<TAB>skill<TAB>kind<TAB>for`, exit 0.

## Registering a review type

An installation with its own review skill — an infra-plan review, a compliance
review, whatever it runs internally — registers it by adding a row to
`~/.config/review/routes.json`:

```json
[
  { "route": "code", "skill": "internal-code-review", "kind": "skill",
    "for": "changed code, using our internal standards checker" },
  { "route": "infra", "skill": "infra-plan-review", "kind": "skill",
    "for": "a pulumi or terraform plan before it's applied" }
]
```

The first row replaces the shipped `code` route (same `route` value); the second adds
a new one. Registering a row does **not** install the skill it names — the operator
still installs `infra-plan-review` separately, and until then `resolve_route.py infra`
reports it registered but missing.
