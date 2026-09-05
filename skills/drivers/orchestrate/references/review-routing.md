# Reviewer routing

## Reviewer selection contract

This reference is the sole live authority for reviewer classification, reviewer
eligibility, and reviewer-model precedence. The benchmark authority remains
[`routing-table.md`](routing-table.md).

For a review with a work order, effective review depth is the routing input:
Focused and Targeted are routine; Full is load-bearing. An order with no stamped
depth retains [review-depth.md](../../ticket/references/review-depth.md)'s Targeted
default.

For every review without a work order—a bare diff, chat plan, file-backed PRD, design document, or GitHub issue—the dispatcher judges the subject against [review-depth.md](../../ticket/references/review-depth.md)'s sensitivity floor: any of its four categories makes the subject load-bearing; otherwise it is routine.

Precedence is fixed: effective depth, or the judged sensitivity floor when there
is no order, produces routine/load-bearing routing stakes; the selected review
skill supplies its routing-table area; `routing-table.md` supplies that row's
candidate model or ladder; parent policy and the Codex presence/headroom gate
remove unavailable candidates. Builder tier is never an input, and a fallback is
never borrowed from another row.

Haiku never reviews.

Reviewer-routing stakes and plan-review's plan stakes tier are independent.
Neither derives from, overrides, or rewrites the other.

An explicit Astra executor/coordinator admission is not reviewer evidence. It
does not alter this matrix, the Full-review route, or headroom handling. When the
selected review route cannot run, report it as unresolved; never promote Astra or
silently downgrade the review.

| Review skill | Routing stakes | Initial route |
|---|---|---|
| code-review | routine | Run the Codex presence/headroom gate first. With usable Codex, use Luna from the Code review row. On absent, unknown, ≤5%, or rate-limited Codex, enter Claude-only mode at Sonnet from the Code review row and make no second Codex attempt for the session. |
| code-review | load-bearing | Use Opus directly from the Code review row; select no Codex rung. |
| plan-review | routine | Run the Codex presence/headroom gate first. With usable Codex, use Terra from the Plan / spec writing row. On absent, unknown, ≤5%, or rate-limited Codex, enter Claude-only mode at Opus from the Plan / spec writing row, which has no Sonnet rung, and make no second Codex attempt for the session. |
| plan-review | load-bearing | Use Opus directly from the Plan / spec writing row; select no Codex rung. |

For a Codex UI parent, routine `code-review` uses Luna and routine `plan-review`
uses Terra, subject to the same presence/headroom gate. Load-bearing review has
no benchmark-validated Codex route. When the operator explicitly directs the
workflow to use Codex anyway, honor that product choice with Luna for
`code-review` or Terra for `plan-review`, label the review **unvalidated**, and
retain the ordinary same-session retry cap. An explicit choice does not promote
the route or alter the benchmark table.

Rendered evidence does not change these stakes. Before admitting a Codex
reviewer, verify that the selected model accepts image input and attach every
required render through `codex-worker.py --image`; a filename in the prompt is
not an attachment. If the images are unavailable, report an evidence-transport
blocker instead of a model-capability blocker.

Opus in the Plan / spec writing ladder is an availability rung, not a benchmarked
plan-writing win.

The matrix chooses only the initial reviewer adapter/model. Existing read-only
sandboxing, explicit effort, same-session retry, escalation, liveness, recovery,
and worker-state mechanics remain owned by orchestrate and the merged #145, #149,
#150, #151, and #152 work.

## Related authorities

Use `routing-table.md` for benchmarked areas, ladders, scores, and effort notes;
use `review-depth.md` for depth, sensitivity, hardening, blocking, and whole-diff
behavior.
