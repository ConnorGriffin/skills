# Evidence envelope v2

This is the provider-neutral reference for methodology-skill observations. It vendors
the exact v2 vocabulary manifest in [contract-v2.json](contract-v2.json); its
provenance is [contract-v2.provenance.json](contract-v2.provenance.json). Wire
semantics come from AgentFlow commit
`98d67d3b4a3f72d243e4765075d4a6728f6c46d1`,
`agentflow/evidence_contract.py` and `agentflow/evidence.py`. The skill pack
reproduces those semantics locally. It has no AgentFlow runtime dependency, evidence
store, policy state, or promotion path.

## Eligibility and wire shape

Emit one `failure_observation` or `producer_fact` envelope only after the
observation has a durable authority pointer and immutable subject revision.
`observed_at` is a nonnegative integer and never a Boolean.

The manifest lists the union of possible fact fields; actual wire shapes are
conditional:

- Every failure has only `failure_class`, `validation_state`,
  `signature_digest`, and `normalizer_version`. Only
  `fix_introduced_defect` additionally requires `reviewed_parent_revision`
  and `fixer_revision`.
- Every producer has only `producer_kind`, `fact_digest`,
  `normalizer_version`, and `validation_state`. Only the
  `review_action` producer additionally requires a nonempty
  `review_action` from the closed enum; that field is forbidden on every other
  producer.

`observation_id`, `target_event_id`, normalizer versions, locators,
repositories, scopes, and other ID fields use the upstream ID grammar: 1–128
characters, starting alphanumeric and continuing with alphanumerics, `.`, `_`,
`:`, `/`, or `-`. Digests are 32–128 raw lowercase hexadecimal characters;
they never carry a `sha256:` prefix.

A subject is exactly one of:

- `review`: exactly `subject_kind`, `subject`, and `revision`, with a
  40–64-character lowercase hexadecimal revision;
- `issue` or `document`: those three fields plus `locator` and
  `content_digest`; the first three use the ID grammar and the digest is raw
  lowercase hex.

A source has exactly `authority_kind`, `repository`, `locator`, `revision`,
`content_hash_algorithm`, `content_hash`, and `scope`. All are nonempty.
`authority_kind` is `github` or `repository`. A GitHub revision is 40–64
lowercase hex. A repository revision is exactly `sha256:` followed by its raw
`content_hash`.

Scratchpads, chat-only conclusions, candidates, proposals, prompts, source bodies,
free-form findings, transcripts, secrets, and opaque model memory are ineligible.

## Closed producer event table

All producers permit every closed validation state. The action column describes the
conditional `review_action` field, not lineage.

| Producer kind | Methodology event | Required authority and subject | Action field | Permitted outgoing lineage |
| --- | --- | --- | --- | --- |
| claim | scope or Wayfinder grounded claim | issue, document, or review revision | forbidden | `derives_from` |
| criterion | scoped acceptance criterion | issue or document revision | forbidden | `derives_from` |
| decision | scope or Wayfinder ruling | issue or document revision | forbidden | `derives_from`, `governs`, `revises` |
| disposition | scope or Wayfinder resolution | issue or document revision | forbidden | `derives_from`, `governs`, `revises` |
| objection | plan-review objection | document revision | forbidden | `derives_from`, `revises` |
| revision | plan revision after objection | document revision | forbidden | `derives_from`, `implements`, `revises` |
| verdict | plan-review conclusion | document revision | forbidden | `derives_from`, `governs`, `verifies`, `refutes` |
| finding | code-review exact-head or snapshot finding | review revision | forbidden | `derives_from`, `addresses` |
| review_action | code-review action for a finding | review revision | required enum value | `derives_from`, `addresses` |
| fix | code-review fix | review revision | forbidden | `derives_from`, `addresses` (required), `implements`, `revises` |
| verification | plan, review, or orchestration check | immutable revision | forbidden | `derives_from`, `verifies`, `refutes` |
| delegation | orchestration delegation plan | issue or document revision | forbidden | `derives_from`, `delegates` (required) |
| slice | orchestration bounded slice | issue or document revision | forbidden | `derives_from` (required), `delegates` |
| decline | orchestration decline or collapse | issue or document revision | forbidden | `derives_from` |
| settlement | final bounded outcome | immutable revision | forbidden | `derives_from`, `settles` (required) |

## Exact lineage matrix

Links are unique, ordered by dense integer ordinals from zero, and bounded to 32.
The source and target event kinds must both be admitted by the selected relation:

| Relation | Source producer kinds | Target event kinds |
| --- | --- | --- |
| `derives_from` | any producer | any producer or `failure_observation` |
| `governs` | decision, disposition, verdict | claim, criterion, delegation, slice, finding, review_action, fix, verification |
| `addresses` | finding, review_action, fix | `failure_observation`, finding, objection |
| `delegates` | delegation, slice | claim, criterion, decision, delegation |
| `implements` | revision, fix | criterion, decision, finding, review_action |
| `verifies` | verification, verdict | claim, criterion, decision, finding, fix, verification |
| `refutes` | verification, verdict | claim, criterion, decision, finding, fix, verification |
| `revises` | revision, decision, disposition, objection, fix | claim, criterion, decision, disposition, objection, revision, finding, fix |
| `settles` | settlement | claim, decision, disposition, verdict, fix, verification |

Only four relations are required by producer kind: fix → `addresses`, settlement
→ `settles`, delegation → `delegates`, and slice → `derives_from`. The
checked-in fixture additionally requires each target to identify an earlier envelope
from the same repository, making the example graph bounded and acyclic.

## Working-tree code review identity

For a committed review, `subject.revision` is the exact reviewed SHA. For a working
tree review, resolve base and head SHAs, then set the review `subject.revision` to
the raw 64-character SHA-256 digest of the canonical tuple `(base_sha, head_sha,
git diff --binary base...head, git diff --cached --binary, git diff --binary,
git ls-files --others --exclude-standard with each untracked file's bytes)`.
Retain base and head in the ID-safe review subject
`base:<base_sha>/head:<head_sha>`. Two dirty snapshots at one base/head therefore
have distinct raw revisions. Do not prefix the revision with `sha256:`, and do not
substitute `HEAD` alone.

## Examples

The positive fixture contains normalized pointers and digests only. Its dense,
backward lineage covers:

- scope and Wayfinder: claim → criterion → decision → disposition;
- plan review: claim and criterion through objection, revision, refuting
  verification, and verdict;
- code review: failure, finding, review_action, fix, verification, and settlement,
  plus two distinct dirty snapshots at one base/head;
- orchestration: claim, criterion, delegation, slice, decline, verification, and
  settlement.

Together the envelopes cover all 15 producer kinds and all six failure classes.
Negative fixtures keep candidates separate from observations and reject prohibited
producer and failure kinds. `python3 scripts/validate.py` validates the complete
matrix, conditional shapes, IDs, raw digests, source/subject vocabularies, lineage,
snapshot distinction, and negative fixtures.
