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
- Durable close ordering follows tracker truth. For a research spike: the
  `## Findings` comment lands; the home session verifies it; the spike issue
  closes; then the home session derives its `Spikes` and `Decisions` ledger
  lines, updates Status, commits with DCO sign-off, and pushes the standing
  planning branch. For the epic: the direct tracker completion checks pass;
  the home session syncs the final ledger and archives the OpenSpec change in a
  signed, pushed commit; only then does the planning pull request leave draft;
  a human merges it; the home session verifies the merge, closes the epic issue,
  and tears down the planning worktree. — `inline`

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
  bootstrap, native child issues, native blocked-by edges, direct tracker
  completion checks, and both durable close sequences; bounded zero-hit checks
  for the three gate terms and the enumerated superseded protocol identifiers.

Why: this skill is inherited process machinery whose tracker instructions can
mutate durable issue state.

Disposition: admitted into issue #142's work order.

## Open questions

- When a deferred `build` child is closed as won't-do, must it also leave the
  closing epic's native child set, or does the completion predicate admit a
  closed won't-do build without a merged pull request?
- How does a research spike produce the authoritative `## Findings` GitHub
  comment while the existing `$research` interface requires a Markdown file in
  the repository and only the epic ledger may ride the standing planning pull
  request?
- Must the first epic normalize its declared child relationships and standing
  ledger before issue #142 executes? Live grounding found issues #143 through
  #147 declare themselves children of #133 but have no native parent; the
  standing ledger uses non-normative Build states and puts instructions in
  Notes.

## Spawned tasks

- Cold executor, rule-corpus, and ceremony-skeptic review passes completed in
  this triage session; their verified blocking conditions are folded into the
  revised work order.
- Three review panels reached the mandatory cap. The final panel's remaining
  blockers are the three decisions above plus an executable spike for the
  direct GitHub completion predicates; drafting is stopped until `/scope`
  resolves them.
