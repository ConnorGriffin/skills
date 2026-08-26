---
title: The ticket flow
description: How one tracked issue becomes merged history, and which skill owns each step.
flow: epic,ticket,scope,orchestrate,review,pr-body
---

## The common path

The planning stack turns an idea into a durable work order before implementation begins. `epic` maps a large effort into clear child tickets; small work can begin at `ticket`. `ticket` owns the lifecycle: triage locks the brief, start creates the implementation path, revise actions a review round, and finalize records the result after merge.

`scope` resolves thin uncertainty, while `orchestrate` slices work that needs parallel attention. `review` is the front door for a terminating review round. `pr-body` makes the pull request explain the change in the pack's own terms.
