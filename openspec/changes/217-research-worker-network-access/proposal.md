# Research worker source access

## Why

Research workers are dispatched read-only, but neither adapter currently opts
them into the hosted web tools they need to reach primary sources. A denied
tool leaves the coordinator to improvise a recovery path that the research
contract does not define.

## What changes

- Add an explicit, persisted network capability to both worker adapters without
  widening filesystem access or enabling arbitrary shell egress.
- Require research dispatches to request that capability and fail visibly when
  source access is unavailable.
- Define coordinator-fetched local source material as the bounded fallback,
  resumed through the same worker.

## Risk contract

- **Must prevent:** network access becoming implicit; widening repository write
  access; secret exposure; and silently presenting uncited output as completed
  research.
- **Must recover:** when a provider refuses hosted search or fetch, the
  coordinator fetches the required sources into session scratch and resumes the
  same worker against those local files.
- **Accepted failure:** when neither hosted tools nor coordinator fetching can
  obtain the required primary sources, research stops clearly and produces no
  successful findings artifact; recovery is manual.
- **Unsupported:** arbitrary shell-command egress, private or authenticated
  sources requiring worker credentials, local-network access, and identical
  tool names across model families.
- **Evidence owed:** default dispatch remains offline; the opt-in is present on
  start and survives resume for both adapters; read-only filesystem boundaries
  remain unchanged; and the research contract exercises the refusal fallback.

