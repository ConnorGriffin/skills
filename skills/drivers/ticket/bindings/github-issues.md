# Binding: GitHub issues

Supplies [the tracker contract](../SKILL.md#the-tracker-contract) for GitHub. Ticket
ids are issue numbers. Pass `--repo <org/repo>` on every command so it works from a
worktree whose remote is not the ticket's repository.

Needs `gh` on `PATH`, authenticated, with issue-write access. Without it, report
`ticket: github issues binding needs an authenticated gh; run gh auth login`, name the
operation that could not run, and stop.

## 1. Read

```sh
gh issue view <id> --repo <org/repo> --json number,title,body,state,labels,parent,comments
```

Comments arrive oldest-first with `body` and `createdAt`. `Could not resolve to an issue` means the ticket is absent.

## 2. Post

```sh
gh issue comment <id> --repo <org/repo> --body-file <path>
```

Write the body as GitHub-flavored markdown (the order in a triple-backtick fence with no
language tag) to a file outside the branch's tracked content; `--body` mangles fences
and quote lines through shell quoting.

## 3. Move status

GitHub issues have no workflow, so status is labels plus open or closed:

| State | Action |
|---|---|
| triaged | `code` only: `gh label create build --repo <org/repo> --color 1d76db --description "Implementable ticket" --force` and `gh issue edit <id> --repo <org/repo> --add-label build`. Then add `ticket:triaged`. |
| in progress | add `ticket:in-progress`, remove `ticket:triaged` |
| pending review | add `ticket:pending-review`, remove `ticket:in-progress` |
| done | `gh issue close <id> --repo <org/repo>`, remove `ticket:pending-review` |

Create a missing status label once with `gh label create ticket:<state> --repo
<org/repo>`. A failure to create or attach `build` skips `ticket:triaged` and keeps the
posted order. The `build` type label and the `ticket:*` status
labels stay independent.

## 4. Locate the newest work order

````sh
gh issue view <id> --repo <org/repo> --json comments \
  --jq '[.comments[] | select(.body | test("(?m)^```[a-z]*\\s*\\r?\\n(EXECUTION LOCK |WORK ORDER)"))] | last'
````

The last match is the newest order, of any lock version. Empty output means no order,
which is `start`'s refusal; a non-zero exit is a transport failure and is reported as
one.
