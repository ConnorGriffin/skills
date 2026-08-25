# Binding: GitHub issues

The reference binding for [the tracker contract](../references/tracker-contract.md).
Ticket ids are issue numbers. Transport is the GitHub CLI (`gh`), authenticated
for the target repository.

Run every command with `--repo <org/repo>` so the binding works from a worktree
whose remote is not the ticket's repository.

## Requirements

* `gh` on `PATH`, authenticated (`gh auth status`).
* Push and issue-write access to `<org/repo>`.

`gh` absent or unauthenticated is a stop, not a degraded mode: report
`ticket: github issues binding needs an authenticated gh; run gh auth login`,
name the operation that could not run, and stop. Never substitute a local file,
another tracker, or a guess at the ticket's contents.

## 1. Read a ticket

```sh
gh issue view <id> --repo <org/repo> --json number,title,body,state,labels,parent,comments
```

`parent` lets triage find a candidate parent; a second read through this same
operation supplies that parent's `labels` so triage can confirm the `epic` type.
`comments` arrives oldest-first, each with `body` and `createdAt`. Sort by
`createdAt` when a verb wants newest-first.

A missing issue exits non-zero with `Could not resolve to an issue`. That is the
absent-ticket failure: stop, naming the id.

## 2. Post a comment on a ticket

```sh
gh issue comment <id> --repo <org/repo> --body-file <path to the comment body>
```

Write the body to a file in the ticket's worktree, outside the branch's tracked
content, and pass it with `--body-file`. Passing prose through `--body` puts
fenced blocks and quote lines at the mercy of shell quoting.

## 3. Move a ticket's status

GitHub issues have no status workflow, so this binding maps the four states onto
labels plus the issue's own open or closed state:

| State | What the binding does |
|---|---|
| triaged | Receives triage's classification. `code` first creates (if needed) and attaches `build`, then adds `ticket:triaged`; `investigation` and `manual` add only `ticket:triaged`. |
| in progress | add `ticket:in-progress`, remove `ticket:triaged` |
| pending review | add `ticket:pending-review`, remove `ticket:in-progress` |
| done | `gh issue close <id> --repo <org/repo>` and remove `ticket:pending-review` |

Create a missing status label once with
`gh label create ticket:<state> --repo <org/repo>`. For a `code` triage, first
ensure and attach the independent type label:

```sh
gh label create build --repo <org/repo> --color 1d76db --description "Implementable ticket" --force
gh issue edit <id> --repo <org/repo> --add-label build
gh issue edit <id> --repo <org/repo> --add-label ticket:triaged
```

Creation failure or attachment failure is the contract's one non-fatal status
failure: report it, retain the posted work order, and do not run the later
`ticket:triaged` command. `investigation` does not create or attach `build` and
applies only `ticket:triaged`. `manual` does not create or attach `build` and
applies only `ticket:triaged`. Every other `ticket:*` transition
remains exactly as listed above.

A repository whose project board owns status is served the same way. The labels
are this binding's status channel, and the board stays the humans' view.

## 4. Locate the newest work order

````sh
gh issue view <id> --repo <org/repo> --json comments \
  --jq '[.comments[] | select(.body | test("(?m)^```[a-z]*\\s*\\r?\\nWORK ORDER"))] | last'
````

The scan is newest-first in effect: `gh` returns comments oldest-first, so the
last match is the newest order. Empty output means no order, which is the refusal
in `start` and `revise`, not an error to work around.

A non-zero exit is a transport failure, and is reported as such rather than as an
absent order.

## Markup

GitHub-flavored markdown. Headings are `##`, the attribution line is a `>` quote,
and the work order sits in a triple-backtick fence with no language tag. The
templates carry the substance; this binding decides the markup.
