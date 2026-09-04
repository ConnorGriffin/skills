---
name: reviewer-memory
description: Store durable review and slicing observations locally as raw JSON plus an OKF digest. Use when capturing review outcomes, reading a repository's accumulated reviewer memory, or distilling its durable lessons.
---

# Reviewer Memory

Reviewer memory is one operator's local, durable record of review outcomes and ticket slicing. Each repository has a store under `~/.config/reviewer-memory/<repo-key>/`, where `<repo-key>` is the filesystem-safe form of ticket's normalized remote. The store contains:

```text
<repo-key>/
  raw.jsonl       append-only review and slicing captures
  okf/
    index.md      entry page for the OKF bundle
    <topic>.md    one-concept-per-file durable lessons
```

The OKF bundle is a directory of Markdown documents. Each page has only `title`, `updated`, and `tags` YAML frontmatter. `okf/index.md` is the entry page and pages link to each other with explicit relative links.

## Script interface

Run `scripts/memory.py` with one of these commands:

- `ensure <repo>` resolves a remote URL or checkout, creates the missing store skeleton, and prints JSON with its key, paths, and whether the bundle has body content.
- `append-review <repo>` reads one JSON object from all of standard input and appends a review record to `raw.jsonl`.
- `append-slicing <repo>` reads one JSON object from all of standard input and appends a slicing-outcome record without renaming its fields. Completing either operation returns its result to the caller; it does not complete the caller's review or workflow.
- `pointer <repo>` prints the absolute path to `okf/index.md` for prompt injection.

`raw.jsonl` is permanent: never truncate or rewrite it as part of ordinary use.

## Failure rule

Missing store roots are created on demand, and an empty bundle is valid. If a store exists but its paths are unreadable, writes are denied, `raw.jsonl` has a malformed JSON line, or `okf/index.md` does not start and close frontmatter with `---` lines, the script exits nonzero and names the file and repair. On a permission denial, rerun the verb outside the sandbox or with escalated permissions. A caller **halts its verb** on that exit; it does not continue without memory. The sole deliberate absence is that this skill is not installed at all: a consumer that cannot find this script says one line and continues without memory.

## Distill

The operator invokes `/reviewer-memory distill [repo]` to turn permanent captures into a compact, useful bundle:

1. Read the repository's complete `raw.jsonl` and its durable GitHub artifacts, including work-order comments and committed docs or scope ledgers.
2. Rewrite `okf/` as an OKF bundle. Keep `index.md` to a capped one-page digest; link it explicitly to per-topic pages such as `gotchas.md`, `request-types.md`, and `slicing-outcomes.md` when those topics exist.
3. Preserve every raw line. Distillation is idempotent over `raw.jsonl`: it revises the derived bundle, never the capture record.
