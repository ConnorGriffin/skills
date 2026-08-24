# Scope ledger — epic-manager

Driver skill atop /orchestrate: an epic-level architect that splits work into
workstreams at real seams, briefs per-workstream coordinator leads, and verifies
boundaries only.

## Status

Redefined 2026-08-24: the architect-over-parallel-leads design stays shelved
(base rate: one 3+-seam epic, #133, in harmonic's history). The live design is
a sequential integration-batch driver, proven by harmonic PR #160 (tickets
#95-#106 as one integration branch, coordinator-merged sub-PRs, full gate per
merge, one human-merged PR to main). The skill codifies that prompt's generic
skeleton; repo specifics stay in work orders and repo CLAUDE.md.

Generic skeleton: coordinator-only atop /orchestrate; integration branch from
fresh origin/main; ordered tickets whose newest WORK ORDER comment is the
verbatim brief (no re-triage); rebase each ticket branch onto the current
integration tip before /ticket start; sub-PRs target the integration branch
and only those may be coordinator-merged; full repo gate after every merge;
claims measured from the current tip, never copied from orders; parked-ticket
list is untouchable; escalate to owner only for trust failures and unsettled
design decisions; report each state change in the first sentence after it.

## Decisions

- Hierarchy is capped at two levels: architect over coordinator leads — evidence
  degrades past two relays; inline
- Leads run /orchestrate internally; the epic manager never routes models itself —
  keeps the routing table and its verification loop intact; inline
- Coordination is written artifacts (contract briefs, ledger), not agent-to-agent
  chat; inline
- Architect verifies boundaries: integration gates, composition, one spot-checked
  diff per workstream, evidence pasted not summarized; inline
- Leads run as sub-agents of the epic session, continued via SendMessage; the
  session lives as long as the epic and is re-seedable from this ledger; inline
- Below three seams: refuse, fall back to plain /orchestrate; inline
- Briefs and epic ledger live in docs/scope/<epic>.md, per-workstream
  sections; inline
- A dead or drifting lead is replaced via /handoff from the ledger; inline
- No automatic rollback on a bad integration; human pre-merge review is the
  guardrail; inline
- Epics with open decisions: manager routes decisions to the operator and
  dispatches only unblocked workstreams (harmonic epics are decision-gated);
  inline
- Entry point: standalone driver skill named /epic, invoked with the ordered
  ticket list, integration branch name, and parked list (supersedes the earlier
  ticket-verb idea); inline
- Model routing per the orchestrate table; the #160 Codex-only force was a
  per-run budget instruction and is not codified; inline
- /epic may launch sub-coordinators (an orchestrate session owning a slice of
  the batch) when a slice is genuinely independent; two levels maximum;
  default is the sequential loop; decide the spawn rule at implementation;
  inline

## Open questions

- Dispatch mechanic for leads (SendMessage sub-agents vs manual sessions vs remote)
- Workstream-count threshold and fallback behavior
- Where contract briefs and the epic ledger live
- Relationship to scope/handoff skills (reuse vs own format)
- Category placement and skill boundaries in the pack

## Spawned tasks

- Sonnet exploration of harmonichq/harmonic issue history (done, verified):
  ~88 issues, 2026-08-18 to 2026-08-24. Epic candidates: #19 I:C rework (serial,
  decision-gated), #133 Diagnose evidence canvas (sub-issues #134-#139 plus
  handoffs #143-#145; the one genuine 3+ parallel-seam epic), #82 cold-start
  (serial, blocks the others), CI/tooling cluster (loose theme, ~2 streams).
  Spot-check: #133 sub-issues confirmed via API.
