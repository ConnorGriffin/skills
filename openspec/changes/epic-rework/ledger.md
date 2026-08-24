# Ledger — planning-stack rework

## Status
next: /ticket triage #142 (3a) in a fresh session; #143 (3b) after 3a merges; then #144-#146
updated: 2026-08-24

## Notes
- proposal and risk contract: openspec/changes/epic-rework/proposal.md
- invoke /ticket for every build child; operator gates are acceptance lines on their tickets
- until #139 lands, the home session posts a session-fit comment on each triaged ticket (ladder from orchestrate routing-table) so /ticket start stays a single bare command

## Fog
- none

## Decisions
- #140 Review routing — direct routing-table reads in both review skills; Codex reviewers from a Claude parent behind the presence+headroom gate (Luna routine / Opus load-bearing, Claude-only fallback); skill-mandated spawns pre-authorized, task-level refusal still stops the run
- #135 Label inventory — 7-repo approved list; 7 workflow labels stand; all agentflow:*, wayfinder:*, ready-for-agent, ciq experiments, ticket:done deleted; type labels machine-applied

## Spikes
- #140 Review sub-agents through orchestrate routing (Codex included) — resolved — ruling approved, builds #144 #145 #146
- #135 Target-repo list and label inventory with dispositions — resolved — approved list plus amendment

## Builds
- #138 Mechanical rename wayfinder to epic — done (PR #141 merged, finalized)
- #142 Epic skill content (3a) — filed
- #143 Cross-skill amendments and machinery (3b) — filed
- #144 Route review skills through routing table — filed (queued behind 3a/3b)
- #145 Claude-parent Codex reviewer dispatch reference — filed (queued behind 3a/3b)
- #146 Pre-authorize required review delegation — filed (queued behind 3a/3b)
- #139 Triage stamps session-fit preamble into work orders — in triage; rescoped to flat orders plus start.md no-re-ask line, chunked residue deferred to #147

## Deferred
- #147 Session-fit rule for chunked work orders — after 3b and #144/#145

## Rounds
- 2026-08-24 #133 — all children attached as native sub-issues; PR #136 body now names the epic; won't-do rule: close as not-planned, labels off, stays attached; research spikes: worker writes body, home session posts under ## Findings
- 2026-08-24 #139 #147 — triage found scope couldn't meet acceptance; rescoped to flat orders (option 2 + start.md no-re-ask), chunked half filed deferred as #147
- 2026-08-24 gate — dotfiles PUBLISHED_SKILLS updated to drivers/epic, reinstall run, test -L ~/.claude/skills/epic passes; children 4–7 unblocked on this gate (dotfiles commit unpushed)
- 2026-08-24 #140 — ruling approved; builds #144 #145 #146 filed, queued behind 3a/3b for file overlap
- 2026-08-24 #140 — Terra findings posted: direct routing-table reads for both review skills; Codex reviewers from Claude parent behind the presence+headroom gate; skill-mandated spawns pre-authorized
- 2026-08-24 #142 #143 — filed 3a/3b per sequencing; #138 finalized; operator gate before children 4–7: test -L ~/.claude/skills/epic after dotfiles reinstall
- 2026-08-24 #138 — build merged as PR #141; #140 re-dispatched per orchestrate routing (Terra, read-only)
- 2026-08-24 #140 — filed: review skills never route to Codex; skill-mandated spawns blocked by session instructions (observed on #138 start)
- 2026-08-24 #139 — filed: start sessions ask about model fit; fix is a fit preamble stamped at triage
- 2026-08-24 #138 — triaged in fresh session; work order stamped, no spec amendment needed
- 2026-08-24 #138 — filed rename build; spike resolved
- 2026-08-24 #135 — home session generated inventory across 7 repos; proposed resolution posted, one stale claim surfaced (home#18)
