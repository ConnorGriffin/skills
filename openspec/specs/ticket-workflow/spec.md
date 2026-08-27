# Ticket workflow

How one tracked ticket moves from arrival to resolution.

## Behavior

* Four verbs, one at a time: `triage` reads the ticket and repo and posts a
  locked work order as a ticket comment (interviewing through `/scope` when
  scope is thin); `start` executes the order in a fresh session on an
  isolated worktree and opens the PR; `revise` actions one review round;
  `finalize` runs after a human merges — closes the ticket, tears the
  worktree down, and records what the ticket cost.
* Literal invocation of `triage`, `start`, or `revise` requests the work order or
  task prompt plus only the repository code and documentation needed for every
  mandatory dispatch the verb routes, including nested review and nested
  Orchestrate work. A Codex UI parent admits OpenAI Codex; a Claude Code parent
  admits OpenAI Codex or Anthropic Claude under existing routing. Credentials,
  secrets, patient data, `.env`, and real database contents are excluded.
  Automatic activation outside an invoked parent asks once before its first
  external dispatch with the same terms. `finalize` grants no worker-egress
  consent.
* Work orders too big for one context are sliced at triage into sub-orders in
  the same comment. Chunks are never issues. The slicing rubric targets a
  projected peak under 180k tokens per chunk, folds chunks that would peak
  under 120k into a neighbour, and treats more than four chunks as a sign the
  ticket is really a larger effort. On a chunked order, `start` coordinates
  one agent per chunk per the coordinator-mode reference, which binds
  `/orchestrate`'s delegation rules.
* Status moves through `ticket:<state>` labels via the GitHub issues binding;
  agents never merge.
* Telemetry: sessions claim tickets as they work (`ticket.py claim`), and
  `finalize` runs `ticket.py record`, appending verdict, role-tagged peaks,
  chunk count, rubric traits, and repo to `~/.config/ticket/telemetry.jsonl`.
  `scan` and `record` accept `--project` to resolve the target repository when
  they run outside its worktree. Every record carries counts and labels supplied
  on the command line, never prose from a session. A `no-data` or
  `unmeasurable` verdict appends nothing: the latter names claims for this
  repository that supplied no usable peak. A denied write is reported in one
  visible line and never blocks the verb.
* On a misprediction verdict, `finalize` drafts an amendment against the
  slicing rubric and shows it to the user; prose and the helper's constants
  move together.

## Invariants

* No work order, no `start`: the verb refuses rather than inventing scope.
* A session never runs an order stamped for a stronger model tier than its
  own, and never re-slices in flight.
* Bounded worker-egress consent covers every mandatory nested dispatch routed by
  an invoked verb, but does not replace generic delegation authority, change an
  adapter's isolation, override platform approval policy, or filter prompt bytes.

## Dependents

The review workflow's depth stamps and the slicing rubric's calibration both
read this telemetry; the pending epic-rework change re-homes the amendment
path.
