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
- The boundary is semantic rather than an exhaustive artifact list: required
  operator-local workflow state and selected-ticket artifacts may be written,
  while state for a distinct external concern still requires exact disclosure and
  a subsequent authorization. Why: merged reviewer-memory support added a valid
  local triage write after the prior list was locked, reproducing the same omission
  pattern already seen with remote-tracking refs. `→ ADR`

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
- **Evidence owed:** public-contract tests for required operator-local workflow
  state, selected-ticket artifacts, the continuation, prerequisite, and
  explicit-authorization paths; full repository and strict OpenSpec validation.
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

## Re-triage after reviewer memory landed

- `origin/main` at `ecb7c0e` made reviewer-memory initialization and reading a
  required triage step. The issue-239 branch already contains that merge, and the
  current closed list omits the store even though the selected lifecycle requires
  it.
- `origin/main` then advanced through `d780ab9` to `5372dda`. A real merge
  simulation against the current tip completed without conflicts, so the branch
  and its planning records remain reusable.
- The previous exhaustive artifact list is superseded by a stable distinction:
  required operator-local workflow state and state belonging to the selected
  ticket lifecycle are allowed; creating or mutating state for a separate concern
  remains external and requires exact disclosure plus a subsequent explicit
  authorization.
- No human decision remains. Adding only `reviewer-memory` to the list would retain
  the omission defect and fail again when another legitimate local lifecycle
  mechanism lands.

## Spawned tasks

None.

## Start execution evidence

- Chunk 1 reconciled the ticket branch with current `origin/main` while preserving
  the pinned-parent-plan handoff, one executable child lock, parent change and
  archive ownership, and child-carried required amendment. After one reproduced
  current-main drift correction, the ticket-focused suite passed 325 tests with one
  skip before integration.
- Chunk 2 added the shared ownership-and-purpose boundary, the triage consumer, and
  one aggregate public-contract test. The test failed first against reconciled
  current-main text for the missing authority boundary and passed after the two live
  contract files changed. The deterministic inventory matched all 29 assigned paths.
- The integrated contract remains prose-only: no parser, state machine, tracker
  operation, automatic repair, or runtime authorization enforcement was added.
- Strict OpenSpec validation passed all four discovered items. Structural validation
  covered 28 skills and 420 files; the documented unittest selection passed 485
  tests with 23 skips; Python compilation completed silently.
- Each chunk received the required Full-depth review through the operator-selected,
  unvalidated Codex exception, routed to GPT-5.6-Luna by the review matrix. Chunk 1's
  first round checked 12 Standards items and 10 Spec/risk items, found one moving-main
  drift, then converged after correction on 14 Standards items and 12 Spec/risk/fix
  items. Chunk 2 checked 15 Standards items and 16 Spec/risk/evidence items with no
  findings. Coordinator verification reproduced the required executable evidence.
- The whole-diff Full review ran after the final current-main refresh. Its first round
  requested that the scope ledger carry the deterministic inventory and executable
  commands behind the summarized evidence; those reproducible facts follow.
- The final inventory contains 32 paths: the original 29 plus the current-main
  issue-259 scope ledger and two archived OpenSpec records. Those three upstream
  records are protected grounding/history, not issue-239 edit authority.

### Reproducible final evidence

Closed inventory command:

```sh
rg -l -i 'selected-ticket|selected ticket|ancillary|parent-plan amendment|reviewer-memory|exact-worktree Codebase Memory|lifecycle claim' . | sort
```

Complete output (32 paths):

```text
./AGENTS.md
./README.md
./docs/epic-flow.md
./docs/scope/195-retire-agentflow-premise.md
./docs/scope/239-triage-authority-boundary.md
./docs/scope/259-remove-unused-ticket-telemetry.md
./docs/scope/reviewer-memory.md
./openspec/changes/239-triage-authority-boundary/design.md
./openspec/changes/239-triage-authority-boundary/proposal.md
./openspec/changes/239-triage-authority-boundary/specs/ticket-workflow/spec.md
./openspec/changes/239-triage-authority-boundary/tasks.md
./openspec/changes/archive/2026-08-28-241-epic-human-dispatch-slicing/proposal.md
./openspec/changes/archive/2026-08-28-241-epic-human-dispatch-slicing/specs/planning-and-review/spec.md
./openspec/changes/archive/2026-08-28-241-epic-human-dispatch-slicing/specs/ticket-workflow/spec.md
./openspec/changes/archive/2026-08-29-259-remove-unused-ticket-telemetry/proposal.md
./openspec/changes/archive/2026-08-29-259-remove-unused-ticket-telemetry/specs/ticket-workflow/spec.md
./openspec/specs/planning-and-review/spec.md
./openspec/specs/ticket-workflow/spec.md
./scripts/validate.py
./site/relationships.py
./skills/drivers/epic/SKILL.md
./skills/drivers/ticket/SKILL.md
./skills/drivers/ticket/verbs/finalize.md
./skills/drivers/ticket/verbs/triage.md
./skills/tools/code-review/SKILL.md
./skills/tools/plan-review/SKILL.md
./skills/tools/reviewer-memory/SKILL.md
./skills/tools/reviewer-memory/agents/openai.yaml
./skills/tools/reviewer-memory/scripts/memory.py
./tests/test_behavior.py
./tests/test_reviewer_memory.py
./tests/test_ticket.py
```

Final verification commands, run from the ticket worktree after merging current
`origin/main`:

```sh
openspec validate --all --strict
/opt/homebrew/bin/python3.14 scripts/validate.py
/opt/homebrew/bin/python3.14 -m unittest tests.test_behavior tests.test_pr_body tests.test_pr_body_gate tests.test_pr_body_bench tests.test_ticket tests.test_reviewer_memory tests.test_codebase_memory_install tests.test_check_dco tests.test_ci_changed_paths tests.test_site_build
/opt/homebrew/bin/python3.14 -m py_compile skills/tools/codebase-memory/scripts/install.py skills/tools/reviewer-memory/scripts/memory.py scripts/ci_changed_paths.py skills/drivers/orchestrate/scripts/worker_lifecycle.py skills/drivers/orchestrate/scripts/codex-worker.py skills/drivers/orchestrate/scripts/claude-worker.py
```

Observed result:

```text
OpenSpec: 4 passed, 0 failed
Structural validation: validated 28 skills and 420 files
Unittest selection: Ran 485 tests; OK (skipped=23)
py_compile: exit 0; no output
```

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

## Re-triage after reviewer memory — review cycle 1

### Round 1

- `authoring` — the verification command was flattened instead of preserving the
  repository fact's required line breaks and continuation indentation. Resolved by
  transcribing the `AGENTS.md` test literal exactly and retaining host substitution
  as a separate line.
- Additional perspective reads found no blockers.
- Injected blockers: none.

### Round 2

- `authoring` — whole-ticket acceptance required fail-first evidence against the
  rejected exhaustive implementation even though the serial execution order removes
  it before creating the replacement test. Resolved by requiring failure against
  restored current-main text, matching sub-order 2.
- Injected blockers: none.

### Round 3

- `authoring` — the order required a closed inventory but named only categories,
  leaving the executing worker to discover authority, consumer, and protected-
  history roles. The three-round cap returned through `/scope`; the repo already
  settled every role, so no operator decision was open. Resolved by regenerating a
  deterministic 29-path inventory and assigning every path a mutability role.
- Injected blockers: none.

## Re-triage after reviewer memory — review cycle 2

### Round 1

- A context-free fresh cold pass reproduced the branch and inventory evidence and
  returned no blocking objections.
- Injected blockers: none.
- Verdict: `COUNTERSIGNED` (unvalidated Codex exception selected by the invoked
  ticket workflow).
