---
title: The UI lifecycle
description: How a rendered surface moves from intent to evidence.
flow: ui-craft,drive-local-webapp,review
---

## A surface is a contract

`ui-craft` treats rendered UI as a lifecycle. It locks greenfield work before build, preserves shipped behavior during revision, and asks for rendered evidence rather than source-only confidence.

`drive-local-webapp` supplies local browser evidence when a surface can run. A final `review` routes any remaining question to the appropriate specialist.
