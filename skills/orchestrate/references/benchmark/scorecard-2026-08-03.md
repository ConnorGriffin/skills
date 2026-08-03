# Benchmark scorecard (judged by coordinator; scale 1–5)

## Code review (answer key: inverted gate / off-by-one / dropped unstamped test case)
| Model | Catches | False positives | Score | Notes |
|---|---|---|---|---|
| Claude Opus | 3/3 | 0 | 5 | Only full catch; also produced a "checked and correct" list; flagged the #273 fixture anti-pattern |
| Claude Sonnet | 2/3 | 0 | 4.5 | Empirically verified via scratch-copy test run (respected read-only rule); missed dropped test case |
| GPT-5.6-Sol | 2/3 | 0 (one process-level stretch: charter lock-evidence claim) | 4 | Terse, accurate |
| GPT-5.3-Spark | 2/3 | 0 | 4 | Good remediation suggestions; very fast |
| GPT-5.6-Luna | 2/3 | 0 | 4 | Extremely concise, all correct; cheapest catch rate |
| Claude Haiku | 2/3 | 0 | 3.5 | Caught inversion + partial credit on missing-None coverage; MISSED off-by-one |
| GPT-5.6-Terra | 2/3 | 1 (unstamped `_ic` helper claim) | 3.5 | Concise |
| GPT-5.4 | 2/3 | 0 | 3.5 | Clean but no test-drop catch |
| GPT-5.5 | 2/3 | 1 (claimed SyntaxError on legal keyword-only param) | 3 | FP was confidently wrong |
| GPT-5.4-Mini | 1/3 | 0 | 2 | Missed the blatant inverted gate |

## Hermetic implementation (private-app bug-fix replay; truth = the merged fix)
All 7 found the identical one-line core fix and added passing tests; baseline suite errors (20) pre-exist in every worktree.
| Model | Placement vs truth | Tests added | Score | Notes |
|---|---|---|---|---|
| Claude Opus | exact (matched a subtle placement decision in the merged fix) | 71 LOC | 5 | Comment documents the subtlety |
| Claude Sonnet | exact | 73 LOC | 5 | Comment documents the subtlety |
| GPT-5.6-Sol | exact | 57 LOC | 4.5 | Minimal comment |
| GPT-5.6-Terra | exact | 43 LOC | 4.5 | Concise, correct reasoning in comment |
| Claude Haiku | misplaced (subtle behavioral deviation from the merged fix) | 87 LOC | 3.5 | Works but deviates from merged behavior |
| GPT-5.3-Spark | misplaced | ~50 LOC | 3.5 | Same deviation |
| GPT-5.6-Luna | misplaced | 34 LOC | 3 | Same deviation + thinnest tests |

## Contamination note
First-round plan/review runs saw a dirty worktree (fixture-prep agent left the mutated diff applied, 11:29–11:44); all plan+review scores use the r2 reruns on the verified-clean tree. Explore/docs/proto/brainstorm/impl used separate worktrees — unaffected.

## Exploration (agentflow pipeline map; judge spot-checked file:line claims)
| Model | Score | Evidence |
|---|---|---|
| Opus | 5 | All spot-checks verified incl. obscure internals; 20 cited gotchas all correct |
| Sonnet | 5 | Fully verified; deepest balancer/quota mechanics section |
| Sol | 4 | Thorough; one repeated off-by-2 line citation |
| Luna | 4 | Comprehensive; one garbled file path amid otherwise verified claims |
| Haiku | 3 | Fabricated an enum member + line citation (confirmed confabulation) |
| Terra | 3 | Conflated two label constants; thinner merge-gate coverage |
| Spark | 3 | Citations precise but shallowest coverage |

## Plan/spec (private-app design-issue replay; truth = the merged design)
| Model | Score | Evidence |
|---|---|---|
| Terra | 5 | Tightest; correct fail-closed; tests match truth triad |
| Sol | 4.8 | Fully correct + explicit fail-closed; slight over-scaffolding |
| Luna | 4.8 | Correct; concrete acceptance snapshot table; mild repetition |
| GPT-5.4 | 4.7 | Exact placement match; line-level citations all verified |
| Spark | 4 | Correct decisions; hedges + truncated verification command |
| GPT-5.4-Mini | 3.8 | Clean but invents an ungrounded schema-version bump |
| Opus | 3.5 | Tight spec, verified names, but fails OPEN where truth fails closed — load-bearing polarity error |
| GPT-5.5 | 3.5 | Correct semantics; invents an unnecessary new module; most padded |
| Sonnet | 3.5 | Correct fail-closed; visible self-negotiation + one unresolved fork |
| Haiku | 2.5 | Core placement left open; pseudocode mutates a frozen dataclass |

## Prototyping (printable card vs a private repo's locked mockup spec)
| Model | Score | Evidence |
|---|---|---|
| Opus | 5 | Correct card geometry; every lock term reproduced |
| Sol | 5 | Resolved the letter-vs-card tension explicitly with a cut guide |
| Spark | 5 | Found and correctly reused the lock's own CSS system |
| Sonnet | 3 | Print-safe but visually off-lock (wrong ingredient structure, no type voices) |
| Terra | 3 | Close to lock, safe, unremarkable |
| Haiku | 2 | Wrong page geometry for its own gutter math |
| Luna | 1 | No page size, invented UI, printed never-print front-matter on the card |

## Brainstorming (open design question, private app)
| Model | Score | Evidence |
|---|---|---|
| Opus | 5 | 7 mechanism-distinct directions, cheap decisive kill-tests, most novel idea of the whole benchmark |
| Terra | 4.5 | Distinct mechanisms, concrete kill-tests |
| Sonnet | 4 | Structurally distinct; kill-tests lean paper-bound |
| Luna | 4 | Well-grounded in delivery mechanics; concrete placebo designs |
| Sol | 3 | Several kill-tests are expensive cohort studies; generic-ML dressing |
| Haiku | 2.5 | Stock ML moves; slow field-trial kill-tests |
| Spark | 2 | Malformed HTML output; MLOps boilerplate re-skinned |

## Documentation (ADR for a merged agentflow PR)
| Model | Score | Evidence |
|---|---|---|
| Opus | 5 | House style exact; ties to the ADRs the diff itself cites |
| Sol | 5 | Equally disciplined; strong why |
| Haiku | 4 | Correct, no fabrication, thinner |
| Terra | 4 | Correct, slightly generic |
| Luna | 4 | Correct; only one to include Alternatives per house convention |
| Sonnet | 3 | Narrates implementation identifiers (charter violation) |
| Spark | 2 | Fabricated an ADR cross-reference; invented alternatives |

## Final matrix (all areas, coordinator-final scores)
| Area | Opus | Sonnet | Haiku | Sol | Terra | Luna | Spark | 5.5 | 5.4 | 5.4-Mini |
|---|---|---|---|---|---|---|---|---|---|---|
| Exploration | 5 | 5 | 3† | 4 | 3 | 4 | 3 | – | – | – |
| Hermetic impl | 5 | 5 | 3.5 | 4.5 | 4.5 | 3 | 3.5 | – | – | – |
| Plan/spec | 3.5‡ | 3.5 | 2.5 | 4.8 | 5 | 4.8 | 4 | 3.5 | 4.7 | 3.8 |
| Prototyping | 5 | 3 | 2 | 5 | 3 | 1 | 5 | – | – | – |
| Brainstorming | 5 | 4 | 2.5 | 3 | 4.5 | 4 | 2 | – | – | – |
| Documentation | 5 | 3 | 4 | 5 | 4 | 4 | 2 | – | – | – |
| Code review | 5 | 4.5 | 3.5 | 4 | 3.5 | 4 | 4 | 3 | 3.5 | 2 |

† fabricated an enum citation (IntakeRoute.DRAFT) — confirmed confabulation.
‡ judge sub-scores were high, but the spec fails OPEN on unstamped rows where the merged fix fails closed — a load-bearing polarity error demoted it: a convincing spec with a wrong safety decision is worse than a hedged one.

Speed/cost observed: Spark fastest by far; Luna/Terra ~2-3x faster than Sol/Opus; Opus most expensive per task (178k tokens on exploration vs Haiku's 39k).
