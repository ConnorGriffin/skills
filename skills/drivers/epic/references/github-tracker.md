# GitHub tracker operations

Epic planning uses authenticated GitHub Issues. Before a mutation, run `gh version` and `gh auth status`; pass `--repo OWNER/REPO` explicitly. The current GitHub CLI must support native sub-issues and dependencies. Live tracker state is truth; re-read it after every mutation that changes relationships or labels.

## Bootstrap labels

Create exactly the four protocol labels idempotently. The `ticket:*` status axis is independent and this skill must not remove, rename, or reconcile it.

```sh
gh label create epic     --repo OWNER/REPO --color 5319e7 --description "OpenSpec planning container" --force
gh label create spike    --repo OWNER/REPO --color 0e8a16 --description "Question that resolves planning uncertainty" --force
gh label create build    --repo OWNER/REPO --color 1d76db --description "Implementable ticket" --force
gh label create deferred --repo OWNER/REPO --color bfdadc --description "Outside this epic's current scope" --force
```

An epic has `epic`; each child has one of `spike` or `build`; a deferred child also has `deferred`. Ticket triage applies `build` to ordinary build tickets.

## Native structure

Create issue bodies in temporary files and use `--body-file`. Capture returned URLs rather than guessing numbers. Attach every spike, build, and deferred follow-up to the epic through native child issues:

```sh
gh issue edit EPIC_NUMBER --repo OWNER/REPO --add-sub-issue CHILD_NUMBER
```

Express a real prerequisite with a native blocked-by edge:

```sh
gh issue edit BLOCKED_NUMBER --repo OWNER/REPO --add-blocked-by BLOCKER_NUMBER
```

Use `--remove-blocked-by`, `--add-blocking`, `--remove-blocking`, `--parent`, or `--remove-parent` to correct a live relationship. Never substitute prose for native structure.

## Read an epic and its children

Read the epic's child nodes directly; `subIssues.nodes` is the child list. Then read every child's labels, state, state reason, and closing-pull-request references. Finally read each referenced pull request's `mergedAt` value.

```sh
gh api graphql -f query='query($owner:String!, $repo:String!, $number:Int!) {
  repository(owner:$owner, name:$repo) {
    issue(number:$number) {
      subIssues(first:100) { nodes {
        number title state labels(first:20) { nodes { name } }
        stateReason
        closedByPullRequestsReferences(first:20) { nodes { number mergedAt } }
      } }
    }
  }
}' -F owner=OWNER -F repo=REPO -F number=EPIC_NUMBER
```

If a closing reference needs fresh confirmation, read that pull request directly:

```sh
gh pr view PR_NUMBER --repo OWNER/REPO --json number,state,mergedAt,url
```

## Completion checks

Perform these direct reads before close-out, and report each as pass or fail:

1. **No open spike child:** every child with label `spike` is closed.
2. **Build completion:** every child with label `build` either has a closing pull request whose `mergedAt` is non-null, or is closed with `stateReason` `NOT_PLANNED`.
3. **No open deferred child:** no open child carries `deferred`.

Only these live reads decide whether the epic may close. A ledger mismatch is visible staleness for the home session to correct, never a completion pass.

## Deferred dispositions

At close-out, first re-read the child and parent relationship. Promotion removes `deferred` and files the child outside the closing epic. Reparenting uses the new parent's native relationship while keeping `deferred`. A won't-do outcome posts the reason, closes with `--reason not planned`, retains the type label, and removes `deferred`:

```sh
gh issue close CHILD_NUMBER --repo OWNER/REPO --reason "not planned"
gh issue edit CHILD_NUMBER --repo OWNER/REPO --remove-label deferred
```

Never archive while the completion read finds an open deferred child.
