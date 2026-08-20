Managed by codebase-memory skill installer.

# Code discovery policy

Use codebase-memory-mcp graph tools first for structural code exploration only
when `list_projects` and `index_status` show that the exact project is indexed.
Use `search_graph` to find symbols, `trace_path` for callers and callees,
`get_code_snippet` for exact source, `query_graph` for multi-hop questions, and
`get_architecture` for orientation. Use `search_code` or ordinary search and
file reads for literal text, configuration, non-code files, and unindexed
projects.

Activating this skill never indexes a project. Run `index_repository` only when
indexing is explicitly requested or required by the target repository.
