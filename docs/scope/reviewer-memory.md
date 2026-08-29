# Scope ledger — #197 per-repo reviewer memory

Route: scope → interview mode (plan exists in operator's head, untested).

## Decisions

- Bedroom-scale assurance: no validator scripts, no hardening ceremony; iterate on breakage. Why: single operator, stated directly. (inline)
- Work-quiet: nothing repo-visible in work repos; store lives outside the target repo. Why: operator does not share workflow with teammates. (inline)
- Store format precedent: stdlib JSONL append + reader, per ~/.config/ticket/{telemetry,claims}.jsonl. Why: matches pack's no-dependency portability rule. (inline)
- Q1: storage is plain dotconfig (~/.config/…), no git sync; revisit dotfiles-repo home only if backup wanted. (inline)
- Q2: this ticket closes the slicing loop — finalize's record feeds the store and triage reads it instead of only the hand anchor table. (inline)
- Q3: randomized-agent routing experiment is its own later issue. (→ issue)
- Q5: missing/malformed/unreadable store STOPS the verb — loud failure, operator repairs. Memory must never silently not-learn (sandboxed-agent worry). (inline)

- Q4: hybrid write path — code-review completion appends raw findings as one JSONL line; finalize appends the slicing record (already computed); an operator-run batch distill (~every 5 tickets) reads raw lines + GitHub artifacts (work-order comments, scope ledgers) and maintains the OKF bundle. Why: code-review findings persist nowhere today (PR #249 carries zero review comments), so without raw capture they are lost; per-ticket session cost stays near zero. (inline)
- Q6/Q7: store shape is a per-repo OKF bundle under ~/.config/reviewer-memory/<normalized-repo>/ — markdown + YAML frontmatter, index.md per repo as the capped digest, linked pages for depth. Consumers (triage, plan-review, code-review) receive a pointer to index.md and traverse. Raw JSONL capture sits beside the bundle. (inline)
- Repo key: normalized remote (github.com/org/repo), same normalization ticket.py resolve_repo uses. Default, no user decision needed. (inline)

### Risk contract

- Must prevent: silent not-learning (a consumer that cannot read/write the store proceeding quietly — Q5: stop loudly instead); store content leaking into target-repo commits or PR/issue comments at work (work-quiet rule); secret exposure via captured findings (store is local dotconfig only, never posted).
- Must recover: none automatic.
- Accepted failure: a mediocre or stale distill digest — consequence is weaker prep, fixed by re-running distill; a lost raw line if a session dies mid-append — consequence is one lesson lost.
- Unsupported: multi-operator/shared stores; cross-machine sync (revisit as dotfiles-repo home later); cross-repo learning (per-repo default).
- Evidence owed: store script's public commands (append, record-read, ensure/path) get unittest coverage per repo test convention; the stop-loudly behavior on missing/malformed store is the one invariant that gets a pinned test.
- Why: single-operator tool, worst credible outcome is quiet non-learning or workplace noise. Disposition: inline, copied into the work order.

## Open questions

- Storage home (dotconfig vs private git repo)
- Slicing-anchor feedback loop in scope?
- Randomized-agent routing extension in scope?
- Write path (who records, when)
- Read path (how triage/reviewers consume)
- Keying (request type / module / change type)
- Epic vs one chunked ticket

## Spawned tasks

(none)
