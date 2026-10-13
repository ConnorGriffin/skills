---
title: The UI lifecycle
description: How a rendered surface moves from intent to evidence.
flow: ui-craft,code-review
---

## A surface is a contract

`ui-craft` settles a surface's structure before any pixels: its screens, states, names, and gestures. It then locks a one-page design in the repo when the operator says "locked". A separate build ticket implements a greenfield lock, or revises a shipped surface in the running app while keeping the behaviors users rely on, and proves both with rendered evidence rather than source-only confidence.

The harness's built-in browser or preview tool supplies rendered evidence when a surface can run. A final `code-review` checks the change against the repository's rules and the originating issue.
