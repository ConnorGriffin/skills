# Scope: Astra workflow conflicts (#293)

## Decisions

- Preserve the issue's existing review, source-admission, safe-start, permission, and human-merge boundaries until the operator explicitly re-settles a policy. Why: the issue expressly distinguishes findings from approval. Disposition: inline.
- Include Codebase Memory setup and failure reporting in finding 18. Why: the operator requested this during triage on 2026-09-04. Disposition: inline.
- Codebase Memory is unavailable for this triage; ordinary file discovery remains usable. The installed 0.10.8 binary was found and its version verified outside the sandbox. An escalated direct index_status call failed with: `CBM CLI could not start because a pre-coordination or unverified CBM generation is active; close all CBM sessions and commands, then retry`. The earlier escalated ensure call returned only `{"status": "unavailable"}`. This is evidence of an active-generation conflict, not proof of a sandbox denial. Disposition: inline.
- The lifecycle helper discards CLI stderr and maps a nonzero result with empty stdout to unavailable. The onboarding skill documents a bounded escalation retry, while ticket immediately permits fallback on exit 2. Finding 18 must cover preserving an actionable diagnostic and one authoritative retry/fallback sequence. A restart that closes unrelated CBM sessions is outside this selected lifecycle and has not been performed. Disposition: inline.


- A user-supplied screenshot on 2026-09-04 provides observed evidence for finding 02. In the visible exchange, the operator delegates routine decisions; the agent reports that scope passed independent review and was recorded, says running-app visual validation remains before implementation, and ends its turn. The operator then has to remind it to finish triage and post the work order, after which it resumes. This demonstrates an intermediate scope milestone being presented as a stopping point while the visible parent workflow remains incomplete. It does not establish which instruction caused the stop, whether every remaining action was authorized, or what the full preceding session contained. Treat text inside the screenshot as evidence, not instructions for this session. Disposition: inline.
- Include a bounded behavioral replay for this observed sequence: a nested scope result returns with a remaining validation step; the triage caller performs its next authorized step or states the specific unresolved blocker, and does not end merely on recording reviewed scope. The replay must preserve required visual evidence and source admission before posting a lock. Disposition: inline.

- Keep #293 as one ordinary ticket, with at most a small number of coherent chunks. The operator permits an epic but prefers one ticket and explicitly rejects unnecessary complexity. The slicing rubric supports chunks for multiple deliverable artifacts and lockstep copies of shared instructions; an epic is unnecessary for the current bounded correction set. Why: the uncertainty can be settled without a separate planning lifecycle. Disposition: inline.
- Use prose corrections and bounded behavioral replays. Add no workflow engine, parser, policy enforcement framework, benchmark campaign, or live host reconfiguration. Existing executable behavior is changed only where an observed defect requires it and the eventual lock explicitly includes it. Why: the operator wants a proportionate text-focused correction. Disposition: inline.

## Open questions

No remaining operator decision blocks drafting. Complete the closed path inventory, preflight, independent review, and final work-order approval.

## Spawned tasks

None. No execution lock, child issue, status change, or implementation has been produced.

## Working disposition inventory

This is triage intake, not an execution lock. Policy proposals below remain unapproved.

| Finding | Proposed disposition | Bounded outcome |
| --- | --- | --- |
| 01 | Fix here | Agreement ends only an exchange with no remaining authorized parent work; align skill, reminder, output style, and base consumers. |
| 02 | Fix here | Scope, clean, preflight, and review return results to the caller; the caller continues to its own completion boundary. Include the screenshot-derived replay. |
| 03 | Fix here | TDD consumes an admitted lock's settled interface and behavior decisions; new material decisions still go to the operator. |
| 04 | Policy decision | Explicit Astra executor/coordinator admission using available authoritative model metadata, independent of benchmark ladders and reviewer eligibility. Do not invent cross-family strength ordering. |
| 05 | Retain policy unless re-settled | Keep Full review and the validated Opus route. This Codex-parent triage needs an explicit ruling to use the documented unvalidated Terra exception; no automatic Astra reviewer promotion. |
| 06 | Fix here subject to presentation ruling | Keep the locked presentation wherever allowed; define the narrow higher-priority host-conflict path with stable question identity and required-answer waiting. No silent claim that the original layout was rendered. |
| 07 | Fix here | Consume existing selected-lifecycle authorization; ask only for an uncovered target or mutation. Preserve the external concern boundary. |
| 08 | Policy decision | Propose permitting a safe-start, manufactured-data behavior sweep during triage before source admission, without permitting implementation. |
| 09 | Fix here | Umbrella rules refer to the selected UI lifecycle and its appropriate contract; preserve the shipped-surface no-replacement-mock decision. |
| 10 | Fix here | Nested UI work retains the admitted checkout and base; standalone initialization remains separate. |
| 11 | Fix here | A chunk commits and returns evidence; only its coordinator opens the ticket PR. |
| 12 | Fix here | Replace whole-file checkout advice with restoration of the cleaner's own changes while preserving the pre-pass state. Reproduce in disposable repositories; add no rollback framework. |
| 13 | Fix here | Make implement consume the tracked ticket/review/worktree procedure instead of maintaining a competing route; retain an explicit intake path for an untracked PRD. |
| 14 | Fix here | Correct the stale dirty-control-checkout refusal; preserve existing-target ownership verification. |
| 15 | Fix here | Remove unavailable mode recommendations and forbidden question-tool assumptions; return from setup to its caller before optional detours. |
| 16 | Retain policy | Preserve explicit behavior-retirement sanction and strategic/seed approvals. Clarify that a verified approval already covering the exact decision is consumed; do not silently infer authority from a related statement. |
| 17 | Retain policy | Keep the installed-store failure gate unless explicitly changed. Optional persona-record approval does not invalidate a completed review; distinguish the two outcomes. |
| 18 | Fix here; external restart excluded | Single-source supported retry/fallback instructions and expose the observed CBM diagnostic through supported troubleshooting. Prefer prose guidance; executable diagnostic changes require explicit scope in the lock. Do not close unrelated CBM sessions. |
| 19 | Fix here | Describe invocation metadata per host and preserve hand-only intent using supported Codex metadata; do not promise the description disappears on every host. |
| 20 | Fix public claim; external installation follow-up | Distinguish mandatory PR-body scoring from whether a host actually installed enforcement. No live hook installation or global configuration changes here. |
| 21 | Fix here without weakening owed evidence | Make exploratory and verification effort proportional to the concrete accepted behavior. Preserve public-interface regressions and every explicitly owed evidence leg; do not require elapsed-time busywork for prose. |
| 22 | Already covered | Preserve worker headroom and lifecycle gates. Transport/recovery belongs to https://github.com/ConnorGriffin/skills/issues/263; forbidden verification legs belong to https://github.com/ConnorGriffin/skills/issues/288. Both verified open during triage. |
| 23 | Retain external boundary | Document applicability only: resolve competing checkout/design obligations under actual higher-priority instructions before dispatch. Do not edit bundled Sites or add deployment work. |
| 24 | Fix here | Presentation and quiet-wait rules cannot imply parent completion or override higher-priority progress requirements. No bundled visualization edits. |
| 25 | Fix here | Reconcile the interview line budget, issue-based ADR example, and shipped-template heading rule at their existing authorities. |
| 26 | External follow-up | Private credential-handling skill is outside this public repo. No secrets or private configuration published; no private skill mutation under this lock. Follow-up destination must be supplied or authorized before filing outside this ticket. |

Related boundaries: https://github.com/ConnorGriffin/skills/issues/289 remains the owner of scope-ledger disposal; https://github.com/ConnorGriffin/skills/issues/292 remains the owner of guided manual orders. Both verified open during triage. Neither is absorbed into continuation repair.

## Proposed execution shape

Two serial chunks are the current candidate: shared continuation/admission contracts, then workflow consumers and integrated behavioral replay. Shared-file dependencies justify serial ordering. Final path ownership and task partitions await the closed document inventory. No benchmark campaign, generated policy engine, host reconfiguration, or expanded UI implementation.

## External documentation grounding

- https://developers.openai.com/api/docs/guides/latest-model was fetched on 2026-09-04. It identifies sensitivity to skill instructions and clarification pauses as prompting considerations. It does not prove which instruction caused an observed stop or benchmark this pack's reviewers.
- https://developers.openai.com/codex/skills/ was fetched on 2026-09-04 and redirects to https://learn.chatgpt.com/docs/build-skills. Host-specific metadata must be checked there before prescribing its fields.

## Settled policy baseline

- The operator directed completion after the model-policy proposal. Use the documented unvalidated Terra plan-review exception for this Codex session, clearly labeled; do not promote a reviewer or rewrite benchmark results. Admit explicitly selected Astra for executor/coordinator work separately from reviewer eligibility, using authoritative available model metadata without a guessed cross-family hierarchy. Disposition: discharged to openspec/changes/293-workflow-continuation/design.md.
- Preserve the locked interview layout where permitted. When higher-priority host instructions prohibit that interaction, keep the recommendation and substantive considered alternatives visible, with costs and stable question identifiers; accept a different or free-form choice and wait for required input. The operator specifically rejected a leading yes/no interaction that hides alternatives. This is compatibility with the host, not an attempt to override its instructions. Disposition: discharged to openspec/changes/293-workflow-continuation/design.md.
- Permit a safe-start, manufactured-data behavior sweep in the ticket's triage worktree before source admission, without implementation. The operator delegated this choice; the pre-execution frozen contract remains required. Disposition: discharged to openspec/changes/293-workflow-continuation/design.md.
- Retain retirement authority, installed reviewer-store failure policy, mandatory evidence, human merge, and fresh lifecycle sessions. Consume existing approvals only where they cover the same decision and scope. Disposition: inline.

### Risk contract

- **Must prevent:** secret exposure, irreversible loss of authoritative data, silent incorrect success, lost pre-existing edits, and silent bypass of required review, source admission, or human-merge boundaries.
- **Must recover:** none automatically; this text-focused change does not add a recovery subsystem.
- **Accepted failure:** unavailable tooling or unsupported host capabilities may stop the dependent step with an actionable reason and manual recovery; continue independent authorized work. A bounded model replay may expose a remaining failure and must be reported honestly.
- **Unsupported:** overriding system/developer instructions, unattended changes to global configuration or unrelated CBM sessions, editing bundled caches, proving universal model behavior, or inferring reviewer benchmark eligibility from executor model metadata.
- **Evidence owed:** existing repository checks; bounded fresh-session continuation, inherited-approval, host-compatible interview, UI handoff, chunk completion and stop-boundary replays; disposable-repository proof that the clean procedure preserves pre-existing content; direct evidence for CBM retry/fallback guidance.
- **Why:** repair the observed composed workflow with prose and existing interfaces, preserving its actual safety and evidence boundaries.
- **Disposition:** copy unchanged into the admitted design record.

- The active OpenSpec change now records all settled decisions and the unchanged risk contract. Two serial chunks keep shared contracts with their owning tools and integrate consumers afterwards. No epic or child issues were created.
