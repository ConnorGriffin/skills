# Review depth

Applies to every order, flat or chunked. Triage stamps one depth per order or
sub-order; `start` and `revise` execute at that depth.

## The three depths

| Depth | What the reviewer checks | Fits |
|---|---|---|
| **Focused** | The exact change asked for, and that nothing else moved | A one-line value change, a version bump, a doc typo |
| **Targeted** | The changed behavior end to end, plus the repo rules that govern it | Most orders: a new resource, a workflow step, a bounded refactor |
| **Full** | The whole diff, every check the repo defines, adversarially | Anything sensitive, anything wide, anything the floor below forces |

## Stamping

* Triage stamps a depth with a one-line reason on every order and every
  sub-order: `Review depth: targeted (one new resource in one target, no shared
  behavior)`.
* An order arriving without a depth is reviewed **Targeted**. Absence is a triage
  defect, not a licence to review lightly.
* Depth escalates mid-review whenever the diff turns out wider or more sensitive
  than the stamp assumed. It never downgrades: a Full stamp stays Full even when
  the diff looks small.

## Sensitivity floor

Judgment, not a keyword match. A change is **Full**, non-negotiably, when it
touches any of:

* authentication, authorization, or identity (trust policies, role assumption,
  single sign-on, token scope)
* secrets: creation, rotation, scope, or exposure surface
* destructive or irreversible operations (deletes, replaces, force-applies,
  data-bearing resources)
* behavior shared across an organization (a shared library, an organization-level
  setting, a workflow every repo inherits)

For workflow machinery every repo inherits: Full when the change alters contract
semantics; Targeted for pure relocation, citation repoints, and additive paragraphs
that no existing consumer's behavior depends on.

These override a lower stamp without discussion.
## What blocks

A finding blocks only when it breaks the order's **Done when** clause. That is the
contract; reviewer taste is not.

* Blocking: the acceptance criteria will not hold, the verification step's
  expectation will not match, a repo rule the order named is violated.
* Not blocking: anything real but outside the order. It becomes a follow-up ticket
  or it is discarded. Never a silent fix, never a scope expansion.

## Reviewer dispatch boundary

Under `Profile: hardening`, Targeted and Focused orders get no reviewer; Full-depth
orders keep one review round after hardening.

Review depth is an input to
[review-routing.md](../../orchestrate/references/review-routing.md), which owns
reviewer classification, eligibility, and model precedence.

* A whole diff assembled from chunks is reviewed Targeted, or Full when any chunk
  was Full.
