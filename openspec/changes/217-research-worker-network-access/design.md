# Design

The adapters expose one task-level capability while translating it to each
provider's hosted research surface. Claude receives explicit permission for
`WebSearch` and `WebFetch`; Codex receives an enabled live web-search tool. The
shared lifecycle persists the capability so resume cannot silently lose it.

## ADR 217 — Network opt-in means hosted research tools

Add one opt-in adapter flag whose contract is access to provider-hosted web
search and fetch while preserving the selected filesystem sandbox. Do not map
the flag to arbitrary shell-command networking.

Each provider adapter translates the capability to its hosted source tools as
defined by that adapter's dispatch reference while retaining the selected
filesystem sandbox. Persist the boolean in worker lifecycle state and replay it
on resume; the dispatch references remain the sole normative home for concrete
provider argv.

### Consequences

Research gains equivalent source-retrieval capability across model families
without claiming identical tools or weakening repository confinement. Package
managers, `curl`, private endpoints, and other shell networking remain outside
the flag's promise. Provider policy can still refuse hosted tools, so the
research skill owns a deterministic coordinator-material fallback rather than
reporting false success. That fallback is the sole exception to the research
worker's original-prompt-only input rule: after a successfully completed worker
returns `SOURCE_ACCESS_UNAVAILABLE:`, the coordinator creates a unique
`.research-sources.*` directory under the worker cwd, stores only fetched public
source files plus `manifest.md` mapping each file to its URL, and resumes the
same session with the absolute manifest path. Ordinary adapter failures and
non-resumable sessions stop without a findings artifact.
