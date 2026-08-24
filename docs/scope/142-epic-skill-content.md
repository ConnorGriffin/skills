# Scope ledger — issue 142 epic skill content

## Decisions

- A deferred child receives its `spike` or `build` type label when it is filed,
  then also receives `deferred`. This is the narrow exception for a deferred
  child the epic files: ordinary build tickets still receive `build` from ticket
  triage. The parent proposal's orphan-control section already requires "a type
  label plus `deferred`"; this is clarification of the existing rule, not a
  proposal amendment. — `inline`
- A research spike's terminal result comment starts with the exact heading
  `## Findings`. The home session verifies that mechanically before marking the
  spike resolved. GitHub remains authoritative; the epic ledger records only the
  derived one-line state and never the comment URL. This standardizes the
  convention after issue #140 used `## Spike findings`. — `inline`

### Risk contract

- **Must prevent:** secret exposure; irreversible loss of authoritative tracker
  data; silent incorrect success from instructions that appear to complete an
  epic while tracker state or the epic ledger still shows unresolved work.
- **Must recover:** nothing automatically. Tracker or Git failures stop visibly
  for the operator; the epic ledger and live GitHub state provide manual recovery
  points.
- **Accepted failure:** a build session may die mid-run and resume from its work
  order and worktree; epic-ledger staleness is visible and corrected manually
  from tracker state.
- **Unsupported:** trackers other than GitHub Issues; concurrent epics sharing
  one OpenSpec change directory.
- **Evidence owed:** validator and the full enumerated suite green; behavior pins
  for the normative epic ledger, planning-PR lifecycle, bounded filing rules,
  exact `## Findings` verification, deferred close-out mutations, four-label
  bootstrap, native child issues, native blocked-by edges, and direct tracker
  completion checks; bounded zero-hit checks for the three gate terms and the
  enumerated superseded protocol identifiers.

Why: this skill is inherited process machinery whose tracker instructions can
mutate durable issue state.

Disposition: admitted into issue #142's work order.

## Open questions

- None.

## Spawned tasks

- Cold executor, rule-corpus, and ceremony-skeptic review passes completed in
  this triage session; their verified blocking conditions are folded into the
  revised work order.
