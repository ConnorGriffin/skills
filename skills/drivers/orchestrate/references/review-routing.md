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

| Review skill | Routing stakes | Initial route |
|---|---|---|
| code-review | routine | Run the Codex presence/headroom gate first. With usable Codex, use Luna from the Code review row. On absent, unknown, ≤5%, or rate-limited Codex, enter Claude-only mode at Sonnet from the Code review row and make no second Codex attempt for the session. |
| code-review | load-bearing | Use Opus directly from the Code review row; select no Codex rung. |
| plan-review | routine | Run the Codex presence/headroom gate first. With usable Codex, use Terra from the Plan / spec writing row. On absent, unknown, ≤5%, or rate-limited Codex, enter Claude-only mode at Opus from the Plan / spec writing row, which has no Sonnet rung, and make no second Codex attempt for the session. |
| plan-review | load-bearing | Use Opus directly from the Plan / spec writing row; select no Codex rung. |

The matrix routes for a Claude parent. A Codex parent follows its own session
policy in `dispatch-codex.md`, and this matrix does not route for it.

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
