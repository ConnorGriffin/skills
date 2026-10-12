## ADDED Requirements

### Requirement: Triage resolves uncertainty before locking

Triage MUST name the ticket's dominant uncertainty and resolve it before drafting:
it MUST put decisions only the user can make to the user in batched rounds of
numbered questions, MUST execute the opening steps of any order that rests on an
assumption nobody has run, and MUST give every count, path, version, or enumeration
the order states as a command and its verbatim output. Triage MUST settle a risk
contract for every bounded order. When nothing is uncertain, triage MUST say so,
name its defaults, and continue without asking.

#### Scenario: A decision only the user can make

- **WHEN** grounding leaves a choice that changes what gets built
- **THEN** triage asks it in a numbered round with options and a recommendation and
  drafts nothing that depends on the answer until it arrives

#### Scenario: The order rests on an unrun assumption

- **WHEN** a draft claims that a parameter, flag, or fixture is honored by a tool
- **THEN** triage runs one live probe of that claim and amends the draft before review

### Requirement: Oversized work becomes tracked child issues

Triage MUST slice work that will not fit one session into pull-request-sized child
issues, each triaged into its own work order, and MUST track them as a checklist on
the parent ticket. Triage MUST record which slicing traits fired.

#### Scenario: Two slicing traits fire

- **WHEN** grounding finds two or more slicing traits, or a projected peak past the
  session band
- **THEN** triage files child issues, lists them on the parent's checklist, and
  locks no single order for the whole effort

### Requirement: Review at the stamped depth

Triage MUST stamp one review depth with a reason, raised to Full by the sensitivity
floor. At Full depth only, triage MUST run one cold, fresh-context `/plan-review`
round on the draft. `start` MUST run one `/code-review` pass at the stamped depth
before opening the pull request, and `revise` MUST review each round's changes the
same way.

#### Scenario: A Focused ticket is triaged

- **WHEN** triage stamps Focused or Targeted depth
- **THEN** it checks the draft against the template's checks and dispatches no plan
  reviewer

#### Scenario: A Full ticket is triaged

- **WHEN** triage stamps Full depth
- **THEN** one cold plan reviewer reads the draft once and triage reproduces each
  objection before acting on it

### Requirement: Four verbs with human gates

The ticket workflow MUST expose one verb at a time: `triage` grounds the ticket and
posts a locked work order after the user approves it; `start` executes the newest
order in the ticket's worktree and, for an OpenSpec-backed ticket, proves that its
one active change can apply to a freshly fetched current baseline without mutating
either authoritative tree, then opens a pull request; `revise` actions one review
round and, for an OpenSpec-backed ticket, repeats that applicability proof before
pushing; and `finalize` reconciles a merged or explicitly abandoned pull request with
the tracker and local worktree state. Agents MUST stop at the pull request boundary
and MUST NOT merge.

#### Scenario: A ticket reaches implementation

- **WHEN** `start` admits the newest work order for an OpenSpec-backed ticket
- **THEN** it reuses the ticket's branch and worktree, implements and verifies the
  order, proves its changed active OpenSpec delta applies in a disposable copy,
  opens one pull request, and stops for human review

#### Scenario: A base ref resembles a Git option

- **WHEN** the public applicability command receives a base-ref value that could be
  parsed as a Git option rather than a local revision
- **THEN** it resolves the value with Git's end-of-options form to a verified local
  commit before merge-base or export, and an unresolved value stops locally without
  invoking a remote

#### Scenario: A structurally valid delta cannot apply

- **WHEN** strict validation passes but a disposable archive reports an unmatched
  modified requirement and no archive result
- **THEN** the workflow stops before the pull request and emits exactly two ordered
  `ticket:` stderr lines: the unmatched requirement first, then direction to add
  the missing rename mapping or correct the modified header; it leaves the active
  change and baseline unchanged

#### Scenario: Applicability infrastructure fails

- **WHEN** executable launch, base export, active-change overlay, or archive CLI
  execution fails during the disposable applicability proof
- **THEN** the public command exits nonzero with one `ticket:` stderr diagnostic,
  removes its temporary directory, and leaves the ticket worktree and base-ref
  OpenSpec trees unchanged

#### Scenario: A ticket changes several active changes

- **WHEN** base-diff discovery finds more than one active OpenSpec change still
  present in the ticket tree
- **THEN** preflight stops visibly because finalization owns one archive unit

#### Scenario: A ticket uses another change-record convention

- **WHEN** start or revise operates a repository whose ticket is not backed by an
  OpenSpec active change
- **THEN** it keeps that repository's verification and pull-request or push path
  without invoking the OpenSpec applicability command

### Requirement: Ticket mutation boundary

Ticket verbs MUST confine writes to the selected ticket's worktree, branch, active
change, comments, and status, plus operator-local state the workflow needs (claims,
fetched refs). Creating or changing a separate branch, issue, pull
request, or repository artifact MUST require the user's approval of that exact
target and mutation. Reading something for grounding MUST NOT grant authority to
write it.

#### Scenario: Required operator-local workflow state is written

- **WHEN** a verb records a claim or a fetched ref
- **THEN** it proceeds without separate approval and gains no authority over a
  distinct repository or tracker concern

#### Scenario: An external amendment is a true prerequisite

- **WHEN** a safe order depends on first changing another issue, branch, or artifact
- **THEN** triage names the exact target and mutation and stops until the user
  approves it

### Requirement: Execution lock fence grammar

The work-order template MUST define one `EXECUTION LOCK v2 <ticket-id> <lock-id>`
fence with exactly three `Source:` modes: `openspec <change-path>@<full-commit-oid>`,
`repository-native <path>@<full-commit-oid>`, and `inline`. `<lock-id>` MUST be a
positive integer, 1 for the ticket's first lock and one more than the highest for
each superseding lock. Every fence MUST carry `Surface lifecycle:`, `Review depth:`,
`Profile:`, `Verification:`, `Expectation:`, and an `Expected diff` naming a closed
allowlist of repository-relative paths with no escape clause. Under a pinned source,
`Do` MUST be absent and `Done when` MUST state only the verification expectation and
the stop at the pull request; the `inline` mode MUST carry the full `Context`, `Do`,
and `Done when` payload.

#### Scenario: A repository with no durable plan record

- **WHEN** the target repository keeps neither an OpenSpec change nor another
  versioned plan artifact for the ticket
- **THEN** the posted lock sets `Source: inline` and carries the complete `Context`,
  `Do`, and `Done when` payload in the fence

#### Scenario: A pinned lock's Done when never restates the source's acceptance

- **WHEN** a fence pins `Source: openspec` or `Source: repository-native`
- **THEN** it carries no `Do` field, and its `Done when` states only the
  verification expectation and the stop at the pull request

### Requirement: Start-peak measurement and review depth

Each participating session MUST be claimable with both its responsibility
(`coordinator`, `worker`, or `reviewer`) and the ticket lifecycle verb that
produced the claim. Finalization MUST compute responsibility-tagged and
verb-tagged costs separately and print the resulting record as JSON. It MUST NOT
create or append a ticket-wide telemetry store. Measurable non-reviewer `start` claims
alone MUST calibrate an order; triage, revise, finalize, and reviewer peaks MUST remain independent
overhead. Claims without a lifecycle verb MUST remain readable as legacy data and
MUST NOT be guessed into a verb. A session MUST NOT be reused under a different
lifecycle verb; same-verb resumes remain valid, while a later verb requires a
fresh session. Review depth MUST be stamped from change scope and sensitivity
rather than inferred from recorded slicing outcomes.

#### Scenario: A measurable ticket is finalized

- **WHEN** finalization computes a slicing record from attributable claims
- **THEN** `record` prints the complete JSON record and finalization creates no
  ticket telemetry file

#### Scenario: A flat ticket has expensive lifecycle overhead

- **WHEN** triage, revise, or finalize peaks above the slicing band while the
  measurable non-reviewer `start` claim remains below it
- **THEN** the flat verdict is based on the `start` peak and reports lifecycle
  overhead separately

#### Scenario: A claimed flat ticket has no attributable execution

- **WHEN** at least one attributable claim exists but no measurable non-reviewer
  `start` claim exists, including when every readable claim predates
  lifecycle-verb attribution
- **THEN** finalization returns `unmeasurable` and makes no slicing judgment

#### Scenario: A flat ticket has no attributable claims

- **WHEN** no attributable in-repository claim exists
- **THEN** finalization preserves the existing `no-data` outcome

#### Scenario: A later lifecycle verb follows execution

- **WHEN** revise or finalize follows the session that executed `start`
- **THEN** the later verb runs in a fresh session so its context cannot inflate the
  start-attributed execution peak

#### Scenario: A session is re-claimed under another verb

- **WHEN** `claim` receives a ticket/session pair already persisted under a
  different lifecycle verb
- **THEN** it preserves and prints the persisted claim, reports one visible
  non-blocking conflict naming both verbs, and does not claim that the submitted
  verb was stored

### Requirement: Under-sliced verdict reporting

Finalization MUST report the misprediction for an `under-sliced` verdict, naming which rubric call was wrong and by how much. It
MUST NOT draft a slicing-rubric amendment, MUST NOT prompt the operator on that
path, and MUST NOT edit the rubric. Finalization MUST NOT report a misprediction for `no-data` or
`unmeasurable`. A change to the
slicing thresholds themselves MUST be operator-initiated and MUST update the
rubric prose and the helper constant together.

#### Scenario: A measured order was too large

- **WHEN** role-aware measurement returns `under-sliced`
- **THEN** finalization reports the misprediction against the stamped shape and
  neither drafts a rubric diff nor asks the operator anything

#### Scenario: A verdict is not a misprediction

- **WHEN** role-aware measurement returns `no-data` or `unmeasurable`
- **THEN** finalization reports that verdict's own meaning and reports no slicing
  misprediction

## MODIFIED Requirements

### Requirement: Work-order lock

`start` and `revise` MUST refuse execution when no comment's fence header starts
`EXECUTION LOCK ` (any version) or the legacy `WORK ORDER`, and MUST use the newest
such comment by post time when several exist. Locating it MUST match on the header
alone and MUST NOT merge fields from an older comment into a newer one. `start` and
`revise` MUST then admit the located comment, and an unrecognized version or
`Source:` mode MUST refuse and route to triage rather than fall back to an older
comment.

#### Scenario: No work order exists

- **WHEN** `start` finds no fenced block beginning `EXECUTION LOCK ` or `WORK ORDER`
- **THEN** it refuses implementation and routes the ticket back to triage

#### Scenario: A newer lock supersedes an older lock of a different version

- **WHEN** a ticket carries an older lock and a newer lock of any version
- **THEN** locate returns the newer comment, and `start` admits or refuses it without
  falling back to the older one

#### Scenario: Both protocols are present

- **WHEN** the ticket carries an older legacy `WORK ORDER` comment and a newer
  `EXECUTION LOCK v2` comment, or the reverse order by post time
- **THEN** `start` and `revise` use whichever comment is newest by post time and
  read no field from the older comment

#### Scenario: The newest comment names an unrecognized source mode

- **WHEN** the newest header-matching comment is an `EXECUTION LOCK v2` fence whose
  `Source:` mode is not `openspec`, `repository-native`, or `inline`
- **THEN** `start` and `revise` refuse execution and route to triage instead of
  falling back to an older comment

### Requirement: Independent type and status labels

The GitHub binding MUST keep the `build` type label independent from the `ticket:*`
status labels. A code ticket's triage transition MUST ensure `build` before applying
`ticket:triaged`, and later ticket verbs MUST move only the status axis they own.

#### Scenario: A code ticket becomes in progress

- **WHEN** `start` reuses or cuts the ticket worktree
- **THEN** the binding adds `ticket:in-progress` and removes `ticket:triaged`
  without removing the ticket's `build` type

### Requirement: Coordinator-owned review handoff

When a ticket verb delegates build work, it MUST dispatch a native subagent with the
model named, and the coordinator MUST dispatch every mandatory reviewer and resume
that same worker with `SendMessage` to act on the verdict. A worker MUST NOT launch
its own reviewer. A review that fails to launch or returns no verdict MUST be
reported as unavailable and MUST block the workflow from advancing as reviewed.

#### Scenario: Delegated start reaches mandatory independent review

- **WHEN** a delegated build worker reports its change verified
- **THEN** the coordinator runs `/code-review` and resumes the same worker with the
  findings or the clean verdict

#### Scenario: Delegated review evidence is unavailable

- **WHEN** a review fails to launch or returns no verdict
- **THEN** the coordinator reports the review as unavailable and does not advance
  the workflow as reviewed

### Requirement: Fail-closed execution admission

`start` MUST admit the located lock before any implementation, and `revise` MUST
repeat that admission every round against whatever lock is newest. An unrecognized
envelope version or `Source:` mode, an abbreviated or unresolvable commit OID, a
source path absent at the pinned tree, an archived or strictly invalid change, a
ticket branch that does not contain the pinned commit, or a missing `Verification:`,
`Expectation:`, or `Expected diff` MUST each refuse execution by name and route to
triage. No refusal may resolve a short OID, substitute the branch head for the pin,
or fall back to an older comment. An edit to what the pinned source authorizes MUST
refuse until a newer lock pins it; ticking or unticking a `tasks.md` checkbox MUST
NOT refuse.

#### Scenario: The pinned commit is not on the ticket branch

- **WHEN** `start` admits a lock whose pinned commit the ticket branch does not
  contain
- **THEN** it refuses by name and routes to triage rather than substituting the
  branch head

#### Scenario: The source was amended without a newer lock

- **WHEN** the pinned source's requirements or task text changed after the lock
  pinned its commit, and no newer lock names the later commit
- **THEN** execution refuses as an unauthorized amendment

#### Scenario: The executor records a completed task

- **WHEN** the executor ticks a `tasks.md` checkbox in the pinned change and a later
  `revise` round re-runs admission
- **THEN** that commit passes and the round proceeds under the same lock

#### Scenario: A lock omits its expected diff

- **WHEN** the located lock carries no `Expected diff` allowlist
- **THEN** admission refuses, since nothing would bound what the executor may touch

### Requirement: Slicing traits are optional record evidence

Finalization MUST be able to record a ticket whose work order fired no slicing
traits without inventing a sentinel trait. The public `record` command MUST emit
an empty `traits` array when no `--trait` flag is supplied. When one or more
`--trait` flags are supplied, it MUST preserve their values and order. Trait
presence MUST NOT alter verdict calculation or session attribution.

#### Scenario: A flat order fired no slicing traits

- **WHEN** finalization invokes `record` without a `--trait` flag
- **THEN** the command succeeds and emits `"traits": []`

#### Scenario: An order fired multiple slicing traits

- **WHEN** finalization invokes `record` with multiple `--trait` flags
- **THEN** the command emits every supplied trait in the same order

## REMOVED Requirements

### Requirement: Role-aware measurement and review depth

**Reason**: ADR 300 removes chunked orders, so worker peaks no longer calibrate
chunk size and no chunked review-cost scenario remains.

**Migration**: See `Start-peak measurement and review depth`.

### Requirement: Slicing amendment verdicts

**Reason**: ADR 300 removes `ticket.py record`'s chunked verdicts
(`still-degraded`, `over-sliced`, `coordinator-only`, `coordination-degraded`).

**Migration**: See `Under-sliced verdict reporting`.

### Requirement: Four-verb lifecycle

**Reason**: ADR 300 drops the unconditional `/scope` step and chunked execution
that this requirement named.

**Migration**: See `Four verbs with human gates`.

### Requirement: Triage mutation authority

**Reason**: ADR 300 removes the Codebase Memory state and epic-child amendment this
requirement carved out.

**Migration**: See `Ticket mutation boundary`.

### Requirement: Execution lock envelope grammar

**Reason**: ADR 300 removes chunked sub-locks and positional task selection.

**Migration**: See `Execution lock fence grammar`.

### Requirement: Slicing and chunk coordination

**Reason**: ADR 300 removes chunked orders and the coordinator mode that ran them;
native subagents replace the pack's orchestration.

**Migration**: Triage files oversized work as child issues on a parent checklist;
see `Oversized work becomes tracked child issues`.

### Requirement: Epic promotion distinguishes uncertainty from bulk

**Reason**: ADR 300 removes the `epic` skill.

**Migration**: Unsettled decisions are resolved in triage's question rounds or a
spike child; see `Triage resolves uncertainty before locking`.

### Requirement: Epic child triage carries required parent-plan amendments

**Reason**: ADR 300 removes the `epic` skill and its parent-plan branch.

**Migration**: A child issue is an ordinary ticket with its own change record.

### Requirement: Epic child implementation preserves the parent archive owner

**Reason**: ADR 300 removes the `epic` skill and its shared parent change.

**Migration**: Each child ticket's own change is archived by its own finalization.

## RENAMED Requirements

- FROM: `### Requirement: Work-order lock and model fit`
- TO: `### Requirement: Work-order lock`
