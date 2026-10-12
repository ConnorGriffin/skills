# Planning and review routing

## Purpose

Define how uncertain work becomes an authoritative, risk-bounded build plan and
how plans, code, security changes, and perspective reviews reach the right check.

## Requirements

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

A research-worker dispatch MUST run one read-only subagent with hosted web search
and fetch allowed and MUST NOT grant repository writes or promise arbitrary shell
network access.

When a completed, resumable worker reports hosted source refusal with the defined
worker result, the coordinator MUST fetch the required public primary sources into
a unique scratch directory under the worker cwd and resume the same worker against
a manifest of that local material. This handoff is the sole exception to the
original-prompt-only worker-input rule. If the worker leaves no resumable session,
or neither source path can obtain the required sources, the research workflow MUST
stop clearly and MUST NOT report completed research or write a successful findings
artifact.

#### Scenario: Research starts with hosted source access

- **WHEN** the research skill dispatches its worker
- **THEN** the worker is a read-only subagent with hosted web tools allowed and no
  repository writes

#### Scenario: Research resumes after provider refusal

- **WHEN** a completed worker reports hosted web refusal as
  `SOURCE_ACCESS_UNAVAILABLE:` and its session is resumable
- **THEN** the coordinator places only public fetched sources and their URL
  manifest in a unique cwd-local scratch directory and resumes that same worker
  with the manifest path

#### Scenario: The failed worker cannot resume

- **WHEN** the worker fails and leaves no resumable session
- **THEN** research stops visibly and writes no successful findings artifact

#### Scenario: A non-research worker starts normally

- **WHEN** a subagent is dispatched without hosted web tools in its allowlist
- **THEN** hosted live source access remains disabled and its other tools are
  unchanged
