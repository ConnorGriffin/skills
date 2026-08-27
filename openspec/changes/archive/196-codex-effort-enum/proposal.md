# Correct the Codex worker effort enum

## Why

The worker locally accepted `minimal`, which the live Codex 5.6 API rejects,
and locally rejected `none` and `max`, which that API accepts.

## What changes

- Align the Codex worker's local guard with the 2026-08-27 live API probe.
- Preserve the superseded probe record while making the current documentation
  and orchestration references name the live enum.
- Pin the adapter's enum in behavior tests.

## Risk contract

The change only affects local validation before a Codex session launches.
The worker default remains `medium`; Claude's separate enum is unchanged.
