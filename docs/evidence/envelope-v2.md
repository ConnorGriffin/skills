# Evidence envelope v2

This is the provider-neutral reference for methodology-skill observations. It vendors
the exact v2 contract in [contract-v2.json](contract-v2.json); its provenance is
[contract-v2.provenance.json](contract-v2.provenance.json). The skill pack validates
fixtures only. It keeps no evidence store, policy state, promotion path, or AgentFlow
runtime dependency.

## Eligibility and shape

Emit one tagged `producer` or `failure` envelope only after the observation has both a
durable authority pointer and an immutable subject revision. A Git subject uses its
resolved commit SHA. A GitHub or document subject uses its stable locator and the
normalized-content digest in `content_digest`. Scratchpads, chat-only conclusions,
candidate lists, proposals, prompts, source bodies, free-form findings, transcript
excerpts, secrets, and opaque model memory are ineligible.

Each envelope has exactly the fields listed by the vendored contract. `source` is the
authority pointer: its locator, repository, revision, scope, and normalized hash are
facts, not captured content. `producer` contains only `producer_kind`,
`validation_state`, `review_action`, `normalizer_version`, and `fact_digest`. A
failure envelope instead contains the six `failure_fact_fields`. Failure class,
validation state, and review action are separate fields; no field derives another.

Lineage links are ordered and use only the contract's relations. A link identifies a
related observation by ID, never embeds that observation's payload. Emit lineage only
when both linked observations are independently eligible.

## Closed producer event table

| Producer kind | Methodology event | Required authority and subject | Permitted action / validation | Lineage |
| --- | --- | --- | --- | --- |
| claim | scope or Wayfinder grounded claim | durable issue, ADR, Git, or document revision | `observed`, `reproduced`, `human_validated`, `model_judged`, `refuted`, or `unvalidated`; action nullable | `derives_from`, `governs` |
| criterion | scoped acceptance criterion | durable issue or document revision | same validation; action nullable | `derives_from`, `governs` |
| decision | scope or Wayfinder ruling | durable issue, ADR, or document revision | validated state; action nullable | `settles`, `governs` |
| disposition | scope or Wayfinder resolution | durable issue or ADR revision | validated state; action nullable | `settles`, `addresses` |
| objection | plan-review objection | reviewed plan revision and criterion locator | `reproduced`, `refuted`, or `unvalidated`; action nullable | `derives_from`, `refutes` |
| revision | plan revision after objection | revised artifact revision | validated state; action nullable | `revises`, `addresses` |
| verdict | plan-review conclusion | plan revision | validated state; action nullable | `settles`, `verifies` |
| finding | code-review exact-head or snapshot finding | reviewed Git SHA or snapshot identity | `reproduced`, `refuted`, or `unvalidated`; review action may be set | `derives_from`, `refutes` |
| review_action | code-review action for a finding | same reviewed identity | contract action and any validation state | `addresses` |
| fix | code-review fix | immutable parent and final revision | validated state; action nullable | `implements`, `addresses` |
| verification | plan, review, or orchestration check | authoritative revision | validated state; action nullable | `verifies`, `refutes` |
| delegation | orchestration delegation plan | authoritative task revision | validated state; action nullable | `delegates`, `derives_from` |
| slice | orchestration bounded slice | authoritative task revision | validated state; action nullable | `derives_from`, `governs` |
| decline | orchestration decline or collapse | authoritative task revision | validated state; action nullable | `settles`, `addresses` |
| settlement | final bounded outcome | authoritative revision | validated state; action nullable | `settles`, `verifies` |

The permitted fields are closed by `contract-v2.json`; fields not named there are
forbidden. The table provides no slot for worker final-message payloads, candidates,
proposals, promotion, policies, or transcripts.

## Working-tree code review identity

For a committed review, `subject.revision` is the exact reviewed SHA. For a working
tree review, resolve base and head SHAs, then set `subject.revision` to a deterministic
`sha256:` digest of the canonical tuple `(base_sha, head_sha, git diff --binary
base...head, git diff --cached --binary, git diff --binary, git ls-files --others
--exclude-standard with each untracked file's bytes)`. Set `subject.subject_kind` to
`working_tree_snapshot` and retain the resolved base/head as immutable SHA facts in
the subject identifier.
Two dirty snapshots at one HEAD therefore have distinct revisions. Do not substitute
`HEAD` alone for this identity.

## Examples

The checked-in positive examples are normalized pointers and digests only. Negative
fixtures prove rejected event kinds and that an `unvalidated` observation cannot be
presented as a lesson. They are exercised by `python3 scripts/validate.py`.
