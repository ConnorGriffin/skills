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
- Define coordinator-fetched public source material as the bounded fallback for
  a successfully completed, resumable worker that reports hosted-tool refusal.

## Risk contract

- **Must prevent:** network access becoming implicit; widening repository write
  access; secret exposure; and silently presenting uncited output as completed
  research.
- **Must recover:** when a successfully completed, resumable worker reports a
  provider refusal of hosted search or fetch, the coordinator fetches the
  required public sources into a unique scratch directory under the worker cwd
  and resumes the same worker against a manifest of those local files.
- **Accepted failure:** when neither hosted tools nor coordinator fetching can
  obtain the required primary sources, research stops clearly and produces no
  successful findings artifact; recovery is manual. An adapter failure that
  leaves no resumable session also stops on this path.
- **Unsupported:** arbitrary shell-command egress, private or authenticated
  sources requiring worker credentials, local-network access, and identical
  tool names across model families.
- **Evidence owed:** default dispatch remains offline; the opt-in is present on
  start and survives resume for both adapters; read-only filesystem boundaries
  remain unchanged; both providers can read the cwd-local fallback material;
  and the research contract exercises the refusal fallback.
