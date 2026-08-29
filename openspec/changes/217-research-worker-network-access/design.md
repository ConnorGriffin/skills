# Design

The adapters expose one task-level capability while translating it to each
provider's hosted research surface. Claude receives explicit permission for
`WebSearch` and `WebFetch`; Codex receives an enabled live web-search tool. The
shared lifecycle persists the capability so resume cannot silently lose it.

## ADR 217 — Network opt-in means hosted research tools

Add one opt-in adapter flag whose contract is access to provider-hosted web
search and fetch while preserving the selected filesystem sandbox. Do not map
the flag to arbitrary shell-command networking.

For Claude, allowlist `WebSearch` and `WebFetch` while retaining `dontAsk` and
the existing read-only write denials. For Codex, enable the hosted web-search
tool in live mode while retaining `--sandbox read-only`. Persist the boolean in
worker lifecycle state and replay it on resume.

### Consequences

Research gains equivalent source-retrieval capability across model families
without claiming identical tools or weakening repository confinement. Package
managers, `curl`, private endpoints, and other shell networking remain outside
the flag's promise. Provider policy can still refuse hosted tools, so the
research skill owns a deterministic coordinator-material fallback rather than
reporting false success.

