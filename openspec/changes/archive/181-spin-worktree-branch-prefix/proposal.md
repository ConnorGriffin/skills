# Resolve spin-worktree branch prefixes per machine

## Why

The helper currently creates Codex-named branches for every new issue, even for
operators using another agent or no agent at all.

## What changes

- Resolve a new issue branch prefix from an explicit flag, then per-machine
  configuration, then no prefix.
- Document the configuration location and bare branch form.
- Keep the ticket workflow's nonnumeric branch guidance aligned with the same
  resolution rule.

## Risk contract

The config file is optional and malformed durable input must not prevent a
worktree from being created. New behavior is exercised in throwaway Git
repositories, leaving real checkouts and real user configuration untouched.
