# Design

The existing claim command remains the only attribution interface. It gains one
required closed value, the lifecycle verb that is already known when the workflow
claims its session: `triage`, `start`, `revise`, or `finalize`. Role continues to
mean responsibility (`coordinator`, `worker`, or `reviewer`); verb means lifecycle
phase. Keeping those meanings orthogonal avoids turning “executor” into a role that
conflicts with existing worker attribution.

`session_cost` reads a missing verb as `legacy`, just as it already reads a missing
role without guessing. `scan` reports the verb on each session and exposes
`verb_peaks` as five fixed scalar integer maxima (`triage`, `start`, `revise`,
`finalize`, and `legacy`), using `0` when a phase has no measurable session. The
flat branch of `verdict` judges only measurable `start` sessions whose role is not
reviewer. The shared zero-claim path remains `no-data`; attributable claims without
a measurable eligible start peak return `unmeasurable`. The chunked branch remains
worker-role based and unchanged.

The transcript is still the measurement unit. The workflow therefore permits one
lifecycle verb per session: a same-verb resume keeps its claim, while moving from
triage to start or from start to revise/finalize requires a fresh session. This
prevents one peak from combining execution with lifecycle overhead. Segmenting one
transcript by lifecycle phase is unsupported and would be a different telemetry
system.

Claim de-duplication remains idempotent for the same ticket, session, and verb. If
the same ticket/session is submitted under a different verb, the command keeps and
prints the persisted claim, reports one visible conflict naming the persisted and
submitted verbs, and exits successfully under telemetry's existing non-blocking
rule. It never prints unstored submitted metadata as though it landed.

## ADR 234 — Lifecycle verb is separate from session role

**Status:** accepted

**Decision:** add a closed lifecycle-verb field to claims and use `start` as the
flat-order execution discriminator. Preserve role as responsibility and preserve
missing verbs as explicit legacy data.

**Why:** a fourth executor role would overload responsibility with lifecycle phase,
while an execution boolean would solve only this verdict and create a second narrow
classification. The verb is the smallest field that names the fact already known at
every claim site and directly satisfies ADR 70's explicit-attribution rule.

**Consequences:** every workflow claim site supplies its current verb; old claims
cannot calibrate flat orders; a flat order with attributable claims but no
measurable eligible `start` evidence is `unmeasurable`, while zero attributable
claims remain `no-data`; a session is never reused across lifecycle verbs; a
cross-verb re-claim is visible but non-blocking; chunked sizing continues to use
worker roles only.
