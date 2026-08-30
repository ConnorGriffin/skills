# Ticket workflow — deltas

## MODIFIED Requirements

### Requirement: Work-order lock and model fit

`start` and `revise` MUST refuse execution when no work-order comment exists in
either recognized protocol, MUST use the newest recognized comment across both
protocols when several exist, and MUST NOT execute an order or sub-order above the
coordinator session's admitted model rung. A comment is recognized when its fenced
block starts `EXECUTION LOCK v2` with a recognized version and `Source:` mode, or
starts the legacy `WORK ORDER` marker. Locating the newest recognized comment MUST
NOT merge fields from an older comment into a newer one, whether both comments use
the same protocol or not.

#### Scenario: No work order exists

- **WHEN** `start` scans the ticket comments and finds no fenced block beginning
  `EXECUTION LOCK v2` or `WORK ORDER`
- **THEN** it refuses implementation and routes the ticket back to triage instead
  of inventing scope

#### Scenario: Both protocols are present

- **WHEN** the ticket carries an older legacy `WORK ORDER` comment and a newer
  `EXECUTION LOCK v2` comment, or the reverse order by post time
- **THEN** `start` and `revise` use whichever comment is newest by post time,
  regardless of which protocol it uses, and read no field from the older comment

## ADDED Requirements

### Requirement: Execution lock envelope grammar

The work-order template MUST define one `EXECUTION LOCK v2 <ticket-id> <lock-id>`
envelope grammar with exactly three `Source:` modes: `openspec
<change-path>@<full-commit-oid>`, `repository-native <path>@<oid>`, and `inline`.
The envelope MUST exist in a flat shape (one fence, one agent) and a chunked shape
(one header fence plus one sub-lock fence per sub-order), and every fence of either
shape MUST carry `Surface lifecycle:`, `Review depth:`, and, on the flat and
chunked-header fences, `Profile:`. Under the `openspec` and `repository-native`
modes, task and acceptance-anchor selection MUST be positional — plain numbers
resolved against the pinned commit's own numbering, with no inline identifier
markers — and an ordinary ticket's lock MUST select its whole pinned change while
only an epic child's lock MUST select a subset. The `inline` mode MUST carry the
full `Context` / `Do` / `Done when` payload verbatim as the fence body, unchanged
from the payload a pre-lock work order carried. Every lock, flat or per sub-lock,
MUST carry an `Expected diff` naming a closed allowlist of repository-relative
paths with no escape clause, and parallel sub-locks' allowlists MUST be disjoint.

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

#### Scenario: A chunked lock's sub-locks divide one pinned source

- **WHEN** a chunked lock's header pins `Source: openspec <change-path>@<oid>` or
  `Source: repository-native <path>@<oid>`
- **THEN** each sub-lock's `Selected tasks:` and `Acceptance anchors:` are a
  disjoint positional subset of that one pinned commit's numbering, and no
  sub-lock restates another sub-lock's selection or the pinned source's own
  Context/Do/Done-when prose

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
