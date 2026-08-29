# Design

The existing claim command remains the only attribution interface. It gains one
required closed value, the lifecycle verb that is already known when the workflow
claims its session: `triage`, `start`, `revise`, or `finalize`. Role continues to
mean responsibility (`coordinator`, `worker`, or `reviewer`); verb means lifecycle
phase. Keeping those meanings orthogonal avoids turning “executor” into a role that
conflicts with existing worker attribution.

`session_cost` reads a missing verb as `legacy`, just as it already reads a missing
role without guessing. `scan` reports the verb on each session and aggregates verb
peaks beside the existing role peaks. The flat branch of `verdict` judges only
measurable `start` sessions whose role is not reviewer. The chunked branch remains
worker-role based and unchanged.

The transcript is still the measurement unit. The existing fresh-session contract
for `start` prevents a single peak from combining earlier triage context with build
context. Segmenting one transcript by lifecycle phase is unsupported and would be a
different telemetry system.

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
cannot calibrate flat orders; a flat order without measurable `start` evidence is
`unmeasurable`; chunked sizing continues to use worker roles only.

