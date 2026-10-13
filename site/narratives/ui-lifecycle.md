---
title: The UI lifecycle
description: How a rendered surface moves from intent to evidence.
flow: ui-craft,code-review
---

## A surface is a contract

`ui-craft` designs a surface through eight gated stages, defined in its lock reference. Structure is settled before any pixels, review happens at component grain, and each screen is locked in a one-page design doc in the repo. A separate build ticket implements a greenfield lock, or revises a shipped surface in the running app while keeping the behaviors users rely on, and proves both with rendered evidence rather than source-only confidence.

The harness's built-in browser or preview tool supplies rendered evidence when a surface can run. A final `code-review` checks the change against the repository's rules and the originating issue.
