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

### Requirement: Epic authority and labels

An Epic MUST use its OpenSpec proposal and design as the durable destination,
scope, risk, and decision authority; native tracker children as its work units;
and the independent `epic`, `spike`, `build`, and `deferred` labels as its type
protocol. Live tracker state MUST win over the Epic's derived ledger.

#### Scenario: The ledger disagrees with a child issue

- **WHEN** an Epic home session reads a child whose live state or labels differ
  from its ledger line
- **THEN** the live tracker state governs and the home session updates the derived
  ledger rather than treating the ledger as authoritative

### Requirement: Epic planning lifecycle

The Epic home session MUST be the sole writer of the derived ledger on its
standing draft planning pull request, MUST admit a build only when no open spike
or fog can invalidate it, and MUST verify completion from live child and merge
state before archiving and closing the Epic.

#### Scenario: An Epic is ready for close-out

- **WHEN** no spike child is open, every build child is merged or closed not
  planned, and no open deferred child remains
- **THEN** the home session may prepare the final ledger-and-archive change and
  wait for human merge before closing the Epic

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
including nested review and orchestration. Automatic activation outside an
invoked parent MUST ask once before dispatch, and every dispatch MUST continue to
use pack-owned isolated adapters while excluding credentials, secrets, patient
data, `.env`, and real database contents.

#### Scenario: Orchestration activates implicitly

- **WHEN** a workflow reaches orchestration without a literal invocation or an
  invoked parent that already grants bounded dispatch consent
- **THEN** it asks once with the payload, destination, and exclusions and stops if
  consent is denied

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
