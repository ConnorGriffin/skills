---
title: The UI lifecycle
description: How a rendered surface moves from intent to evidence.
flow: ui-craft,code-review
---

## A surface is a contract

`ui-craft` treats rendered UI as a lifecycle. It locks greenfield work before build, preserves shipped behavior during revision, and asks for rendered evidence rather than source-only confidence.

The harness's built-in browser or preview tool supplies rendered evidence when a surface can run. A final `code-review` checks the change against the repository's rules and the originating issue.
