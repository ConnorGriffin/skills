# Scope ledger — orchestrate: Codex headroom check

Routed by /scope → interview mode. Change: on /orchestrate invocation, check
Codex (ChatGPT plan) headroom; at 0% drop all Codex routes and delegate to
Claude models only for the rest of the session.

## Grounding facts

- Codex rate-limit state is recorded in session rollout files
  (`~/.codex/sessions/**/*.jsonl`) as `rate_limits` events:
  `primary.used_percent`, `window_minutes` (10080 = weekly), `resets_at`,
  `plan_type`. No dedicated `codex usage` CLI command exists (v0.144.0).
- Routing table Codex routes: Luna (exploration, review), Terra (impl, plan,
  brainstorm), Sol (prototyping), Spark (latency). Some ladders end on Codex
  models ("none (top of ladder)").

## Decisions

- Headroom is read fresh at invocation via a trivial `codex exec` probe, then
  parsing the `rate_limits` snapshot from the newest rollout file — stale
  snapshots from old sessions are not trusted. — `inline`
- Trip threshold is ≤5% headroom remaining (guard band, not literal 0%);
  a probe that itself fails with a rate-limit error also trips. — `inline`
- Mid-session rate-limit failures from any Codex delegation flip the session to
  Claude-only from that point on — same rule, second trigger. — `inline`
- Degraded (Claude-only) routing uses each row's Claude rungs; plan/spec
  writing routes to Opus with a mandatory coordinator fail-safe review (per the
  table's polarity-error warning); prototyping goes straight to Opus. — `inline`

## Open questions

(none — frontier empty)

## Spawned tasks

(none)
