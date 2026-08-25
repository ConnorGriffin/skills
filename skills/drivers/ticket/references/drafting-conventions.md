# Drafting conventions

## Drafting conventions

Canonical prose constants name only the bytes strictly between their named opening
and closing full-heading-line anchors; neither anchor is part of the constant.
Read source with `Path.read_bytes()` and compare bytes directly. Do not use
`read_text()`, universal-newline normalization, or a line-oriented surrogate.

Transcribe a target repository's `AGENTS.md` `Test:` entry byte-exact into the
order. When this host's interpreter substitution matters, state it separately and
exactly: `Run every python3 above as /opt/homebrew/bin/python3.14; bare python3
on this host is 3.9.6.`

Adapter prompts are prompt text passed positionally. The coordinator writes each
complete prompt to session scratch, passes that file's contents as the adapter's
positional prompt text, and never invents adapter flags or changes. Each dispatch
has one coordinator-owned state file; state is lifecycle metadata, never the
worker's result.

An expected diff is a closed allowlist of repository-relative paths. It has no
escape clause. A generated-facts appendix records deterministic commands and their
byte-complete literal output; every cited line is regenerated from the checked-out
tree.
## Consumer reach
