# Robust Skills adoption audit

## Decision

Adopt three narrowly scoped streams in the first implementation pass: ticket
capability ownership/slicing, codebase-design's hexagonal direction and adapter
responsibility, and UI Craft web implementation. The web stream is delivered through
the existing ticket → Surface lifecycle → `/ui-craft` route, not as standalone
skills; UI Craft progressively discloses the CSS/JavaScript mechanics. This is an
adaptation plan, not a vendor-skill import.

**Upstream snapshot.** `ccheney/robust-skills` at
`0ace9a7f5c20d19cad678b894a717945da2ea8ed` (the HEAD of the supplied clone),
licensed MIT. All upstream links below are immutable blob permalinks at that
commit.

## Inventory and fit

| Stream | Upstream skills (10 total) | Current maintained coverage | Decision |
| --- | --- | --- | --- |
| Architecture | [clean-ddd-hexagonal](https://github.com/ccheney/robust-skills/blob/0ace9a7f5c20d19cad678b894a717945da2ea8ed/skills/clean-ddd-hexagonal/SKILL.md) | `skills/tools/codebase-design/` defines modules, seams, and adapters, but not an inward-dependency or port-responsibility rule. | Adapt the narrow gap. |
| Frontend organization | [feature-slicing](https://github.com/ccheney/robust-skills/blob/0ace9a7f5c20d19cad678b894a717945da2ea8ed/skills/feature-slicing/SKILL.md) | `ticket` already slices work orders and assigns disjoint file/target ownership; UI Craft owns rendered-surface lifecycle. | Borrow only ownership language for ticket chunks; defer FSD architecture. |
| UI web implementation | [modern-javascript](https://github.com/ccheney/robust-skills/blob/0ace9a7f5c20d19cad678b894a717945da2ea8ed/skills/modern-javascript/SKILL.md), [modern-css](https://github.com/ccheney/robust-skills/blob/0ace9a7f5c20d19cad678b894a717945da2ea8ed/skills/modern-css/SKILL.md) | UI Craft owns the ticket-routed surface lifecycle but lacked a compact web-mechanics reference. | Absorb both concept streams into one progressively disclosed UI Craft reference. |
| Database | [postgres-drizzle](https://github.com/ccheney/robust-skills/blob/0ace9a7f5c20d19cad678b894a717945da2ea8ed/skills/postgres-drizzle/SKILL.md) | No database-specific tool. | Defer. |
| Diagrams | [mermaid-diagrams](https://github.com/ccheney/robust-skills/blob/0ace9a7f5c20d19cad678b894a717945da2ea8ed/skills/mermaid-diagrams/SKILL.md) | Existing documentation can use diagrams; no universal diagram-generation procedure. | Defer. |
| Slack | [slack-mrkdwn](https://github.com/ccheney/robust-skills/blob/0ace9a7f5c20d19cad678b894a717945da2ea8ed/skills/slack-mrkdwn/SKILL.md), [slack-block-kit](https://github.com/ccheney/robust-skills/blob/0ace9a7f5c20d19cad678b894a717945da2ea8ed/skills/slack-block-kit/SKILL.md) | No Slack connector, app, or product-facing delivery workflow. | Defer. |
| Teams | [teams-message-formatting](https://github.com/ccheney/robust-skills/blob/0ace9a7f5c20d19cad678b894a717945da2ea8ed/skills/teams-message-formatting/SKILL.md), [teams-adaptive-cards](https://github.com/ccheney/robust-skills/blob/0ace9a7f5c20d19cad678b894a717945da2ea8ed/skills/teams-adaptive-cards/SKILL.md) | No Teams connector, app, or delivery workflow. | Defer. |

The overlap is deliberate only in two places. `ticket` already requires slicing,
fresh-agent-readable sub-orders, serial/parallel modes, and disjoint ownership
in `skills/drivers/ticket/references/slicing.md`; it must remain the owner rather
than gaining a second feature-architecture skill. `codebase-design` already owns
the vocabulary—especially seam and adapter—so a hexagonal addition belongs there,
not in a DDD/clean-architecture duplicate. The upstream FSD hierarchy would
conflict with the charter's locality, deletion test, and "second caller" seam
rule ([profile/CHARTER.md](../../profile/CHARTER.md)).

## First-pass implementation contracts

### 1. Ticket capability ownership and slicing

**Destinations:** `skills/drivers/ticket/references/slicing.md`,
`skills/drivers/ticket/templates/work-order.md`,
`skills/drivers/ticket/verbs/triage.md`, and `tests/test_ticket.py`.

**Boundary:** make each chunk own a coherent capability plus its named files or
targets; name any shared contract and its single owning chunk; prohibit a parallel
chunk from implementing, revising, or depending on another chunk's internal
capability. Preserve the existing trait rubric, measured thresholds, tracker
contract, one ticket branch/PR, and coordinator integration. The upstream source
supports strict directional ownership and public APIs; use that idea only to make
ticket sub-orders executable independently, not to impose FSD folders.

**Tests/acceptance:** add static contract tests that the template, triage procedure,
and slicing reference agree on capability owner, shared-contract owner, and no
parallel overlap. A chunked work order is accepted only when every capability and
shared contract has exactly one owner, parallel ownership is disjoint, and each
sub-order is stand-alone. Do **not** copy FSD's layers, `@x` notation, import rule,
directory tree, or Steiger setup.

### 2. Hexagonal direction and adapter responsibility

**Destinations:** `skills/tools/codebase-design/SKILL.md`,
`skills/tools/codebase-design/references/DEEPENING.md`, and
`tests/test_behavior.py`.

**Boundary:** add a compact decision rule: application/domain code declares the
needed capability at its seam; adapters translate external protocols, storage,
clock, and framework details; dependencies point from adapter toward the core;
composition selects adapters. Tie a seam to the existing two-adapter rule—do not
manufacture ports for hypothetical substitution. This fills the upstream's
dependency/placement guidance without replacing the pack's deep-module model.

**Tests/acceptance:** assert the canonical vocabulary and the four responsibility
rules occur in both entry point and reference. Acceptance is that a reader can
place a port, adapter, and composition root without allowing core code to import
infrastructure, while a one-adapter case remains local. Do **not** copy the
upstream's DDD tactical catalogue, aggregate limits, CQRS/event-sourcing/outbox
prescription, authorization placement table, or canonical directory layout.

### 3. UI Craft web implementation

**Destinations:** `skills/drivers/ui-craft/reference/web-implementation.md`, its
single context pointer in `skills/drivers/ui-craft/SKILL.md`, minimal direct-mode
pointers, and focused assertions in `tests/test_behavior.py`.

**Boundary:** route the concepts through the existing ticket → Surface lifecycle →
`/ui-craft` path. Establish the project baseline first; distinguish ECMAScript
standardization, runtime/host support, and transform/polyfill support; preserve the
small set of JavaScript semantics traps; and make CSS cascade, layout, support, and
degradation decisions. UI Craft remains the single owner of lifecycle, visual
contracts, behavior preservation, and rendered verification.

**Tests/acceptance:** behavior tests require the progressive-disclosure pointer,
baseline-before-decision structure, the three compatibility questions, CSS fallback
or degradation, lifecycle/evidence binding, and pinned provenance. Do not create
standalone language skills or copy dated matrices, edition snapshots, proposal
tables, or exhaustive feature catalogs.

## Deferred work

**Postgres/Drizzle:** defer for both domain specificity and version volatility.
The upstream begins with incompatible stable `0.x` and `1.0.0-beta/rc` relation
APIs and says its official documentation tracks v1 syntax; a general portable pack
cannot safely choose between them without a project-specific version contract.

**Mermaid:** defer because delivery compatibility is the issue, not syntax volume.
The upstream calls C4/architecture forms experimental or beta and notes that hosts
bundle different Mermaid versions, requiring a target-platform render check. This
pack has no Mermaid renderer dependency and explicitly avoids third-party
dependencies ([AGENTS.md](../../AGENTS.md)); add it only with a concrete rendering
surface and verification path.

**Slack and Teams:** defer all four skills. Their upstream guidance is explicitly
vendor-surface/transport-specific: Slack distinguishes multiple markup systems and
streaming/block payloads, while Teams distinguishes four incompatible markup
systems and multiple transport wrappers. The Teams sources also encode dated
connector-retirement guidance. With no Slack/Teams connector or owned delivery
surface here, these broad proactive triggers would create unsupported, rapidly
changing product policy rather than reusable pack behavior.

## MIT provenance and authorship

The upstream [MIT license](https://github.com/ccheney/robust-skills/blob/0ace9a7f5c20d19cad678b894a717945da2ea8ed/LICENSE) permits adaptation provided its
copyright and permission notice accompany copies or substantial portions. Write
each selected skill as a new, pack-native synthesis; cite this pinned snapshot in a
short `Provenance` section and state that its rules, examples, structure, and
wording are adapted by this pack's authors. At implementation, add a
`robust-skills contributors (c) 2026` attribution and source URL to `NOTICE`, and
add the same portion attribution to `LICENSE` if any substantial text, table,
example, or reference file is carried forward. If copying is avoided as bounded
above, the attribution still makes provenance clear without misrepresenting
authorship; if it is not avoided, carry the full upstream MIT notice with the
copied material.
