# Mode: consensus

Settle a contested visual-design decision with a fixed panel of 3 product-derived AI reviewer personas. The panel votes independently, negotiates vetoes and trade-offs, and surfaces the recommendation to you. **The panel is advisory — you always have final say.**

Use this when a design question has real trade-offs between user situations (accessibility vs. density, discoverability vs. minimalism, mobile vs. desktop) and different user situations genuinely want different answers. Do not use for trivial tweaks or unanimous positions.

## Preconditions

- Personas must be repo-specific at `.claude/qa/personas/<name>.md` — one file per persona with lens, job, and rules, plus the declared tie-break ranking in `.claude/qa/personas/RANKING.md`. **If personas are missing or generic archetypes only, STOP and run persona-init (reference/init.md) first.** Never run the panel on untuned personas.
- Panel size is exactly 3.
- Personas are spawned as cheap sub-agents (Haiku); reuse and resume (SendMessage) when history matters. They judge **rendered screenshots only** — never source code.

## Step 1: Fixture coverage

Enumerate every content dimension the question touches (fractions, long names, empty states, worst-case string lengths). **If the current fixture doesn't exercise one, patch it or build a test copy with edge content injected before round 1.** A fixture gap found late forces rework; catch it now.

## Step 2: Neutral framing

Pose the question with all options argued evenly. **Never reveal your lean, the orchestrator's lean, or the originating comment.** Force commitment: "no fence-sitting; verdict line at top." Provide rendered screenshots of both candidates.

## Step 3: Independent votes

Spawn all 3 personas in parallel; they must not see each other's output. Tally votes. **Unanimity ends the panel — go to Step 6.** The orchestrator (you) gives its take only *after* votes, from its own screenshots — never before (no anchoring).

## Step 4: Confirmation pass (split vote only)

When building a hybrid, send each persona a head-to-head: hybrid vs. their own previous winner. They must **ACCEPT** or name a **CONCRETE LOSS** — vague preference restatements don't count.

## Step 5: Negotiation rounds (hard cap: 3)

- **Round 1:** show each persona the other two's positions; each proposes one concrete spec delta per element/text role.
- **Round 2:** enumerate remaining open axes as explicit packages (P1…Pn); each picks one ACCEPT plus any vetoes.
- **Round 3:** audit vetoes for stale premises — personas sometimes defend positions another has abandoned. Correct the record (quote the persona's own prior words) and re-ask only the holdout. A late-round holdout may escalate to a stronger model.

**Two guards:** (a) "correct facts, don't argue taste" — factual corrections must cite rendered evidence (screenshot or measurable property), never bare assertion; (b) ties resolve by declared persona ranking. If ranking is genuinely uncertain for this question, escalate to the user and write their answer into persona files. **Still split after round 3 → the panel is HUNG:** bring the split to the user with each side's best case. Never loop past the cap.

## Step 6: Build and verify rendered

Implement the agreed spec as a new mockup variant, screenshot it, show the user. If Step 1 missed a content dimension, run the edge-content check now (throwaway copy with edge cases, one panel look).

## Step 7: Record

Write a snapshot to `.impeccable/consensus/<timestamp>__<slug>.md`: the question, votes per round, packages/vetoes, final spec, and hung/settled status. Surface the verdict via the critique widget where applicable, marked "(recommended, panel N-0)" — the user always picks.
