# OpenSpec and execution-lock authority

Issue: [#261](https://github.com/ConnorGriffin/skills/issues/261)

## Recommendation

Use one durable change specification and one thin execution lock:

- **OpenSpec owns the change:** motivation, scope, decisions, requirements,
  scenarios, exclusions, and implementation tasks.
- **The tracker owns live coordination:** ticket identity and relationships,
  lifecycle status, comment chronology, and pull-request links.
- **The execution lock owns authorization and delivery policy:** the exact source
  revision and selected work authorized, execution shape, worker ownership,
  assurance gates, expected diff, and the stop-at-PR boundary.
- **Repository rules own reusable process:** engineering standards, ticket
  mechanics, builder self-checks, and tool contracts.

For an OpenSpec-backed ticket, replace the current self-contained `WORK ORDER`
payload with a versioned, thin execution lock that pins the active change at a
full Git commit and selects stable task and acceptance anchors. `start` resolves
and validates that source before execution. It never silently substitutes the
branch head or a later change revision.

For a repository with another durable change-record convention, use the same lock
envelope with a pinned repository-native source. Where no durable change record
exists, use an explicit `Source: inline` mode whose payload remains today's
self-contained `Context` / `Do` / `Done when` fallback. This is one lock protocol
with two source modes, not separate OpenSpec and non-OpenSpec workflows.

The current contract already makes a fenced work order the only entry to
execution, selects the newest one, and requires enough information for a fresh
`start` session
([ticket skill, lines 142–145 and 187–189](../../skills/drivers/ticket/SKILL.md#L142)).
It also makes the active OpenSpec change reviewable through the pull request
([ticket skill, lines 278–287](../../skills/drivers/ticket/SKILL.md#L278)). The
needed conceptual change is:

> “Self-sufficient” means a fresh executor can deterministically acquire and
> verify its authorized source—not that the lock copies every durable fact.

No generated execution snapshot is warranted. A snapshot would add another
schema, generator, and equivalence check while retaining the same need to verify
the source revision.

## Current authorities and duplication

The current workflow deliberately centralizes execution authorization in a
tracker comment, but it also asks triage to create repository change records and
then repeat their substance in the work-order template.

- Ordinary OpenSpec-backed tickets carry `proposal.md`, `tasks.md`, and
  `design.md` when a decision warrants one
  ([ticket skill, lines 278–287](../../skills/drivers/ticket/SKILL.md#L278)).
- The work-order template separately requires `Context`, `Do`, and `Done when`,
  plus an outside-fence summary that translates the order
  ([work-order template, lines 11–16 and 89–111](../../skills/drivers/ticket/templates/work-order.md#L11)).
- Epic children can have a parent OpenSpec change, an untrusted issue-body draft,
  and a later fenced lock. Triage already treats the issue-body pin as intake,
  verifies it against the remote, and refuses a stale draft
  ([triage, lines 23–36](../../skills/drivers/ticket/verbs/triage.md#L23)).
- Builder guidance is copied between `start`, the work-order template, and
  write-mode `ORDER.md`; a test intentionally pins two of those copies byte for
  byte
  ([ticket tests, lines 1910–1919](../../tests/test_ticket.py#L1910),
  [orchestrate, lines 283–310](../../skills/drivers/orchestrate/SKILL.md#L283)).
- UI execution contracts already live in separate manifests or behavior
  ledgers/replays; `start` only requires the order to name and validate them
  ([start, lines 41–50](../../skills/drivers/ticket/verbs/start.md#L41)).

The duplication currently buys detached-worker safety, but a verified immutable
reference can preserve that safety without copying the specification prose.

## One authority per fact

| Fact or current field | Authority | Treatment |
|---|---|---|
| Ticket ID, title, issue body, parent/child links | Tracker state | Read live through the tracker binding. |
| Classification: `code`, `investigation`, `manual` | Tracker state | Do not repeat as specification prose. The lock kind may constrain what execution is authorized. |
| `triaged`, `in progress`, `pending review`, `done` | Tracker state | Retain current status transitions ([ticket skill, lines 178–182](../../skills/drivers/ticket/SKILL.md#L178)). |
| Pull-request URL and review conversation | Tracker state | Delivery evidence, not change intent. |
| Change identity and slug | OpenSpec | The active change directory is the durable record. |
| Motivation, durable context, scope, constraints, exclusions | OpenSpec | Proposal/design facts. Remove duplicated technical prose from the lock. |
| Decisions, risks, and settled alternatives | OpenSpec | `design.md` is the active ADR home when the change carries a decision ([charter, lines 65–69](../../profile/CHARTER.md#L65)). |
| Requirements, scenarios, observable acceptance | OpenSpec | Delta specs own behavioral truth. |
| Implementation decomposition and task completion | OpenSpec | `tasks.md` owns durable task state. |
| `Do` | OpenSpec | Replace with selected stable task IDs in the lock. |
| `Done when` | OpenSpec | Replace with selected requirement/scenario anchors in the lock. |
| Human-readable summary | Tracker state | Keep one short tracker summary; remove copied technical specification from the lock. |
| Lock protocol version and lock ID | Execution lock | Required to parse and audit authorization deterministically. |
| Source mode and full commit pin | Execution lock | `openspec`, `repository-native`, or `inline`; non-inline modes pin path plus full commit OID. |
| Selected tasks and acceptance anchors | Execution lock | Selection authorizes a bounded subset; substantive definitions stay in the pinned source. |
| `Repo(s)` | Execution lock | Names the delivery target and must agree with the pinned source. |
| Execution shape: flat/chunked | Execution lock | A delivery decision, not product intent. |
| `Open as`, `Session fit`, agent/coordinator tiers | Execution lock | Runtime admission and dispatch policy. |
| Capability, file/target, shared-contract ownership | Execution lock | Chunk isolation policy; every capability and contract has one owner ([triage, lines 186–197](../../skills/drivers/ticket/verbs/triage.md#L186)). |
| Surface lifecycle and cited UI artifacts | Execution lock | The route belongs in the lock; artifact contents remain in repository-owned manifests/ledgers. |
| Review depth and reason | Execution lock | Per-execution assurance selection. |
| Hardening profile and QA script | Execution lock | Assurance selection tied to the repository-declared command. |
| Verification command and expectation | Execution lock | Concrete execution gate ([ticket skill, lines 191–208](../../skills/drivers/ticket/SKILL.md#L191)). |
| Expected-diff allowlist | Execution lock | Closed authorization boundary. |
| No-merge / stop-at-PR boundary | Execution lock | Explicit authorization ceiling ([ticket skill, lines 184–185](../../skills/drivers/ticket/SKILL.md#L184)). |
| Branch/worktree reuse rules | Repository rules | Delivery mechanics enforced by the ticket workflow, not tracker data. |
| Builder self-check and drafting conventions | Repository rules | Reusable worker contract; reference or inject once rather than copying into every lock. |
| Comment chronology | Tracker state | The tracker supplies ordered comments. |
| Newest-valid-lock-wins selection | Repository rules | The ticket contract applies chronology and never merges older locks ([tracker contract, lines 49–57](../../skills/drivers/ticket/references/tracker-contract.md#L49)). |
| `Why sliced` | Execution lock | Delivery rationale and later slicing evidence. |
| `Launch` line | Removable duplication | Normal `/ticket start` mechanics belong in workflow documentation. |
| Repeated classification | Removable duplication | Resolve from tracker state. |
| Repeated builder self-check / drafting conventions | Removable duplication | Supply through reusable workflow rules. |
| `ORDER.md` copy | Transport copy, not authority | Preserve for compaction recovery; it must not become a second source of truth. |

## Design comparison

| Design | Benefits | Failure modes | Migration cost | Drift effect |
|---|---|---|---|---|
| Retain the self-contained work order | No migration; detached workers keep the current payload. | Issue, OpenSpec, and lock remain independently editable; revision must reconcile all three. | None | Preserves prose/schema translation drift. |
| Thin lock pinned to an OpenSpec change and commit | One durable specification; keeps explicit authorization and newest-lock semantics; can fail closed before execution. | Needs stable selection anchors and precise pin validation; omitting operational policy could under-specify execution. | Moderate | Removes duplicated change prose while retaining a small execution schema. |
| Generated immutable execution snapshot | Fully materialized frozen worker input. | Adds generator, snapshot schema, validity rules, and source/snapshot equivalence; a stale or invalid source can still generate a snapshot. | High | Replaces prose drift with generator/schema drift. |
| Separate OpenSpec and non-OpenSpec lock formats | Each convention can be optimized independently. | Two parsers and lifecycle contracts diverge; doubles migration and test surfaces. | High and ongoing | Introduces cross-format drift. |

The recommended design is the thin lock with one common envelope and explicit
source modes. It follows the repository's existing rule that OpenSpec is a worked
example rather than a universal requirement
([ticket skill, lines 278–291](../../skills/drivers/ticket/SKILL.md#L278)). It
also avoids reinstating the parallel-state pattern removed during vanilla
OpenSpec adoption
([archived adoption design, lines 62–76](../../openspec/changes/archive/2026-08-28-218-vanilla-openspec/design.md#L62)).

## Proposed execution-lock contract

Terminology:

- **Change specification:** durable repository artifact owning intent, scope,
  decisions, requirements, scenarios, exclusions, and task state.
- **Execution lock:** newest valid fenced tracker comment authorizing one bounded
  execution.
- **Source pin:** source path plus full Git commit OID.
- **Selected work:** stable task and acceptance identifiers within the pinned
  source.
- **Execution policy:** shape, tiers, ownership, UI route, review, verification,
  profile, expected diff, and PR boundary.
- **Draft:** non-authorizing tracker content, including an epic issue-body
  handoff.

Illustrative envelope—not an implementation-ready schema:

```text
EXECUTION LOCK v2 <ticket-id> <lock-id>
Source: openspec <change-path>@<full-commit-oid>
Selected tasks: <stable task identifiers>
Selected acceptance: <requirement/scenario anchors>
Execution: <single agent | chunked>
Session and dispatch policy: <current operational fields>
Verification: <command>
Expectation: <expected result>
Review/profile: <current assurance fields>
Expected diff: <closed allowlist>
Authorization: execute selected work only; open a PR; do not merge
```

`Source: repository-native` substitutes a pinned repository-native planning
artifact. `Source: inline` carries the current self-contained Context/Do/Done-when
payload for repositories with no durable source to pin.

### Fail-closed validation

Before any implementation or worker dispatch, `start` should:

1. Select the newest recognized fenced lock without merging fields from older
   comments.
2. Require exactly one recognized lock version and source mode.
3. For a pinned source, require a full commit OID, resolve that exact object, and
   require the source path at that tree.
4. For OpenSpec, require the change to be active rather than archived at the
   execution checkout, pass strict validation, and contain every selected task
   and acceptance anchor.
5. Verify the ticket branch contains the pinned source commit. Never replace the
   pin with branch head or another local branch.
6. Reject a later source amendment until a newer lock explicitly pins and
   authorizes it.
7. Reject empty selection, work outside the source, missing verification or
   expectation, overlapping parallel ownership, missing UI contracts, model
   mismatch, or repository drift.
8. Apply the current legacy-order path only to already-posted `WORK ORDER`
   comments. Any superseding lock uses the new protocol.

The current epic-child preflight already demonstrates exact remote-branch and
full-commit verification with a fail-closed stale-draft outcome
([triage, lines 23–36](../../skills/drivers/ticket/verbs/triage.md#L23)). The
new rule generalizes that pattern to every pinned change.

## Lifecycle thought experiments

| Situation | Expected behavior |
|---|---|
| Fresh `start` | Read tracker and newest lock; reuse/cut the ticket worktree; resolve the exact source commit; validate source, selection, and policy; refuse before implementation on any mismatch. |
| `revise` | Reuse the same lock and pin. Review fixes may satisfy selected work but may not expand source scope. A scope/source amendment requires a newer lock. |
| Flat execution | Dispatch one executor with the complete lock and verified source coordinates. |
| Chunked execution | The header owns the common pin and whole-ticket policy; each sub-lock owns a disjoint task subset and capability/file/contract allocation. Every worker receives a stand-alone sub-lock plus verified source coordinates. |
| Worker compaction | Keep `ORDER.md` as an uncommitted transport copy of the complete lock and dispatch instructions. If the worker cannot read the pinned source, it stops rather than continuing from memory ([orchestrate, lines 298–310](../../skills/drivers/orchestrate/SKILL.md#L298)). |
| Missing or invalid source | Missing object/path, abbreviated or mismatched OID, failed validation, or missing selected anchors refuses execution and routes to attended re-triage. |
| Amended source | A different commit is unauthorized until a newer lock pins it. |
| Archived source | A new `start` cannot execute an archived change. During an already-open PR, `revise` remains valid only while the active pinned source is available under the current pre-merge rule. |
| Worktree reuse | Require the expected ticket branch and require it to contain the pinned source commit. A different ticket branch or unrelated source refuses. |
| Post-merge archive | Preserve current behavior: keep the normal-ticket change active through review, then archive only after verified human merge ([ticket tests, lines 619–655](../../tests/test_ticket.py#L619)). |
| Epic child | The parent change stays authoritative. The issue-body parent-plan pin remains untrusted intake; the posted lock becomes authorization for the selected parent-plan work. |
| Investigation | Prefer an explicit read-only investigation lock if model dispatch or bounded source access needs authorization; otherwise tracker issue plus findings can be sufficient. Never imply write authorization. |
| Manual ticket | No agent execution lock. Tracker state owns the human handoff. |
| Hardening | Keep the hardening profile, command, QA script, and residue policy in the execution lock. |
| Legacy work order | Parse under existing sufficiency rules. Do not infer a source pin. A supersession or scope amendment migrates to the new lock. The existing surface-lifecycle compatibility path is precedent ([start, lines 41–50](../../skills/drivers/ticket/verbs/start.md#L41)). |
| Repository-native change record | Pin its authoritative path and commit through the common envelope. |
| No durable change record | Use `Source: inline` and retain the current self-contained payload. |

## Worker payload boundary

Copy directly into an isolated worker prompt:

- the complete execution lock or stand-alone chunk sub-lock;
- exact worktree, branch, and graph identity;
- source pin and the coordinator's statement that it was verified;
- selected task and acceptance identifiers;
- verification command and expected output;
- expected-diff allowlist and chunk ownership boundaries;
- UI route, review/profile policy, and no-merge authorization ceiling;
- ephemeral verified facts that are not available in the repository, such as a
  safe-fixture constraint or live-state probe result.

Reference from the verified checkout rather than copy:

- OpenSpec proposal, design, delta specs, and tasks;
- repository-native planning documents;
- UI manifests, behavior ledgers, and replays;
- repository rules, code, and tests.

The worker must stop when it cannot read the pinned source. Do not generate a
second snapshot merely to make the prompt self-contained.

## Migration

1. Define stable task and acceptance identifiers before changing the lock
   template. Markdown list positions and mutable heading text are not sufficient
   identifiers.
2. Add a versioned lock parser/recognition rule while retaining the legacy
   `WORK ORDER` locator.
3. Teach triage to create and validate the OpenSpec change first, commit it, then
   post a lock pinned to that full commit.
4. Teach `start` and `revise` to resolve and validate the source before admitting
   execution.
5. Preserve legacy self-contained orders until a documented sunset condition.
   Do not retrofit pins into posted comments.
6. Migrate chunk prompts to selected task/acceptance IDs while keeping execution
   ownership in each stand-alone sub-lock.
7. Update docs and tests, then use a later implementation ticket to settle the
   attended decisions below.

## Evidence-supported implementation blast radius

Specifications:

- `openspec/specs/ticket-workflow/spec.md`
- `openspec/specs/planning-and-review/spec.md`

Ticket and orchestration skills:

- `skills/drivers/ticket/SKILL.md`
- `skills/drivers/ticket/verbs/triage.md`
- `skills/drivers/ticket/verbs/start.md`
- `skills/drivers/ticket/verbs/revise.md`
- `skills/drivers/ticket/verbs/finalize.md`
- `skills/drivers/ticket/templates/work-order.md`
- `skills/drivers/ticket/references/tracker-contract.md`
- `skills/drivers/ticket/bindings/github-issues.md`
- `skills/drivers/ticket/references/coordinator-mode.md`
- `skills/drivers/ticket/references/slicing.md`
- `skills/drivers/ticket/references/drafting-conventions.md`
- `skills/drivers/orchestrate/SKILL.md`, especially durable `ORDER.md` transport
- `skills/drivers/epic/SKILL.md` for epic-child handoff wording

Tests and documentation:

- `tests/test_ticket.py`: lock location, template, session fit, source pin,
  epic-child, active-change/archive, legacy-order, and chunk ownership contracts
- `tests/test_behavior.py`: durable worker-order and delegation contracts
- `docs/epic-flow.md`

No evidence supports changing unrelated OpenSpec adoption tooling, UI Craft
implementation behavior, CI path selection, or archived history merely to create
this seam.

## Rejected alternatives

- **Two full authorities:** retains the exact translation/drift problem under
  investigation.
- **OpenSpec as execution authorization:** OpenSpec cannot own tracker chronology,
  human authorization, session fit, worker allocation, verification, or the
  stop-at-PR boundary.
- **Generated execution snapshot:** adds a second schema and equivalence problem
  without removing source validation.
- **Separate OpenSpec/non-OpenSpec lock protocols:** unnecessarily doubles parser,
  lifecycle, test, and documentation surfaces. One envelope with explicit source
  modes covers both.
- **Issue body as execution authority:** conflicts with the existing epic-child
  rule that the issue-body draft is untrusted and non-executable
  ([triage, lines 150–166](../../skills/drivers/ticket/verbs/triage.md#L150)).

## Decisions still requiring attended settlement

1. What stable identifier syntax will OpenSpec tasks, requirements, and scenarios
   expose? This is the main prerequisite for a thin lock.
2. What does a checked `tasks.md` item mean: planned, authorized, or implemented?
3. May an ordinary lock select a bounded subset of a shared active change, or must
   every ordinary ticket own its own change?
4. Must every source amendment require a newer lock, including review-driven
   clarification during `revise`? The recommendation is yes.
5. How long must pinned commits remain reachable after merge/archive for revise,
   audit, and recovery?
6. Should investigations always use an explicit read-only lock, or only when they
   dispatch a bounded worker?
7. Should strict OpenSpec validation run at both triage and `start`, or at triage
   plus pre-PR? The recommendation is both triage and `start`, so stale/invalid
   source fails before code changes.
8. What event sunsets legacy self-contained work orders?
9. Can expected-diff ownership be derived from selected tasks without weakening
   its closed-allowlist guarantee? Until proven, keep it explicit.

These choices affect the executable contract and should be settled before a build
ticket is admitted. They do not change the research conclusion: durable change
facts belong in one repository authority, while a tracker lock authorizes a pinned
selection and its delivery policy.
