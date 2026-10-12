---
title: The review front door
description: How a review request reaches one specialist review path.
flow: review,code-review,plan-review
---

## One route per review

`review` classifies the thing in front of it and routes to exactly one specialist. Code changes go to `code-review`; a load-bearing plan goes to `plan-review`.

This makes the review result finite: the selected skill owns its vocabulary, evidence, and stopping rule.
