# Scope ledger — ticket 239 triage authority boundary

## Decisions

- Triage may read broadly but ancillary repository and tracker mutations stay
  inside the selected ticket unless the operator explicitly approves the exact
  disclosed target and mutation. Why: PR #237 shows that an inferred prerequisite
  can otherwise expand and interrupt the selected ticket. `→ ADR`
- The boundary preserves ticket claims and exact-worktree Codebase Memory state.
  Why: those local writes are required mechanics of the selected ticket lifecycle,
  not ancillary repository or tracker work. `inline`
- A parent amendment is prerequisite only when omitting it would contradict a
  recorded destination, constraint, acceptance criterion, risk, or sequence; the
  request cites that clause. Why: a visible artifact predicate prevents the triager
  from expanding scope by private judgment. `→ ADR`
- The selected-ticket write boundary preserves the current Epic-child lifecycle:
  the child creates no per-child change record, but a required amendment to the
  parent's active plan may travel in the selected child's worktree and implementation
  pull request. Why: PR #249 made that parent-owned amendment path the governing
  contract after the first issue-239 scope was written. `→ ADR`

### Risk contract

- **Must prevent:** unapproved ancillary repository or tracker work; silently
  stamping an order that contradicts governing recorded scope; secret exposure,
  irreversible loss of authoritative data, and silent incorrect success.
- **Must recover:** none automatically.
- **Accepted failure:** a true external prerequisite stops triage before mutation
  and leaves the selected ticket untriaged until the operator responds.
- **Unsupported:** automatic parent repair, cleanup of PR #237 or its branch, a
  general authorization engine, and runtime parsing or enforcement of the prose
  contract.
- **Evidence owed:** public-contract tests for the continuation, prerequisite,
  explicit-authorization, telemetry, and Codebase Memory paths; full repository and
  strict OpenSpec validation.
- **Why:** this admits a narrow authority fix without replacing prose workflow with
  enforcement machinery.
- **Disposition:** copied into the issue-239 work order.

## Open questions

None.

## Re-triage after main advanced

- `origin/main` at `7d4cdd6` contains merged PR #249, which replaced the former
  work-order-only child branch rule with a parent-owned amendment carried by the
  selected child's implementation pull request.
- The former issue-239 decision that a child branch carries no parent planning
  artifact is superseded. The authority boundary now distinguishes selected-ticket
  lifecycle state from ancillary state, rather than distinguishing child planning
  files from all other child-branch files.
- No human decision remains: recorded current-main scope governs, and issue 239 must
  integrate with it.

## Spawned tasks

None.

## Start execution evidence

- Chunk 1 reconciled the ticket branch with current `origin/main` while preserving
  the pinned-parent-plan handoff, one executable child lock, parent change and
  archive ownership, and child-carried required amendment. The ticket-focused suite
  passed 87 tests before integration.
- Chunk 2 added the shared closed allowance, the triage consumer, and one aggregate
  public-contract test. The test failed first against reconciled current-main text
  for the missing authority boundary and passed after the two live contract files
  changed.
- The integrated contract remains prose-only: no parser, state machine, tracker
  operation, automatic repair, or runtime authorization enforcement was added.
- Strict OpenSpec validation passed all four discovered items. Structural validation
  covered 27 skills and 401 files; the documented unittest selection passed 472
  tests with 23 skips; Python compilation completed silently.
- Each chunk received the required Full-depth review through the operator-selected,
  unvalidated GPT-5.6-Sol exception. Chunk 1 checked 13 Standards and 15 Spec items;
  chunk 2 checked 15 Standards and 20 Spec/risk/evidence items. All verdicts were
  clean, and coordinator verification reproduced the required evidence.

## Original review rounds

### Round 1

- `authoring` — the verification command omitted the host's Python 3.10+
  substitution. Resolved by recording the required Python 3.14 path separately.
- `authoring` — the change-record evidence proved a commit but not branch containment
  or strict validity. Resolved with current-branch, commit-containment, and strict
  validation output.
- Injected blockers: none.

### Round 2

- `authoring` — the inventory evidence used nondeterministic traversal order.
  Resolved by sorting the command output and regenerating it verbatim.
- `authoring` — the first authority boundary swept in required ticket claims and
  Codebase Memory state. Resolved by limiting the rule to ancillary repository and
  tracker work and preserving ticket-scoped local lifecycle state.
- `authoring` — "safe to carry" and "genuinely required" were private judgments.
  Resolved with the recorded-conflict predicate and exact-target disclosure rule.
- Injected blockers: none.

### Round 3

- `authoring` — the selected-ticket active-change allowance did not say it applied
  only to ordinary tickets, contradicting the Epic-child work-order-only rule.
  `/scope` found no open decision: the existing Epic-child exception governed.
  Resolved by stating the ordinary-ticket limit and preserving parent ownership.
- Injected blockers: none.

The three-panel hard cap was reached with the authoring blocker above. No work order
could be posted from that review cycle. After the blocker was resolved and committed,
the operator directed triage to keep going; the clean rewritten draft entered a new
fresh review cycle.

## Original review cycle 2

The cycle started from commit `c1d3554`, with every blocker from the first cycle
resolved in the active change and work order.

### Round 1

- Refuted before authoring: the worker claimed its own already-approved successful
  dispatch lacked authorization. The running isolated session and the operator's
  explicit approval disproved the claim; it did not travel into the draft.
- `authoring` — the regression-test instruction replaced the existing triage-only
  assertion but did not require one assertion surface spanning the shared ticket
  pipeline and triage procedure. Resolved by requiring the public-contract test to
  aggregate both files and reject the old instruction across the combined text.
- Injected blockers: none.
- The same reviewer reproduced the correction and returned `COUNTERSIGNED`.

### Round 2

- A context-free fresh cold pass returned no blocking objections.
- Injected blockers: none.
- Verdict: `COUNTERSIGNED`.

## Re-triage review cycle

### Round 1

- `authoring` — the first sub-order used the nonexistent `serial after 0` mode.
  Resolved with the schema's initial `parallel` mode and `serial after 1` successor.
- `authoring` — Done-when pinned an OpenSpec item count despite refreshing moving
  `main`. Resolved by requiring every discovered item to pass with zero failures.
- `injected` — the first correction left the slicing rationale saying `two serial
  chunks`. Resolved by naming the initial predecessor and serial successor exactly.
- Injected blockers after correction: none.
- Same-reviewer verdict: `COUNTERSIGNED`.

### Round 2

- Refuted before authoring: the reviewer treated initial `Mode: parallel` as
  concurrent execution. The slicing schema offers only `parallel` for a chunk with
  no predecessor and `serial after <n>` for a real dependency; there is no chunk 0.
  The order now also states that sub-order 1 runs alone and sub-order 2 is cut only
  after it merges.
- `authoring` — the authorization response did not explicitly repeat approval of
  the previously disclosed target and mutation. Resolved in the risk contract,
  test obligation, triage instruction, and acceptance criteria.
- `authoring` — selected-ticket lifecycle work was not a reviewer-decidable closed
  set. Resolved with the exact allowed artifact list; anything else is external.
- `authoring` — the generic confinement self-check could be misread to require a
  real external mutation despite the admitted prose-only assurance level. Resolved
  by defining the aggregate public-contract test as the real run and forbidding
  external proof mutations.
- Injected blockers: none.

### Round 3

- `authoring` — sub-order 1 told its worker to merge upstream into the
  coordinator-owned ticket branch. Resolved by merging upstream into the chunk
  branch and returning the reviewed reconciliation for the coordinator to merge.
- `authoring` — the inventory step said `Repeat`, leaving protected records'
  write status ambiguous. Resolved by making it a read-only verification and
  assigning active-change edits only to the coordinator.
- `authoring` — the closed allowance omitted the control checkout's local
  remote-tracking-ref refresh required to verify an Epic child's pinned base before
  its worktree exists. Resolved by admitting only that local synchronization and
  stating that it creates no remote repository or tracker state.
- Injected blockers: none.
- The three-panel cap routed back through `/scope`. No human decision was open:
  current coordinator ownership and Epic-child pre-worktree rules settled all three
  corrections. The clean rewritten draft therefore started a new review cycle.

## Re-triage review cycle 2

The cycle started from the rewritten draft that resolved every reproduced blocker
above. A fresh cold pass received no prior findings.

### Round 1

- A context-free fresh cold pass returned no blocking objections.
- The reviewer reproduced the branch facts, PR #237 and PR #249 grounding, strict
  OpenSpec validation, and the need for reconciliation; F1 matched byte-for-byte.
- Injected blockers: none.
- Verdict: `COUNTERSIGNED` (unvalidated Codex exception selected by the invoked
  ticket workflow).
