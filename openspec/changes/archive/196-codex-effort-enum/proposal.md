# Correct Codex worker launch and resume validation

## Why

The worker locally accepted `minimal`, which the live Codex 5.6 API rejects,
and locally rejected `none` and `max`, which that API accepts. Its resume path
also omitted the checkout-check bypass used by start, making a non-checkout
worker impossible to resume.

## What changes

- Align the Codex worker's local guard with the 2026-08-27 live API probe.
- Preserve the superseded probe record while making the current documentation
  and orchestration references name the live enum.
- Pin the adapter's enum in behavior tests.
- Keep resume usable from the recorded non-checkout working directory.

## Risk contract

The change only affects local validation before a Codex session launches.
The worker default remains `medium`; Claude's separate enum is unchanged. Resume
continues to rely on the lifecycle-owned recorded cwd rather than adding `-C`.
