# GitHub tracker operations

Wayfinder uses GitHub's native child issues, dependencies, and labels. The
commands below require a current GitHub CLI with `--add-sub-issue`, `--add-blocked-by`, and
the `subIssues` / `blockedBy` JSON fields. Run `gh version` and `gh auth status` before the
first mutation. Pass `--repo OWNER/REPO` explicitly when the working directory is ambiguous.

## Labels

Create the vocabulary once per repository. `--force` makes this idempotent without changing
the state of any issue:

```sh
gh label create wayfinder:map       --color 5319e7 --description "Map of decisions for a multi-session effort" --force
gh label create wayfinder:research  --color 0e8a16 --description "AFK research decision" --force
gh label create wayfinder:prototype --color 1d76db --description "HITL locked UI mockup decision" --force
gh label create wayfinder:interview --color fbca04 --description "HITL interview or domain decision" --force
gh label create wayfinder:task      --color c5def5 --description "Prerequisite action that unblocks a decision" --force
gh label create wayfinder:awaiting-disposition --color bfdadc --description "Completed research awaiting human disposition" --force
```

Repositories labeled under the pre-scope vocabulary carry `wayfinder:grilling` instead of
`wayfinder:interview`. Renaming the label migrates every ticket that carries it in one
step — run this before the create block, and skip it when the old label is absent:

```sh
gh label edit wayfinder:grilling --name wayfinder:interview --description "HITL interview or domain decision" 2>/dev/null || true
```

Every map and decision ticket carries exactly one of the first five ticket-type labels.
`wayfinder:awaiting-disposition` is additional state compatible with exactly one ticket-type
label; it is not a second ticket type and is distinct from the transient
`wayfinder:resolving` claim. Keep the `wayfinder:` namespace reserved for planning: whatever
labels your implementation workflow uses live outside it, and nothing in that namespace
belongs on a build issue.

## Create the map and tickets

Create issue bodies in a temporary file and use `--body-file` so Markdown is not damaged by
shell quoting:

```sh
gh issue create --repo OWNER/REPO --title "Map: <destination>" \
  --body-file /path/to/map-body.md --label wayfinder:map

gh issue create --repo OWNER/REPO --title "Decide <question>" \
  --body-file /path/to/ticket-body.md --label wayfinder:interview
```

Capture the returned URLs or resolve titles immediately; never guess issue numbers.

Add each decision ticket as a native child after both issues exist:

```sh
gh issue edit MAP_NUMBER --repo OWNER/REPO --add-sub-issue TICKET_NUMBER
```

Build issues filed at handoff are not children of the map. The child set remains the exact
decision-ticket set used to calculate the frontier.

## Wire dependencies

If `BLOCKED_NUMBER` cannot be worked until `BLOCKER_NUMBER` closes:

```sh
gh issue edit BLOCKED_NUMBER --repo OWNER/REPO --add-blocked-by BLOCKER_NUMBER
```

Use `--remove-blocked-by`, `--add-blocking`, or `--remove-blocking` to correct edges. Never
encode a dependency only as `Blocked by #N` prose; body prose is not queryable, and other
tools may already read that convention for their own purposes. Wayfinder uses GitHub's
native planning relationship.

## Read the map and frontier

Load the map at low resolution:

```sh
gh issue view MAP_NUMBER --repo OWNER/REPO \
  --json number,title,url,body,state,subIssues,subIssuesSummary
```

List child numbers, then inspect only the open candidates:

```sh
gh issue view MAP_NUMBER --repo OWNER/REPO --json subIssues --jq '.subIssues[].number'

gh issue view TICKET_NUMBER --repo OWNER/REPO \
  --json number,title,url,state,labels,assignees,blockedBy
```

A ticket is on the frontier only when `state` is `OPEN`, it does not carry either the
`wayfinder:resolving` or `wayfinder:awaiting-disposition` label, and every issue in
`blockedBy` is closed. Preserve GitHub's returned child order when choosing the first
frontier ticket. Tickets carrying `wayfinder:awaiting-disposition` are excluded from the frontier.

## Claim and resolve

The claim is the `wayfinder:resolving` label, shared by human sessions and unattended
workers. Assignment cannot distinguish the two, since an unattended worker may run under the
operator's own GitHub identity. Claim before doing work:

```sh
gh label create wayfinder:resolving --repo OWNER/REPO --color d4c5f9 \
  --description "A session is resolving this decision ticket" --force
gh issue edit TICKET_NUMBER --repo OWNER/REPO --add-label wayfinder:resolving
```

Re-read the issue after claiming. If another session won the race, choose another frontier
ticket. Release the claim on completion or when giving up:

```sh
gh issue edit TICKET_NUMBER --repo OWNER/REPO --remove-label wayfinder:resolving
```

Post the full answer as a comment, then close only after its ADR and map update are durable:

```sh
gh issue comment TICKET_NUMBER --repo OWNER/REPO --body-file /path/to/resolution.md
gh issue close TICKET_NUMBER --repo OWNER/REPO --reason completed
```

Update the map with `gh issue edit MAP_NUMBER --body-file ...`. Before every mutation,
re-fetch the current body and child/dependency state so concurrent sessions do not overwrite
one another.

## Reconcile awaiting dispositions

Human map sessions inspect every open research child and reconcile each one carrying
`wayfinder:awaiting-disposition` before reading the ordinary frontier. The state label is the
durable queue; `Awaiting disposition` is its map index. If either side is missing, restore the
map entry for every labeled child before reconciling and do not treat an unlabeled map entry as
disposed without checking its research ticket. For each pending child, load its labels and
terminal findings comment. Skip it when another session already holds `wayfinder:resolving`;
otherwise claim it and re-read to confirm the claim. Keep the ticket open, keep
`wayfinder:awaiting-disposition`, and keep the map entry until every structured
`handoff_required` candidate has a durable ruling.

Treat GitHub as the recovery log. Before the first mutation and after every mutation:

1. Re-fetch the map body, all open research children and their labels, research ticket
   comments, and native relationships. Repair any mismatch between labeled children and the
   map's `Awaiting disposition` index before continuing.
2. Enumerate the map's `Handoffs` links and ordinary issues whose bodies contain the exact
   `Wayfinder handoff: #<map>` marker, then inspect each issue's `blockedBy` relationships:

   ```sh
   gh search issues --repo OWNER/REPO --match body "Wayfinder handoff: #MAP_NUMBER" \
     --json number,title,url,state,body --limit 100

   gh issue view BUILD_NUMBER --repo OWNER/REPO --json number,title,url,state,body,blockedBy
   ```

   GitHub's search tokenizes text, so treat every hit as a candidate only: confirm the exact
   marker line in the fetched body before matching, and never conclude an issue is absent from
   an empty search result alone — the map's `Handoffs` links are the second read.
3. Match records by the exact candidate identity copied into each build issue or disposition
   comment: the build issue repeats it in its `Wayfinder candidate:` marker, and the
   disposition comment repeats it verbatim. A selected candidate is complete only when one map
   entry, one exact marker, and one native `blockedBy` edge to this terminal research child all
   name the same build issue.
4. If only one or two facts exist, repair that same build issue. If all three exist, record no
   new mutation. Create a build issue only when no existing or partial record matches.
5. Treat an existing disposition comment as complete only when it matches the candidate
   identity and contains `no-build` or `deferred`, its required observable trigger, and its
   verification condition. A no-build ruling must also contain its reason. Repair an incomplete
   comment in place; never append a duplicate disposition.

Read the findings and disposition comments, and repair one in place, by its comment URL:

```sh
gh issue view RESEARCH_NUMBER --repo OWNER/REPO --json comments \
  --jq '.comments[] | {url, body}'

# COMMENT_ID is the number after `#issuecomment-` in that comment's URL.
gh api --method PATCH /repos/OWNER/REPO/issues/comments/COMMENT_ID \
  --field body=@/path/to/disposition.md
```

Posting a second comment for a candidate that already has one is a duplicate disposition, not
a repair.

For each selected candidate, create its standalone build issue first, carrying both the
`Wayfinder handoff: #<map>` and `Wayfinder candidate:` markers in its body, then add the
truthful dependency, then add its titled map line:

```sh
gh issue edit BUILD_NUMBER --repo OWNER/REPO --add-blocked-by RESEARCH_NUMBER
```

Never make build issues map children or add `wayfinder:*` labels to them. Every unselected
candidate must instead have a research-ticket disposition comment that says `no-build` or
`deferred`; include its exact candidate identity, an observable trigger, and a verification
condition. Selecting zero candidates is valid only when every candidate has one of those
explicit rulings.

Once replay proves that every candidate is disposed, re-fetch the map and finalize in this
order: remove its `Awaiting disposition` line, remove the state label, append the research
ticket's explicit final gist under `Decisions so far`, close the ticket, and release the claim.

```sh
gh issue edit RESEARCH_NUMBER --repo OWNER/REPO --remove-label wayfinder:awaiting-disposition
gh issue close RESEARCH_NUMBER --repo OWNER/REPO --reason completed
gh issue edit RESEARCH_NUMBER --repo OWNER/REPO --remove-label wayfinder:resolving
```

Replay the full read-and-match procedure after an interruption. Closed research always has a
durable disposition; no hidden issues-to-file list exists outside GitHub.

## Correct structure

```sh
# Move a ticket to another map.
gh issue edit TICKET_NUMBER --repo OWNER/REPO --parent NEW_MAP_NUMBER

# Remove it from the current parent.
gh issue edit TICKET_NUMBER --repo OWNER/REPO --remove-parent

# Remove a child from a known map.
gh issue edit MAP_NUMBER --repo OWNER/REPO --remove-sub-issue TICKET_NUMBER
```

Closing an out-of-scope ticket removes it from the frontier; keep it as a child so the map
retains its planning history.
