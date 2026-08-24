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
- A deferred build closed as won't-do stays a native child of its epic and
  keeps its `build` type so the epic retains the history of work it declined.
  The closing session posts the specific reason, closes the issue with GitHub's
  `NOT_PLANNED` state reason, and removes `deferred`. The build completion
  predicate therefore accepts either a merged closing pull request or a closed
  `NOT_PLANNED` build. — `inline`
- A research worker uses `$research` unchanged in a temporary per-spike
  worktree and returns its Markdown findings file. The home session posts that
  content to the spike under the exact `## Findings` heading, verifies the
  comment, then removes the temporary worktree and its unshipped file. The
  standing planning pull request still carries only the epic ledger. — `inline`
- The first epic adopts the native tracker and normative-ledger contract before
  issue #142 executes. Live verification on 2026-08-24 found every declared
  child attached to #133 and PR #136 at `43cad55`, with pointer-only Notes and
  the closed Builds grammar. — `inline`
- The direct completion-read spike is grounded in GitHub CLI 2.97.0's actual
  shapes: `subIssues.nodes` enumerates children; each child's labels, state,
  state reason, and closing pull-request references determine its branch; each
  referenced pull request's `mergedAt` determines merge truth. Its fixtures pass
  merged and `NOT_PLANNED` builds and reject open spikes, incomplete builds, and
  open deferred children. Against live #133 it correctly fails on #140, builds
  #139/#142–#147, and deferred #147. — `inline`

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

- None.

## Spawned tasks

- Cold executor, rule-corpus, and ceremony-skeptic review passes completed in
  this triage session; their verified blocking conditions are folded into the
  revised work order.
- Three review panels reached the mandatory cap. The final panel's remaining
  blockers were routed through `/scope`. The user settled all three decisions,
  the epic home session normalized live tracker and ledger state, and the direct
  GitHub completion predicates passed their fixture spike and failed on the
  expected live open work.
