# Bounded implementation evidence

The source contract remains pinned at `8dee32b38046177674819e2c427b077396a97ad1`.
This record reports observations; it does not claim that prose instructions repair
all model behavior. The implementation is delivered as a draft with the interview
failure below unresolved. The task checklist records implemented contracts and
completed evidence collection, not a universal behavioral pass.

## Combined verification

The lock's complete verification command ran on the combined implementation at
`b6c1713a1e28663a25559091203d98f5b835b2e3`, with every Python invocation using the
specified supported interpreter. It completed with exit 0, including compilation.

```text
validated 28 skills and 481 files
Ran 536 tests in 82.619s
OK (skipped=23)
py_compile exit 0
Change '293-workflow-continuation' is valid
DCO_OK commits=11
```

A later structural check covers this evidence file and checkbox bookkeeping.
Existing static contract assertions were updated where lifecycle wording changed;
those assertions are not presented as model-behavior evidence.

## Fresh-session behavioral cases

The bounded scenario workers used `gpt-5.6-terra`, medium effort, through the
installed Codex adapter. They read the actual candidate instruction files. These
were explicitly framed disposable scenarios; results do not establish universal
behavior or a new model ranking. Raw launcher results, tool traces, fixture files
and captures remain in coordinator session scratch. The observed inputs and
results are recorded here so a final message is not the sole evidence.

| Case | Input sequence and observed next action | Result |
| --- | --- | --- |
| Agreement and helper return | The nested scope helper had returned a proposed inspection to a parent task. The worker asked the required inspection question and did not read the marker. The next input was exactly `yes`. Its next tool call read the marker and returned `continuation marker: 293-next-authorized-action`. | Pass for this bounded case. |
| Inherited TDD decisions | An admitted `parse_count(text)` interface and ordinary valid/invalid behaviors were already approved. The delegated next step was fixture inspection. The worker read the fixture in its first tool batch and returned the marker without repeating approval. | Pass for this bounded case. |
| New decision under a restricted host | A later input introduced million-digit untrusted values without an approved resource policy. The host restriction forbade question tools and textual multiple-choice questions. The worker disclosed the plain-question format and explained alternatives, but asked what should happen when input exceeds the proposed limit. | **Fail: the question presupposed an unaccepted limit.** |
| Interview after the focused wording fix | A fresh session read the corrected interview and TDD files with the same uncovered resource decision. It asked: “What maximum number of decimal digits should this parser accept from untrusted input?” | **Fail again: the cap was still assumed. This remains unresolved.** |
| Denial / unanswered decision | The operator rejected the proposed cap and withheld implementation and inspection pending the unresolved policy. The worker reported Q1 unresolved and made no subsequent dependent tool call. | Pass for this bounded stop boundary. |
| First shipped-surface evidence producer | A fresh session received an inherited disposable checkout with a safe localhost server declaration, manufactured data, no ledger, and no execution lock. It created an initial behavior ledger, app-only replay, index and evidence locator in that checkout, then requested approval before freezing. It created no replacement mock, implementation change, commit, new branch or tracker post. | Pass for preparation, inherited ownership and the negative freeze boundary. |
| Chunk completion | A separate fresh session verified the exact synthetic file contents, committed only that file, left `ORDER.md` uncommitted, and returned commit/evidence with the coordinator named as next owner. No PR or real external-service operation was attempted. | Pass for the bounded chunk-return boundary. |

The host-restricted interview result is an observed failure despite the corrected
prose. It is retained under the accepted-failure clause in [design.md](design.md),
not counted as passing and not used to justify a new runtime enforcement system.
The screenshot-derived helper-stop concern was represented as a caller/helper
scenario; no original screenshot was supplied for this implementation replay.

### UI runtime evidence and limits

The manufactured page contained one Details button and two example task names.
The coordinator used the installed browser driver against its declared local
server, then inspected both captures. The exact state checks and browser result:

```text
initial aria-expanded=false and detail hidden: true
first activation aria-expanded=true and detail visible: true
second activation aria-expanded=false and detail hidden: true
CONSOLE_ERRORS []
```

The captures showed the collapsed and expanded states at 1280 by 720 pixels.
They were attached to the fresh worker. The worker retained the inherited branch
and baseline, labeled its ledger `SWEEP IN PROGRESS`, and stopped before adding a
frozen stamp. Its generated replay module passed a syntax check but was not itself
executed; the supplied coordinator browser run exercised the same one-handler
behavior. This is preparation evidence, not a completed production UI revision.

### Astra admission evidence and limits

The actual coordinator's matching local rollout reported `gpt-6-astra` and
`medium`; its session metadata matched the current session identifier. The
read-only adapter probe returned `OK` with 78% headroom. Repository writes were
confined to the selected ticket and owned chunk worktrees. This verified the
current ticket's explicitly admitted execution route. A separate fresh generic
Astra replay was not run. No reviewer eligibility or cross-family ranking is
inferred from that metadata.

## Executable failure and preservation evidence

New CBM command-interface assertions failed against the previous implementation
for absent diagnostics. The hyphenated variant also failed before its fix. A later
live teardown exposed the installed CLI's actual `generation is active` wording;
that exact input was added to the command-interface regression and failed before
its correction. The final live candidate check returned exit 2 with:

```text
stdout: {"status": "unavailable"}
stderr: Codebase Memory has an active-generation conflict; wait for that generation to finish, then retry this checkout. Do not terminate unrelated sessions.
```

The CLI's unsafe close-all suggestion was not emitted by the helper. No unrelated
session was stopped. Missing/unsupported binaries remain distinguishable, while
malformed replies and wrong identities retain their existing fail-closed tests.
A generation conflict did not trigger a generic sandbox escalation or restart.

The disposable clean proof preserved different staged and unstaged content in
both the touched file and an unrelated file. It intentionally failed the post-check
with exit 1, reversed only the cleaner's patch, and checked both snapshots:

```text
intentional post-check exit: 1
index before/after: 1d1da8ddf12150df2cd55e8a006ca9365c1b41dbce1629fe3b9849ed848c594e
worktree before/after: eb77a6ca132c37c234fccf87af33168af0d57836148fa32c35ed0753a50562ff
verdict: staged and unstaged tracked and unrelated baselines preserved; cleaner edit removed
```

The first chunk worker was stopped after launching nested native reviewers.
Scoped stop and verify succeeded; those reviewers were not accepted evidence.
The coordinator used the installed adapter for every accepted Full review.
The operator explicitly approved the **unvalidated Luna** route; depth remained
Full and the benchmark table was not promoted.

## Disposition closure

All 26 dispositions remain governed by [dispositions.md](dispositions.md):

- 01–04, 06–11, 13–15, 19, 21 and 24–25: the named public instruction changes are
  implemented; bounded outcomes and limits are reported above.
- 12: pre-pass capture and scoped rollback are implemented with disposable proof.
- 18: owner-based retry/fallback and bounded diagnostics are implemented, including
  the observed active-generation failure. External session shutdown is excluded.
- 05, 16 and 17: reviewer policy, explicit sanctions and installed-store failure
  policy are retained. Prior exact-scope approval is reused; optional persona
  persistence does not invalidate a completed verdict.
- 20: public hook-enforcement claims are corrected; live installation work remains
  an external follow-up on the originating ticket.
- 22: transport/recovery remains with #263 and forbidden verification legs with
  #288; this change does not absorb them.
- 23: competing external obligations remain subject to actual higher-priority
  instructions; no bundled Sites or deployment changes were made.
- 26: private credential-skill work remains outside this public pack and outstanding
  on the originating ticket. No private skill or configuration was changed.

Scope-ledger disposal remains with #289, and guided manual orders remain with
#292. No separate private or global mutation is implied by this implementation.
