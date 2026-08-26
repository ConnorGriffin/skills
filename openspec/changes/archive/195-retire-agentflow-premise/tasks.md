# Tasks

- [x] Remove evidence-v2 files, validator checks, and emission instructions
  (`docs/evidence/`, `scripts/validate.py` lines 46-58 and 206-776/868-869, the
  four skills' `## Evidence v2` sections, `tests/test_ci_changed_paths.py`'s
  path expectation, and the retired `EvidenceEnvelopeTests` class).
- [x] Restate live consumption and immutable-release facts in AGENTS.md /
  CLAUDE.md and `openspec/specs/pack-integrity/spec.md` / `openspec/project.md`.
- [x] Record ADR 195 and archive this completed change.
- [x] Convert or delete every copied prose constant from the pre-change
  extraction (`grep -nE '^ *[A-Z][A-Z0-9_]* = ' tests/test_behavior.py
  tests/test_ticket.py` against `main`). Closed mapping below: every constant
  maps to exactly one of **deleted** (subject is evidence-v2 or the pin
  mechanism itself), **structural** (a heading/count check suffices), or
  **behavioral** (assertIn of the load-bearing sentence, whitespace-normalized,
  against the live file — naming the surviving test).

## Constant mapping — tests/test_behavior.py

Infrastructure (paths, markers, module loaders — out of scope, unchanged):
`ROOT`, `CBM_SCRIPT`, `CBM_REINDEX`, `CBM_TEARDOWN`, `CBM_LIFECYCLE`,
`SPIN_SCRIPT`, `CODEX_WORKER`, `CLAUDE_WORKER`, `WORKER_LIFECYCLE`,
`UI_CRAFT_AUDIT`, `UI_CRAFT_CRITIQUE`, `UI_CRAFT_SWEEP`, `UI_CRAFT_ROUTE`,
`README`, `BEGIN_IGNORE`, `BEGIN_HOOK`, `LIFECYCLE_SPEC`, `LIFECYCLE_MODULE`,
`WORKER_SPEC`, `WORKER_MODULE`, `CLAUDE_WORKER_SPEC`, `CLAUDE_WORKER_MODULE`,
every class-level `SKILL`/`REFERENCE`/`AGENT_METADATA`/`RESOLVER`/
`ROUTES_JSON`/`UI_CRAFT`/`DRIVER`/`PROPOSAL`/`EPIC` path constant, and the
unrelated `drive-local-webapp` sandbox fixtures (`DARWIN_ERROR`,
`DARWIN_ERROR_ALT`, `TIMEOUT_ERROR`, `FORCE_DARWIN`, `PLAYWRIGHT_PACKAGE_JSON`,
`PLAYWRIGHT_STUB`).

| Constant | Disposition | Holding test |
|---|---|---|
| `MANDATORY_DELEGATION_AUTHORIZATION` | behavioral | `DelegationAuthorityContractTests` (`AUTHORIZATION`/`DISCRETIONARY_ONLY`/`REFUSAL_STOPS_WORKFLOW` needles against `code-review`, `plan-review`, `ticket` `SKILL.md`) |
| `EPIC_WORKER_DISPATCH` | behavioral | `EpicAdapterDispatchTests.test_research_worker_dispatch_stays_on_the_worker_adapters_only` |
| `EPIC_REWORK_SESSION_TOPOLOGY` | behavioral | `EpicDelegatedExecutionContractTests.test_proposal_session_topology_names_home_session_as_sole_ledger_writer` |
| `EPIC_DELEGATED_EXECUTION` | behavioral | `EpicDelegatedExecutionContractTests.test_epic_delegated_execution_keeps_dispatch_and_wave_rules` |
| `PLAN_REVIEW_COLD_READER_DISPATCH` | behavioral | `PlanReviewAdapterDispatchTests.test_caller_owned_round_ledger_covers_both_plan_locations` |
| `MECHANICAL_FIX_IN_PLACE_BODY` | behavioral | `PlanReviewAdapterDispatchTests.test_mechanical_fix_in_place_stays_narrow_and_deterministic` |
| `DESIGN_IT_TWICE_ADAPTER_DISPATCH` | behavioral | `DesignItTwiceAdapterDispatchTests` (both tests) |
| `PREFLIGHT_VERBATIM_COMMAND_OUTPUT` | behavioral | `VerbatimEvidenceBlockContractTests.test_preflight_forbids_edited_command_output` (subject is the command-output-pasting contract, not evidence-v2) |
| `PLAN_REVIEW_EVIDENCE_BLOCK_SPOT_CHECK` | behavioral | `VerbatimEvidenceBlockContractTests.test_plan_review_spot_checks_at_least_one_evidence_block` (same — not evidence-v2) |
| `PERSONA_REVIEW_PANELIST_DISPATCH` | behavioral | `PersonaReviewAdapterDispatchTests.test_panelist_dispatch_stays_on_the_worker_adapters_only` and `test_panelist_prompt_excludes_persona_and_panel_content` |
| `RESEARCH_WORKER_DISPATCH` | behavioral | `ResearchAdapterDispatchTests` (`research_job` helper + its three tests) |
| `REVIEW_ROUTING_CONTRACT` | behavioral | `LiveProseContractTests.test_reviewer_routing_and_admission_rules_remain_explicit` |
| `ROUTING_TABLE_REVIEW_CONSUMER` | behavioral | `ReviewerRoutingCanonicalContractTests.test_routing_table_review_consumer_block_is_load_bearing` |
| `ROUTING_TABLE_ROUTES` | behavioral | `ReviewerRoutingCanonicalContractTests.test_routing_table_routes_keep_the_review_row_and_escalation_rule` |
| `ORCHESTRATE_MAINTENANCE` | structural | `ReviewerRoutingCanonicalContractTests.test_orchestrate_pack_wide_reach_boundaries_are_preserved` (asserts exactly one `## Maintenance` heading survives); process prose only, no cross-skill callers |
| `CODE_REVIEW_DEPENDENCY_SELECTION` | behavioral | `ReviewerRoutingCanonicalContractTests.test_code_review_dependency_selection_keeps_the_headroom_gate` |
| `ORCHESTRATE_REVIEW_PRECEDENCE` | behavioral | `ReviewerRoutingCanonicalContractTests.test_orchestrate_review_precedence_overrides_generic_area_routing` |
| `ORCHESTRATE_PACK_WIDE_REACH` | behavioral | `ReviewerRoutingCanonicalContractTests.test_orchestrate_pack_wide_reach_boundaries_are_preserved` |
| `ORCHESTRATE_COLLECT_CHILD_RESULTS` | behavioral | `ReviewerRoutingCanonicalContractTests.test_orchestrate_collect_child_results_binds_every_dispatch` |
| `DISPATCH_CODEX_ADMISSION` | behavioral | `LiveProseContractTests.test_reviewer_routing_and_admission_rules_remain_explicit` (`cannot switch to Claude workers`) |
| `DISPATCH_CODEX_FROM_CLAUDE_ADMISSION` | behavioral | `LiveProseContractTests.test_reviewer_routing_and_admission_rules_remain_explicit` (`headroom at or below 5%`) |
| `REVIEW_DEPTH_DISPATCH_BOUNDARY` | behavioral | `LiveProseContractTests.test_review_depth_and_slicing_keep_their_load_bearing_rules` (`Full-depth orders keep one review round`) |
| `SLICING_ORCHESTRATOR_TIER` | behavioral | `LiveProseContractTests.test_review_depth_and_slicing_keep_their_load_bearing_rules` and `TicketLiveProseContractTests.test_session_fit_rules_are_produced_and_consumed` (`The coordinator never launches an agent smarter than itself.`) |
| `COORDINATOR_REVIEWER_SELECTION` | behavioral | `ReviewerRoutingCanonicalContractTests.test_coordinator_reviewer_selection_requires_independent_verification` |
| `README_CODE_REVIEW_ROW` | behavioral | `ReviewerRoutingCanonicalContractTests.test_readme_lists_code_review_and_plan_review_with_orchestrate_integration` |
| `README_PLAN_REVIEW_ROW` | behavioral | same test as above |
| `RESEARCH_WORKER_PARAGRAPH` (main tests/test_behavior.py:4948) | deleted as a constant | sentence is now a needle in `EpicAdapterDispatchTests.test_research_spike_worker_findings_handoff_is_explicit` |
| `VERIFICATION_AND_FAILURE_PARAGRAPH` (main tests/test_behavior.py:4955) | deleted as a constant | sentence is now a needle in `EpicAdapterDispatchTests.test_spike_close_order_and_failed_worker_disposition_are_explicit` |

## Constant mapping — tests/test_ticket.py

Infrastructure: `ROOT`, `TICKET_SCRIPT`, `TICKET_DIRECTORY`, `DISCOVERY_POLICY`.

Cross-file duplication guard, survives unchanged (Do 5a): `GRAPH_SELECTION_TRAPS`
(compares `codebase-memory`'s reminder.md against the discovery-policy prose;
comment at its definition names the dependent).

| Constant | Disposition | Holding test |
|---|---|---|
| `SESSION_FIT_TEMPLATE_BODY` | behavioral | `TicketLiveProseContractTests.test_session_fit_rules_are_produced_and_consumed` |
| `SESSION_FIT_TRIAGE_BODY` | behavioral | same |
| `SESSION_FIT_MODEL_CHECK_BODY` | behavioral | same |
| `CHUNKED_SESSION_FIT_TEMPLATE_BODY` | behavioral | same (structural counts: flat fence has exactly one `Session fit:`, chunked header fence has none) |
| `CHUNKED_SESSION_FIT_TRIAGE_BODY` | behavioral | same (`selected Agent rung:` and the fail-closed return-through-`/scope` sentence) |
| `CHUNKED_SESSION_FIT_MODEL_CHECK_BODY` | behavioral | same (byte-identical-across-`SUB-ORDER` sentence from `start.md`) |
| `BUILDER_SELF_CHECK_BODY` | cross-file duplication guard, survives (Do 5a) | `TicketLiveProseContractTests.test_builder_self_check_matches_its_live_template_copy` (compares `verbs/start.md` to `templates/work-order.md` directly) |
| `DRAFTING_CONVENTIONS_BODY` | deleted | subject is the pin mechanism itself — the canonical-prose-constant rule (Do 6) |
| `REVIEW_DEPTH_SENSITIVITY_FLOOR_BODY` | behavioral | `ReviewDepthSensitivityFloorTests.test_sensitivity_floor_forces_full_depth_non_negotiably` |
| `DRAFTING_CONVENTIONS_INSTRUCTION` | behavioral | `TicketSkillContractTests.test_drafting_conventions_instruction_is_inside_flat_and_sub_order_fences` and `test_ticket_verb_consumers_point_to_drafting_conventions` |
| `TICKET_CHUNK_WORKER_ADAPTER_DISPATCH` | behavioral | `TicketChunkWorkerAdapterDispatchTests` (both tests) |

Six sentinel headings (`## Reference boundary` x5, `## Consumer reach` x1) are
deleted; each was the final heading of its file and existed only as a closing
anchor for a byte-pin split. No surviving test splits on any of them: the
behavioral predicates above read each whole file
(`" ".join(text.split())`) and `assertIn` the load-bearing sentence directly,
so none needs a closing anchor at all. `drafting-conventions.md`'s
`## Consumer reach` sentinel is deleted along with its test per Do 6.
