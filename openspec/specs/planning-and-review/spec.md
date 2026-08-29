# Planning and review routing

## Purpose

Define how uncertain work becomes an authoritative, risk-bounded build plan and
how plans, code, security changes, and perspective reviews reach the right check.

## Requirements

### Requirement: Scope routing

`/scope` MUST classify the dominant uncertainty and route to exactly one
specialist. When nothing is genuinely uncertain it MUST return control without
inventing a question or creating a ledger, and ticket triage MUST invoke this
scope decision unconditionally before admitting a work order.

#### Scenario: A grounded ticket has no unresolved decision

- **WHEN** ticket triage invokes `/scope` after grounding and every open point has
  an obvious default
- **THEN** `/scope` reports that there is nothing to scope and returns without a
  ledger or a manufactured interview

### Requirement: Scope records and risk admission

Outside an epic child, a routed scope effort MUST record decisions, open
questions, and spawned tasks in its scope ledger, and a bounded plan MUST carry
its settled risk contract in the downstream authoritative artifact before build.
An epic child MUST instead keep its temporary scope instrumentation in untracked
session scratch and rely on its parent epic and stamped work order.

#### Scenario: Scope admits bounded work

- **WHEN** a non-epic scope effort becomes ready to build
- **THEN** every durable disposition is discharged and the authoritative issue,
  plan, or brief contains the settled must-prevent, recovery, accepted-failure,
  unsupported, and evidence obligations

#### Scenario: Scope runs for an epic child

- **WHEN** `/scope` routes work whose parent is confirmed as an epic
- **THEN** its specialist uses untracked session scratch and creates no child
  scope ledger or `docs/scope` artifact

### Requirement: Review routing and containment

`/review` MUST classify a review subject and route it to exactly one registered
review skill. A registered route whose implementation is missing MUST stop rather
than substitute another review, and persona material identifying real colleagues
MUST remain in private data rather than this public pack.

#### Scenario: A registered review route is unavailable

- **WHEN** route resolution finds the requested route but cannot find its named
  review skill
- **THEN** review stops with the missing-skill result and does not run a nearby
  route

### Requirement: Orchestration authorization and isolation

Literal `/orchestrate` invocation MUST authorize only the work order or task
prompt plus the repository code and documentation needed for mandatory dispatches,
including review and orchestration. Automatic activation outside an invoked parent
MUST ask once before dispatch, and every dispatch MUST continue to use pack-owned
isolated adapters while excluding credentials, secrets, patient data, `.env`, and
real database contents. The coordinator MUST own every mandatory reviewer dispatch
reached by delegated work. Its delegation prompt MUST identify the mandatory-review
handoff, and the worker MUST return or write its review-ready result through the
coordinator-recorded durable result locator at that boundary. The coordinator MUST
collect that result and resume the same worker with verified findings for correction
or a verified clean verdict to finish. Unavailable review evidence MUST block the
workflow from advancing as reviewed. Direct adapter dispatch from inside a sandboxed
worker is unsupported.

#### Scenario: Orchestration activates implicitly

- **WHEN** a workflow reaches orchestration without a literal invocation or an
  invoked parent that already grants bounded dispatch consent
- **THEN** it asks once with the payload, destination, and exclusions and stops if
  consent is denied

#### Scenario: Delegated work reaches mandatory review

- **WHEN** an Orchestrate worker returns work whose governing workflow requires independent review
- **THEN** the coordinator dispatches that reviewer through the existing adapter and resumes the same worker with actionable findings or a verified clean verdict instead of asking the worker to launch a nested reviewer

#### Scenario: Delegated review evidence is unavailable

- **WHEN** the mandatory reviewer has a failed launch, nonzero exit, missing result artifact, or missing verdict
- **THEN** the coordinator reports the review as unavailable and does not advance the workflow as reviewed

### Requirement: Decision-record home

A new load-bearing decision in a repository that tracks design with OpenSpec MUST
be recorded in the relevant change's `design.md` under an `## ADR <issue> — Title`
heading. Existing `docs/adr/` records MUST remain as legacy history and MUST NOT
become the home for new decisions in that repository.

#### Scenario: An OpenSpec change settles a lasting decision

- **WHEN** implementation depends on a load-bearing decision that should outlive
  the session
- **THEN** the decision is recorded in that change's `design.md` and no parallel
  sequential or new `docs/adr/` record is created

### Requirement: Epic OpenSpec authority

An Epic MUST use its OpenSpec proposal, design, and tasks as the durable
destination, scope, risk, decision, and implementation-sequence authority:
`tasks.md` links every tracker child issue in checked implementation order.
Native tracker children remain its work units under the independent `epic`,
`spike`, `build`, and `deferred` type labels, and live tracker state MUST be
authoritative for child type, status, dependencies, deferral, and closing pull
requests. The Epic MUST NOT maintain a derived ledger or other parallel index
of tracker state.

#### Scenario: Planning state is read in a fresh session

- **WHEN** an Epic home session resumes and needs current planning and child
  state
- **THEN** it reads the active change's proposal, design, and tasks for durable
  planning and live tracker state for child work state, with no derived ledger
  to reconcile

### Requirement: Epic lifecycle without a ledger

The Epic home session MUST keep the active change coherent from planning
altitude without a dedicated planning worktree or standing planning pull
request. Imprecise concerns MUST be kept as named open questions in the
change's `design.md`, cleared only by recording a decision there or promoting
the question to a tracker spike, and a build MUST NOT be admitted while an open
spike or named open question can invalidate its outcome, constraints, or
acceptance criteria. Completion MUST be verified from live child and merge
state, after which close-out follows the repository's archive guidance for the
active change.

#### Scenario: An imprecise concern arrives during planning

- **WHEN** the home session captures a concern too imprecise to ticket
- **THEN** it records a named open question in `design.md` and clears it only
  through a recorded decision or a promoted spike, never by silent deletion

#### Scenario: An Epic is ready for close-out

- **WHEN** no spike child is open, every build child is merged or closed not
  planned, and no open deferred child remains
- **THEN** the home session verifies those predicates from live tracker state,
  follows the repository's archive guidance for the active change after the
  human-merged work is verified, and closes the Epic issue

### Requirement: Coordinator wait narration follows state changes

A coordinator governed by the shared communication contract MUST emit no update
for re-polled unchanged external state, result locators or files, result sets, or
elapsed time alone, including after three no-news batches. It MUST report worker
completion, worker failure, an abandoned wait, an operator-relevant external-state
or coordinator decision/action milestone declared before the wait, and any state
change the coordinator itself caused. A time interval alone MUST NOT qualify as a
milestone.

#### Scenario: A worker remains active across polls

- **WHEN** repeated checks find the same running state, result locator or files,
  or result set and no operator-relevant external-state or decision/action
  milestone has been crossed
- **THEN** the coordinator continues waiting without emitting a status update

#### Scenario: A wait reaches an outcome

- **WHEN** the worker completes or fails, or the coordinator abandons the wait
- **THEN** the coordinator reports that outcome immediately

### Requirement: Research worker source access

A research-worker dispatch MUST explicitly enable provider-hosted web search
and fetch while preserving the selected filesystem sandbox, and the selected
adapter MUST persist that capability across resume. The capability MUST remain
off for dispatches that do not request it and MUST NOT promise arbitrary shell
network access.

When a successfully completed, resumable worker reports hosted source refusal
with the defined worker result, the coordinator MUST fetch the required public
primary sources into a unique scratch directory under the worker cwd and resume
the same worker against a manifest of that local material. This handoff is the
sole exception to the original-prompt-only worker-input rule. If the adapter
fails without a resumable session, or neither source path can obtain the
required sources, the research workflow MUST stop clearly and MUST NOT report
completed research or write a successful findings artifact.

#### Scenario: Research starts with hosted source access

- **WHEN** the research skill dispatches a read-only worker
- **THEN** the selected adapter enables its hosted web tools without granting
  repository writes or arbitrary command-network access

#### Scenario: Research resumes after provider refusal

- **WHEN** a successfully completed worker reports hosted web refusal as
  `SOURCE_ACCESS_UNAVAILABLE:` and its state is resumable
- **THEN** the coordinator places only public fetched sources and their URL
  manifest in a unique cwd-local scratch directory and resumes that same worker
  with the manifest path

#### Scenario: The failed worker cannot resume

- **WHEN** an adapter failure leaves no terminal state with a session ID
- **THEN** research stops visibly and writes no successful findings artifact

#### Scenario: A non-research worker starts normally

- **WHEN** an adapter start omits the hosted-web opt-in
- **THEN** hosted live source access remains disabled and the existing sandbox
  behavior is unchanged

### Requirement: Epic dispatch remains human-operated

An epic coordinator MUST maintain the active OpenSpec plan, record decisions,
file bounded children, and write a draft order into each child issue without
dispatching workers, running ticket verbs, posting the executable work-order lock,
or opening pull requests. The operator MUST invoke ticket triage to ground and
independently review the draft before it becomes the fenced lock, and MUST explicitly
invoke each later child ticket phase that proceeds to attended work.

#### Scenario: A child work order is ready

- **WHEN** the epic has settled a child's decisions and written its draft order in the issue
- **THEN** the coordinator stops for the operator to invoke ticket triage instead of posting the lock or invoking a worker adapter

### Requirement: Epic child drafts pin their parent-plan base

Before handing a child to the operator, an epic coordinator MUST commit and push
the current active plan on the epic planning branch and record the remote branch
name without an `origin/` prefix plus full commit in the child issue draft. The epic coordinator MUST NOT open a
pull request for the planning branch.

#### Scenario: A child draft is handed to the operator

- **WHEN** the epic has finished the child's draft order
- **THEN** the draft identifies the pushed parent-plan branch name without an `origin/` prefix and the full commit it must still resolve to

#### Scenario: A child is already in flight

- **WHEN** a child implementation pull request has not yet been human-merged
- **THEN** the epic refuses every later child handoff

#### Scenario: The next child becomes eligible for handoff

- **WHEN** the prior child implementation pull request is human-merged
- **THEN** the epic advances its planning branch from the updated remote default branch, records any next planning update, and pins a new commit before handing off the next child

### Requirement: Epic slicing defaults to three or fewer children

An epic MUST default to no more than three child tickets. Before creating a fourth
or later child, the coordinator MUST record a justification in the active change's
`design.md` that explains why fewer, larger independently shippable builds do not fit.

#### Scenario: A proposed epic has four child tickets

- **WHEN** the coordinator cannot consolidate the proposed work into three independently shippable children
- **THEN** it records the capability boundary or dependency that requires the additional child before filing it

### Requirement: Epic planning artifacts ship with implementation

An epic coordinator MUST NOT open a pull request containing only epic planning
artifacts. When ticket triage requires a parent-plan amendment, it MUST commit that
amendment in the child's ticket worktree and the resulting planning updates MUST
travel with the implementation pull request that realizes them.

#### Scenario: Planning changes are ready but implementation has not run

- **WHEN** the epic's planning artifacts have changed and no child implementation is ready
- **THEN** the coordinator keeps the change active and waits rather than opening a planning-only pull request

### Requirement: Patient Codex worker liveness checks

When a Codex adapter remains running without terminal output or a session identifier,
the coordinator MUST wait another minute and check again. Silence, an empty session
identifier, PID presence, or low parent-process CPU MUST NOT by itself be treated as a
hang or authority to stop the worker.

The repository MUST contain a behavior test that pins this agent-facing instruction.

#### Scenario: Running adapter is quiet

- **WHEN** the Codex adapter is still running and has not emitted terminal output or a
  session identifier
- **THEN** the coordinator waits another minute before checking again and does not stop
  the worker based on silence alone

#### Scenario: Guidance regresses

- **WHEN** the patience instruction is removed or weakened
- **THEN** the behavior test fails
