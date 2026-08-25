# Ledger — planning-stack rework

## Status
next: #144 triage — BLOCKED on operator decisions Q1 (bare-subject rule) and Q2 (plan-review Claude-only fallback); 2 of 3 panels spent; then #139 re-triage; #153-#157 JIT; #163-#165 per queue notes
updated: 2026-08-25

## Notes
- proposal and risk contract: openspec/changes/epic-rework/proposal.md
- build children: the /ticket skill; operator gates: acceptance lines on their tickets
- interim session-fit rule until #139 lands: see #138's session-fit comment for the pattern

## Fog
- #144 Q1 bare-subject routing rule: JUDGED_SENSITIVITY_FLOOR / CLOSED_SUBJECT_PROXY / LOAD_BEARING_UNLESS_OVERRIDDEN — awaiting operator
- #144 Q2 plan-review Claude-only fallback: the routing table's Plan/spec row is Terra -> Sol -> none, with no Claude rung, and warns against Claude for specs; #144's scope text asserts a Sonnet/Opus fallback that the table does not ground — awaiting operator

## Decisions
- #140 Review routing — direct routing-table reads in both review skills; Codex reviewers from a Claude parent behind the presence+headroom gate (Luna routine / Opus load-bearing, Claude-only fallback); skill-mandated spawns pre-authorized, task-level refusal still stops the run
- #135 Label inventory — 7-repo approved list; 7 workflow labels stand; all agentflow:*, wayfinder:*, ready-for-agent, ciq experiments, ticket:done deleted; type labels machine-applied

## Spikes
- #140 Review sub-agents through orchestrate routing (Codex included) — resolved — ruling approved, builds #144 #145 #146
- #135 Target-repo list and label inventory with dispositions — resolved — approved list plus amendment

## Builds
- #138 Mechanical rename wayfinder to epic — merged
- #142 Epic skill content (3a) — merged
- #143 Cross-skill amendments and machinery (3b) — merged
- #144 Route review skills through routing table — in triage (draft rewritten clean after round-1 BLOCK)
- #149 Universal effort dial and Claude CLI worker adapter — merged
- #150 Extract shared worker lifecycle into one module — merged
- #151 Dispatch code-review reviewers through pack adapters — merged
- #152 Dispatch plan-review cold reviewers through pack adapters — merged
- #153 Dispatch persona-review's panel through pack adapters — filed
- #154 Dispatch ticket's chunk agents through pack adapters — filed
- #155 Dispatch epic's workers through pack adapters — filed
- #156 Dispatch research's background agent through pack adapters — filed
- #157 Dispatch codebase-design's parallel design agents through pack adapters — filed
- #159 Delegated-execution mode for the epic home session — filed (behind #155)
- #163 Coordinator wait protocol: collect child results, never idle-wait — filed
- #164 Triage evidence blocks command-generated verbatim — filed
- #165 Builder self-check distilled from review blockers — filed
- #145 Claude-parent Codex reviewer dispatch reference — merged
- #146 Pre-authorize required review delegation — merged
- #139 Triage stamps session-fit preamble into work orders — in-progress

## Deferred
- #147 Session-fit rule for chunked work orders — after 3b and #144/#145

## Rounds
- 2026-08-25 #144 — triage round 2 on the clean rewrite: Sol cold review BLOCK on 4, all reproduced. Two are coordinator rulings now made: the review front door's resolver (skills/workflows/review/scripts/resolve_route.py) green-lights a partial install because PACK_SHIPPED_SKILLS and INSTALL_COMMAND only ever name the selected review skill, so making orchestrate required means amending the resolver and its tests; and reviewer ELIGIBILITY ("Haiku never reviews", review-depth.md:55, repeated at slicing.md:146) must move to review-routing.md or "sole authority" is unsatisfiable. Two are unsettled decisions routed to the operator per the cap rule: the bare-subject rule's candidate definitions miss file-backed PRDs and design docs, which plan-review/SKILL.md:12 admits as ordinary subjects; and the matrix's Claude-only Sonnet/Opus route for plan-review has no source in the Plan/spec row (Terra -> Sol -> none), whose own note warns against routing specs to Claude without a fail-safe review
- 2026-08-25 #144 — triage round 1: Sol drafted, Sol cold review returned BLOCK on 6 findings, all reproduced against the tree. Two changed the design: plan-review's stakes tier is a different axis from reviewer-model routing and must not be collapsed into it (its panel/termination contract is broader than review-depth's four sensitivity categories), and the classifier cannot live in ticket/review-depth.md because README declares no ticket dependency for either review skill and forbids hidden runtime requirements. Coordinator rulings: classifier homes in orchestrate beside routing-table.md (a dependency #140 already forces), plan-review stakes untouched, review-depth keeps depth and the floor but loses all reviewer-selection claims. Also caught: the verification chain in flight was stale, missing worker_lifecycle.py from AGENTS.md's Test line since #150. Order rewritten clean rather than patched
- 2026-08-25 #152 — PR #168 merged on green CI; worktree removed. #144's blocked-by edges (#145 #149 #151 #152) are all merged, so the final integration ticket is now triageable
- 2026-08-25 #152 — resumed from handoff: Opus worker had left the canonical-block rewrite uncommitted in the worktree, not lost; home session verified rather than redid it. Ten-mutation sweep over the pinned section caught all ten by construction, full chain green (401 tests, 27 skills). Capped review's acceptance met, so no new round. PR #168 opened; body passed scorer and a Terra cold voice judge
- 2026-08-25 handoff — operator ended the home session mid-#152; state comment posted on #152; ladder standing: Terra → Sol → Opus 5 (operator-amended); Codex-first directive stands for new dispatches
- 2026-08-25 #152 — built (Terra), two fix rounds failed semantic falsifiability, escalated Sol then Opus per ladder; reviewer capped with canonical exact-block mandate
- 2026-08-25 #151 — PR #167 merged after a base-drift CI failure (symbols moved by #150's refactor; Sol merged main and repointed by import-verification); #152 build dispatched on the settled base, instructed to reuse #151's test harness
- 2026-08-25 #151 — built through 3 review rounds; Terra failed the portable-recovery criterion twice, escalated to Sol per ladder (operator amended ladder: Sol failure now escalates to Opus 5 before surfacing); Sol's fix proved both native and portable paths; PR #167 opened
- 2026-08-25 #150 — fix round closed both blockers (dead gate_wait removed, unmocked Claude lifecycle coverage); PR #166 merged on green CI
- 2026-08-25 #151 #152 #165 — both dispatch orders countersigned and stamped (Terra/medium) after multi-round Sol cold review; #151 building (#152 serialized behind it, shared test module); #165 filed distilling 4 blocker patterns into builder self-check
- 2026-08-24 #149 — PR #162 merged after conflict resolution with #161 (coordinator reconciled both SKILL.md rewrites, kept both test pins); #150 build dispatched (Sol), #151 #152 triage drafts dispatched (Terra)
- 2026-08-24 #149 — chunked build complete over 3 review rounds (caught invalid --cwd flag, live $HOME sandbox escape, stale reference shape); PR #162 opened, Sol voice-judged the body; merge on green
- 2026-08-24 #145 — PR #161 merged on green CI after base update; #144's blockers now down to #149 #151 #152
- 2026-08-24 #146 — PR #160 merged on green CI; #161 awaiting re-run after base update; #149 chunk 2 rerunning Claude-side live cases post-auth-fix
- 2026-08-24 routing — operator directive: Codex-only for new dispatches (opus rung → Sol, sonnet rung → Terra, escalate Terra → Sol; Claude only if Sol fails); in-flight work untouched
- 2026-08-24 #145 #146 — both built (Sonnet, Terra), Full-depth reviews converged SHIP with zero blocking findings; PRs #161 #160 opened, merge on green CI
- 2026-08-24 #150 — triaged (opus / high, Full depth, blocked on #149); order pins base commit and mandates post-rebase re-derivation; triage caught a would-be reversal of the #62 stdin risk contract and corrected the issue body's line census (9, not 5)
- 2026-08-24 #145 — triaged (sonnet / high, Full depth, landable on either #149 base); building via Sonnet session; session-fit comment posted
- 2026-08-24 #159 — filed: delegated-execution mode (operator hands locked subtrees to the home session), attached to #133, proposal amendment in scope
- 2026-08-24 orchestration — operator delegated completion to home session after killing Sol sessions; #144 reframe done (blocked, native edges), #146 triaged (Terra/medium, Full depth) and building via Terra worker, #149 building via Opus coordinator (chunked), #145 #150 triages in flight, #151-#157 held for just-in-time triage
- 2026-08-24 #144 #149-#157 — dispatch subtree surfaced; #144 reframed as final integration behind #145 #149 #151 #152; nine new builds attached to #133
- 2026-08-24 #139 — start blocked: work order predates #158's rewrite of the same files; re-triage required
- 2026-08-24 #143 — built and merged as PR #158 (Opus / medium); finalize in progress; #139 and #144-#146 unblocked
- 2026-08-24 #143 — triaged (Opus / medium); session-fit comment posted per interim rule
- 2026-08-24 #142 — built and merged as PR #148 (Terra / medium), finalized; 3b unblocked
- 2026-08-24 #142 — triaged (Terra / medium); session-fit comment posted per interim rule
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
