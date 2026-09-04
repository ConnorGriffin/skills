# Design

## ADR 293 — Continue the caller under explicit boundaries

Status: accepted in attended triage, 2026-09-04.

An answered decision updates the active task and resumes its next authorized step. Helper completion returns to its caller; only the outer requested workflow's completion or a concrete unresolved boundary ends the turn. Required unanswered decisions, actual denials, unavailable required evidence, failed source admission, and explicit human handoffs remain boundaries. A blocker names the dependent action and missing input; unrelated authorized work continues. User steering is applied to the existing task unless it explicitly replaces it.

The existing base profile owns the cross-workflow rule. Independently installed helpers carry the minimum local return instruction they need, with a pointer to the authority, rather than requiring an uninstalled profile. TDD consumes interface and behavior decisions already present in an admitted lock; it asks only for a new material decision. Existing exact-scope authorization is consumed, not requested again.

## ADR 293 — Host-compatible choices preserve alternatives

The locked interview presentation remains the default where permitted. Higher-priority host restrictions win; this change cannot bypass them. When the host permits a choice tool, use its supported interface. When it requires a plain question, present a proposed implementation and the considered alternatives as explanatory comparison with meaningful costs, then ask one concise question with a stable Q identifier. Do not disguise prohibited multiple-choice questions as prose, hide alternatives, pre-answer the user's decision, or treat the recommendation as accepted. Accept rejection, free-form alternatives, partial answers, and explicit delegation. Required unanswered decisions wait; settled choices do not recur. Disclose a host-caused format change before using it. Update the existing lock to describe this narrow compatibility case, retaining its normal appearance.

## ADR 293 — Executor choice and reviewer evidence are separate

Explicit operator selection of Astra for execution/coordinator work is admissible when the host's authoritative available-model metadata identifies that model and supports the required work. This is an explicit admission, not a benchmark result or a new rung in every ladder. Preserve the current row ladders and reviewer precedence. Match known model identity through authoritative metadata; never guess hidden effort or claim an unsupported cross-family strength comparison. Unknown identities or unsupported required capabilities produce an actionable admission question. A selected Astra coordinator can use the existing admitted worker routes; that policy is stated directly rather than implemented as an invented numerical hierarchy. Unchanged reviewer and headroom gates still apply.

This triage uses the operator-directed, unvalidated Terra plan-review exception. Implementation retains Full review and its existing permitted routes; selecting Astra as executor never selects it as reviewer. State an unresolved reviewer route explicitly rather than skipping or silently downgrading review. Do not add model-resolution code or alter provider settings.

## ADR 293 — Produce first-revision evidence before admission

For a shipped surface without a suitable frozen ledger, triage may run the behavior sweep in its selected ticket checkout after the existing safe-start declaration and manufactured-data source have been verified. Triage records and freezes the behavior ledger/replay through the existing operator-sanction procedure before pinning the source and posting a lock. This exception permits evidence preparation, not implementation or new design changes. If the safe source or required sanction is unavailable, triage reports that specific unmet prerequisite and posts no executable lock. An epic child carries any required parent-contract amendment through its existing child-worktree path; it creates no separate child change record.

Nested UI work keeps the admitted ticket branch and base. Only standalone setup chooses a fresh default-branch tip. Umbrella charter/epic prose refers to the selected lifecycle: shipped revision uses behavior evidence; greenfield/fallback uses its lock. Do not invent a replacement mock for a shipped surface. A worker commits its chunk and returns evidence; only the coordinator opens the ticket PR.

## Failure and proportionality decisions

Retain installed reviewer-memory failure semantics, source pins, retirement sanctions, safe-start, fresh lifecycle sessions, and human merge. Optional persona-memory approval does not retroactively invalidate a verdict. Consume prior approvals only when they cover the exact decision and scope.

CBM keeps its existing stdout JSON and exit statuses. Surface an actionable bounded diagnostic on stderr when the underlying CLI cannot operate; preserve the existing fail-closed handling of malformed responses or wrong identity. Never print environment secrets or raw private source. Its owning skill defines the supported version check, sandbox-specific bounded permission retry, and actionable fallback; ticket and code-discovery consumers point to that sequence. An active-generation conflict is not labeled a sandbox failure and does not authorize closing unrelated sessions.

Clean must capture enough pre-pass state to undo only its own edits while preserving both index and working-tree content, including unstaged edits. No whole-file restore from Git's index or HEAD may substitute for pre-pass state. If concurrent changes make safe reversal uncertain, preserve them and report the conflict. Use ordinary snapshot or patch operations, not a new rollback tool.

Preflight and polish ask for evidence proportionate to the admitted behavior, not elapsed-time busywork or mandatory external participants for every tiny change. Retain every evidence obligation actually named by the accepted contract. Builder fail-first expectations apply to changed executable behavior where a meaningful negative test exists; prose behavior uses the bounded fresh-session replays below, not string-matching tests presented as proof of behavior.

### Risk contract

- **Must prevent:** secret exposure, irreversible loss of authoritative data, silent incorrect success, lost pre-existing edits, and silent bypass of required review, source admission, or human-merge boundaries.
- **Must recover:** none automatically; this text-focused change does not add a recovery subsystem.
- **Accepted failure:** unavailable tooling or unsupported host capabilities may stop the dependent step with an actionable reason and manual recovery; continue independent authorized work. A bounded model replay may expose a remaining failure and must be reported honestly.
- **Unsupported:** overriding system/developer instructions, unattended changes to global configuration or unrelated CBM sessions, editing bundled caches, proving universal model behavior, or inferring reviewer benchmark eligibility from executor model metadata.
- **Evidence owed:** existing repository checks; bounded fresh-session continuation, inherited-approval, host-compatible interview, UI handoff, chunk completion and stop-boundary replays; disposable-repository proof that the clean procedure preserves pre-existing content; direct evidence for CBM retry/fallback guidance.
- **Why:** repair the observed composed workflow with prose and existing interfaces, preserving its actual safety and evidence boundaries.
- **Disposition:** copy unchanged into the admitted design record.

## Delivery and evidence ownership

Chunk 1 owns helper continuation, host-compatible decision communication, CBM diagnostics, and their tests. Chunk 2 consumes those public prose contracts and owns ticket/model/UI integration and stale consumer corrections. Serial ordering reflects that dependency. The coordinator incorporates chunk 1's signed-off commit into the ticket branch before creating chunk 2's worktree from the updated ticket branch. The coordinator alone updates this change's task checkboxes and records aggregate replay results in `replay-results.md`; workers return raw evidence through their ordinary result channel. The lock's file allowlists are in `inventory.md`.

A bounded replay uses a fresh session with the actual candidate instruction files and a disposable scenario. Capture the model, effective host restriction relevant to the scenario, input sequence, observed next action, expected action, and verdict. Report blocked evidence as blocked. A static audit or a hypothetical response is not a behavioral pass. Use existing adapters; add no reusable harness, runner, or new runtime machinery. The replays must cover: agreement followed by next permitted action; helper completion before parent completion; inherited TDD approval plus a new-decision counterexample; host-restricted alternatives without a leading default; safe UI evidence production with inherited checkout; chunk return without a PR; and an unanswered decision/denial that still stops the dependent step. Group compatible cases into a small number of sessions but reset context for independent comparisons. Repeat a failed case after its relevant fix only.

CBM regression tests exercise its command-line interface with disposable fake executables: an empty failing CLI response with an actionable error remains unavailable on stdout/exit 2 with a useful stderr reason; missing/unsupported binary stays distinguishable; malformed JSON and wrong project remain fail closed. No production daemon restart is a test prerequisite. Clean evidence uses disposable Git repositories with staged and unstaged baseline content and verifies the index and working-tree bytes after a failed pass, including preservation of unrelated content. No pack script under test targets a real project checkout.

For integration run the repository Test command exactly as copied in the lock, using a supported Python on this host; run strict OpenSpec validation. Changed executable behavior needs meaningful regression tests. Do not expand the suite with static tests that merely duplicate the prose. Stop at the implementation PR; archive later through the repository's existing human-merged archive PR procedure.
