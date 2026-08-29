# Cover safe-fixture UI fidelity evidence in the worker-egress consent grant

## Why

Invoking `/ticket start` grants a bounded transfer for the mandatory reviewer
dispatches the verb routes, but the granted payload names only the work order,
repository code, and documentation. UI fidelity evidence — the screenshots
`/ui-craft` renders from manufactured or synthetic fixtures — falls outside that
payload, so a compliant coordinator must halt and re-ask before it can send those
captures to its reviewers. One live run stalled roughly half an hour on exactly
that question, which the operator had already answered at invocation.

The grant is also stated only at the front door. By the time a coordinator reaches
a reviewer dispatch, the sentence that authorizes it is far out of context.

## What changes

- Name UI fidelity evidence rendered from manufactured or synthetic fixtures in the
  granted payload, in both workflow front doors, both invocation manifests, and the
  three adapter approval rationales.
- Restate the grant at all four coordinator reviewer-dispatch steps — triage's
  `/plan-review`, start's and revise's `/review`, and chunked coordination's
  per-chunk review — so it is in context where the decision is made.
- Extend the behavior test that pins the payload wording to cover the four new
  dispatch-step statements.

The exclusion list is unchanged: credentials, secrets, patient data, `.env`, and
real database contents stay outside the grant, as does anything rendered from real
user, production, or patient data. Guidance text only; no runtime enforcement.
