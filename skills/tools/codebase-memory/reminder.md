Managed by codebase-memory skill installer.

# Code discovery policy

Use codebase-memory-mcp graph tools first for structural code exploration, against
exactly one project: the one that belongs to the checkout you are working in.

Establish that project before querying. When a workflow supplies a `project` for
the checkout it verified, use exactly that name as given. Otherwise resolve the
canonical current checkout through the supported structured interface,
`python3 <cbm-onboard-skill-directory>/scripts/cbm-lifecycle.py ensure <checkout
path>`, and use the `project` it prints. Never pick the graph by project name,
branch-like label, list order, apparent recency, or because it was the only result;
`list_projects` is an inventory, not a way to choose the current checkout. A
reported `unavailable`, or no usable interface at all, means ordinary search and
file reads for the rest of the session. Follow cbm-onboard's bounded diagnostic and
retry sequence: distinguish a missing or unsupported binary from an unable-to-respond
CLI; retry the same `ensure` command with its documented local-only sandbox rationale
only after the normal workspace-write attempt. An active-generation conflict means
wait and retry, never a sandbox denial or permission to close another session.

With that project established, use `search_graph` to find symbols, `trace_path` for
callers and callees, `get_code_snippet` for exact source, `query_graph` for
multi-hop questions, and `get_architecture` for orientation. Use `search_code` or
ordinary search and file reads for literal text, configuration, non-code files, and
unindexed projects.

Activating this skill never indexes a project. Run `index_repository` only when
indexing is explicitly requested or required by the target repository.
