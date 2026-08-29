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

## Spawned tasks

None.

## Review rounds

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
