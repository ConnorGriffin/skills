# Design

## ADR 253 — Safe-fixture fidelity evidence joins the literal-invocation egress payload

**Context.** ADR-194 settled that literally invoking `/ticket triage|start|revise`
or `/orchestrate` grants a bounded transfer: the work order or task prompt plus
only what the delegated task needs from the repository's code and its
documentation, to the isolated worker the routing selects, with credentials, secrets, patient data,
`.env`, and real database contents excluded. That payload predates `/ui-craft`
attaching fidelity screenshots to the work a reviewer has to see. A coordinator
holding those captures therefore has to stop and re-ask — correct behavior against
the grant as written, and an interruption the operator has already answered.

**Decision.** The granted payload now reads: the work order or task prompt plus
only the repository code, documentation, and UI fidelity evidence rendered from
manufactured or synthetic fixtures (tracked in the repository or not, never real
user, production, or patient data). Frontmatter descriptions, which are capped at
1024 bytes, carry the compacted form "repository code, documentation, and
safe-fixture UI fidelity evidence".

The boundary rides on the pack's existing safe-fixture taxonomy — `manufactured`
and `synthetic`, the two `SAFE_DATA_SOURCES` in `/ui-craft`'s router. Evidence
rendered from anything else is not in the payload. The phrase covers untracked
local captures deliberately, because a fidelity screenshot is usually a working
file rather than a committed one.

Every coordinator reviewer-dispatch step now restates the grant in place: triage's
`/plan-review`, start's and revise's `/review`, and chunked coordination's
per-chunk review. A consent sentence a thousand lines from the dispatch it governs
does not reach the agent making the call.

**Supersedes.** ADR-194's payload sentence. That record is frozen legacy history
under the charter's ADR-home rule, so it keeps its original bytes and is not
edited; this record is the live one.

**Consequences.** The exclusion list is untouched, and nothing here is enforced at
runtime — the boundary is a prose contract the behavior test pins, exactly as
before. A consumer on an older vendored pin of this pack keeps re-asking until the
pin is bumped.

## Why the pin is two substrings, not one

`assert_material_boundary` pinned one literal naming only code and
documentation across every payload surface. Its replacement has to match both the
long body phrase and the compacted frontmatter form, which diverge after
"documentation, and". Pinning "repository code, documentation, and" together with
"ui fidelity evidence" matches both, and is strictly stronger than the term it
replaces: it now takes two independent regressions to pass a surface that has
dropped the evidence clause.

## What the descriptions gave up

The longer payload phrase costs bytes in two frontmatter descriptions that are
capped at 1024. The ticket description pays by dropping "to execute a work order"
from its trigger list; that phrase is the one trigger this skill also states in
its `## Invocation` body and in the `start` verb's own refusal path, so losing it
from the description narrows catalog matching without losing the rule. The
orchestrate description pays with the shorter delegation clause alone and keeps
its full trigger prose, landing at the cap exactly.

The qualifier that bounds the evidence to safe fixtures is pinned, not just the
evidence clause itself: every payload surface must carry either the long form's
"manufactured or synthetic fixtures" parenthetical or the description's
"safe-fixture" compound. Without that, a surface could name UI fidelity evidence
with no fixture bound and keep the suite green, which would authorize screenshots
rendered from production data — the outcome this change's risk contract must
prevent.

## Baseline specs

The deltas here carry the new wording; `openspec/specs/` keeps the old phrase until
the post-merge archive syncs it, which is this repository's established sequence.
