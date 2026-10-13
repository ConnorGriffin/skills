---
title: The UI lifecycle
description: How a rendered surface moves from intent to evidence.
flow: ui-craft,code-review
---

## A surface is a contract

`ui-craft` settles a surface's structure before any pixels: its screens, states, names, and gestures. After the operator picks one of three directions, review moves to component grain. An inventory is approved first, then a library built and approved a few components at a time, then screens composed only from approved components and locked one by one in a one-page design doc in the repo. A separate build ticket implements a greenfield lock, or revises a shipped surface in the running app while keeping the behaviors users rely on, and proves both with rendered evidence rather than source-only confidence.

The harness's built-in browser or preview tool supplies rendered evidence when a surface can run. A final `code-review` checks the change against the repository's rules and the originating issue.
