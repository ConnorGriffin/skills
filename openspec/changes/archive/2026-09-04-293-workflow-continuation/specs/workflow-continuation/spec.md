# Workflow continuation

## ADDED Requirements

### Requirement: Parent continuation

An answered decision or completed helper MUST resume the next authorized caller step; an actual unanswered decision, denial, failed admission, missing required evidence, or explicit handoff MUST stop only the dependent work.

#### Scenario: Scope returns before triage has posted its lock

- **WHEN** the nested scope result is complete and another authorized triage step remains
- **THEN** the caller performs that step rather than ending on acknowledgment

### Requirement: Host-compatible decisions

Interview presentation MUST preserve the locked form where permitted and MUST obey higher-priority host restrictions elsewhere. A fallback MUST expose substantive considered alternatives and their costs, retain stable identifiers, accept free-form rejection or delegation, and wait for required answers.

#### Scenario: A host forbids textual multiple-choice questions

- **WHEN** the operator needs to decide between materially different implementations under that restriction
- **THEN** the agent gives an allowed explanatory comparison and concise question without hiding alternatives or assuming agreement

### Requirement: Safe helper failure

Clean MUST preserve the pre-pass index and working-tree content when undoing its edits. CBM MUST preserve its existing stdout/exit contract while reporting an actionable failure reason and applying the owning bounded retry/fallback policy.

#### Scenario: CBM has an active-generation conflict

- **WHEN** the CLI cannot operate and reports an active-generation conflict
- **THEN** the helper exposes an actionable stderr reason, does not call it a sandbox denial, and does not terminate unrelated sessions

### Requirement: Inherited decisions and bounded evidence

Helpers MUST consume admitted decisions covering the same scope without redundant approval, retain genuine new decisions, and verify supported behavior proportionately without substituting static prose checks for behavioral evidence.

#### Scenario: TDD receives settled behavior and interface decisions

- **WHEN** the admitted lock covers its proposed interface and test behavior
- **THEN** TDD proceeds while a materially new decision still returns to the operator

### Requirement: Independent executor admission

An explicitly selected Astra executor/coordinator MUST be admitted through authoritative available metadata separately from reviewer eligibility. No consumer MAY infer new benchmark rankings, hidden effort, or cross-family strength ordering.

#### Scenario: Astra coordinates a Full-review change

- **WHEN** Astra is explicitly selected and supported for execution
- **THEN** execution admission does not promote Astra as reviewer and the Full-review route remains independently checked

### Requirement: UI preparation and ownership

Ticket triage MAY prepare first-revision behavior evidence only after safe-start and manufactured data are verified; the required ledger and replay MUST be frozen before lock admission. Nested UI work MUST retain the admitted checkout/base and existing sanction requirements.

#### Scenario: A shipped surface has no frozen ledger

- **WHEN** safe-start and manufactured data are verified in the ticket checkout
- **THEN** triage prepares and freezes evidence before source admission without starting implementation or replacing the inherited base

### Requirement: Owned completion boundaries

A chunk MUST commit and return evidence without opening its own PR. Setup and legacy entry points MUST return through the selected ticket/review/worktree lifecycle and recommend only supported modes.

#### Scenario: A chunk completes its assigned work

- **WHEN** its verification expectation is met
- **THEN** it returns its commit and evidence to the coordinator, which owns the ticket PR

### Requirement: Audit closure without scope expansion

Implementation MUST account for every numbered finding under dispositions.md, preserve retained policy and separate issue ownership, and report bounded replay evidence and unrun checks honestly. No global reconfiguration, private skill edit, bundled-cache change, benchmark campaign, or new policy framework is authorized.

#### Scenario: A private-machine finding remains outside the public pack

- **WHEN** the pack corrections are complete but finding 26 requires separate private work
- **THEN** the ticket records that external follow-up as outstanding rather than claiming it repaired or publishing private data
