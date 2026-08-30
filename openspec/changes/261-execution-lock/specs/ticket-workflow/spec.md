# Ticket workflow — deltas

## MODIFIED Requirements

### Requirement: Work-order lock and model fit

`start` and `revise` MUST refuse execution when no comment's fence header starts
`EXECUTION LOCK ` (any version) or the legacy `WORK ORDER`, MUST locate the newest
such comment across both protocols by comment time when several exist, and MUST
NOT execute an order or sub-order above the coordinator session's admitted model
rung. Locating the newest header-matching comment MUST match on the `EXECUTION
LOCK ` header prefix alone, version-agnostically, so a newer lock of any version
outranks an older lock of any version; it MUST NOT parse or validate the
`EXECUTION LOCK` version or `Source:` mode, and MUST NOT merge fields from an
older comment into a newer one, whether both comments use the same protocol or
not. `start` and `revise` MUST then parse and validate the located comment before
acting on it: an unrecognized `EXECUTION LOCK` version or an unrecognized
`Source:` mode MUST refuse execution and route to triage, and MUST NOT fall back
to an older comment.

#### Scenario: No work order exists

- **WHEN** `start` scans the ticket comments and finds no fenced block beginning
  `EXECUTION LOCK ` or `WORK ORDER`
- **THEN** it refuses implementation and routes the ticket back to triage instead
  of inventing scope

#### Scenario: Both protocols are present

- **WHEN** the ticket carries an older legacy `WORK ORDER` comment and a newer
  `EXECUTION LOCK v2` comment, or the reverse order by post time
- **THEN** `start` and `revise` use whichever comment is newest by post time,
  regardless of which protocol it uses, and read no field from the older comment

#### Scenario: A newer lock supersedes an older lock of a different version

- **WHEN** a ticket carries an older `EXECUTION LOCK v2` comment and a newer
  `EXECUTION LOCK v3` comment
- **THEN** locate returns the newer v3 comment on the header match alone, without
  regard to either comment's version, and `start` and `revise` admit or refuse
  based on whether v3 is a version they recognize — never by falling back to the
  older v2 comment

#### Scenario: The newest comment names an unrecognized source mode

- **WHEN** the newest header-matching comment is an `EXECUTION LOCK v2` fence
  whose `Source:` mode is not `openspec`, `repository-native`, or `inline`
- **THEN** `start` and `revise` refuse execution and route to triage instead of
  falling back to an older comment

## ADDED Requirements

### Requirement: Execution lock envelope grammar

The work-order template MUST define one `EXECUTION LOCK v2 <ticket-id> <lock-id>`
envelope grammar with exactly three `Source:` modes: `openspec
<change-path>@<full-commit-oid>`, `repository-native <path>@<full-commit-oid>`, and `inline`.
`<lock-id>` MUST be a positive integer, unique within the ticket, starting at 1 and
incremented for each lock posted on that ticket that supersedes a prior one. The
envelope MUST exist in a flat shape (one fence, one agent) and a chunked shape
(one header fence plus one sub-lock fence per sub-order), and every fence of either
shape MUST carry `Surface lifecycle:`, `Review depth:`, and, on the flat and
chunked-header fences, `Profile:`. Under the `openspec` and `repository-native`
modes, task and acceptance-anchor selection MUST be positional — plain numbers
resolved against the pinned commit's own numbering, with no inline identifier
markers. Whole-change ownership is a property of the ticket, not of the fence: an
ordinary ticket's flat lock or chunked header MUST select its whole pinned change
(`all`), and an epic child's flat lock or chunked header MUST select its owned
subset of the shared parent change; a chunked lock's sub-locks MUST each select a
disjoint positional slice of the header's own selection, together covering exactly
what the header selected. Under a pinned source, `Do` MUST be absent from the fence
— the pinned tasks are the Do steps — and `Done when` MUST state only the lock's
own delivery acceptance (the verification command's expectation and the
stop-at-pull-request condition), never a restatement of the pinned source's
acceptance criteria; `Context` remains present as orientation only. The `inline`
mode MUST carry the full `Context` / `Do` / `Done when` payload verbatim as the
fence body, unchanged from the payload a pre-lock work order carried. Every lock,
flat or per sub-lock, MUST carry an `Expected diff` naming a closed allowlist of
repository-relative paths with no escape clause, and parallel sub-locks'
allowlists MUST be disjoint.

#### Scenario: An ordinary ticket's lock pins an OpenSpec change

- **WHEN** triage posts a lock with `Source: openspec <change-path>@<oid>` for an
  ordinary (non-epic-child) ticket
- **THEN** the lock's selected tasks and acceptance anchors cover the whole pinned
  change rather than a subset

#### Scenario: A repository with no durable plan record

- **WHEN** the target repository keeps neither an OpenSpec change nor another
  repository-native plan artifact for the ticket
- **THEN** the posted lock sets `Source: inline` and carries the complete
  `Context` / `Do` / `Done when` payload in the fence, with no `Selected tasks:` or
  `Acceptance anchors:` fields

#### Scenario: A chunked ordinary ticket's sub-locks divide the whole change

- **WHEN** a chunked lock's header pins `Source: openspec <change-path>@<oid>` for
  an ordinary (non-epic-child) ticket
- **THEN** the header's `Selected tasks:` reads `all`, and each sub-lock's
  `Selected tasks:` and `Acceptance anchors:` are a disjoint positional slice of
  the header's own selection that together cover it exactly, with no sub-lock
  restating another sub-lock's selection or the pinned source's own
  Context/Do/Done-when prose

#### Scenario: A pinned lock's Done when never restates the source's acceptance

- **WHEN** a flat or sub-lock fence pins `Source: openspec` or `Source:
  repository-native`
- **THEN** the fence carries no `Do` field, and its `Done when` states only the
  verification command's expectation and the stop-at-pull-request condition, never
  the pinned source's own acceptance criteria for the selected tasks

### Requirement: Execution lock authoring in an OpenSpec repository

Triage in an OpenSpec-backed repository MUST author the ticket's change (proposal,
tasks, and design and spec deltas as the decisions require) on the ticket branch,
run strict OpenSpec validation against it, and commit it before posting a lock.
The lock's `Source:` commit MUST be read back from the commit just made rather than
predicted or remembered, and MUST be the full commit object id, never an
abbreviated form. A change that fails strict validation MUST NOT be pinned or
posted.

#### Scenario: Triage authors and pins a change

- **WHEN** triage in an OpenSpec-backed repository finishes drafting the ticket's
  change and `openspec validate <change-id> --strict` passes
- **THEN** triage commits the change on the ticket branch, reads back the exact
  commit that produced, and posts a lock whose `Source:` names that repository
  path and full commit oid

#### Scenario: Strict validation fails

- **WHEN** the authored change does not pass `openspec validate <change-id>
  --strict`
- **THEN** triage resolves the validation failures before any commit or lock is
  made, and posts nothing in the meantime

### Requirement: Fail-closed execution admission

`start` MUST resolve and validate the located lock's pinned source before any
implementation, coordinator-mode switch, or worker dispatch, and `revise` MUST
repeat that admission every round against whatever lock is newest at that moment.
An unrecognized envelope version or `Source:` mode, an abbreviated or
unresolvable commit OID, a source path absent at the pinned tree, an archived or
strictly invalid change, a selected task or acceptance anchor absent at the
pinned commit, an empty selection, a ticket branch that does not contain the
pinned commit, a missing `Verification:`, `Expectation:`, or `Expected diff`, or
overlapping ownership between parallel chunks MUST each refuse execution by name
and route to attended re-triage. No refusal may degrade to a warning, resolve a
short OID, substitute the ticket branch head for the pinned commit, or fall back
to an older comment. An edit to what the pinned source authorizes — its prose,
its requirements and scenarios, the text of a task, or a task added or removed —
MUST refuse until a newer lock pins the amended commit. Ticking or unticking a
`tasks.md` checkbox MUST NOT refuse, because the executor is required to record
completed work that way.

#### Scenario: The pinned commit is not on the ticket branch

- **WHEN** `start` admits a lock whose pinned commit the ticket branch does not
  contain
- **THEN** it refuses by name and routes to attended re-triage, rather than
  substituting the branch head for the pin

#### Scenario: The source was amended without a newer lock

- **WHEN** the pinned source's requirements or task text changed after the lock
  pinned its commit, and no newer lock names the later commit
- **THEN** execution refuses as an unauthorized amendment

#### Scenario: The executor records a completed task

- **WHEN** the executor ticks a `tasks.md` checkbox in the pinned change as work
  completes, and a later `revise` round re-runs admission
- **THEN** that commit passes the amendment row and the round proceeds under the
  same lock and pin

#### Scenario: A lock omits its expected diff

- **WHEN** the located lock carries no `Expected diff` allowlist
- **THEN** admission refuses, since nothing would bound what the executor may
  touch
