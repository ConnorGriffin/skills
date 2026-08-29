# Scope ledger — consent-grant single source (ticket 258)

## Decisions

- Q1: PR 257 merged before work started; 258 builds against main. Why: no stacking needed. inline
- Q2: hybrid mechanism — generator for the byte-identical copies, clause checker for
  paraphrasing dispatch references and byte-capped yaml descriptions. Why: templating
  cannot honestly produce deliberate paraphrases/trims; a pure checker leaves the
  identical copies hand-synced. → issue (this ticket, 258)

### Risk contract

- Must prevent: silent widening of the consent grant (a surface losing the
  safe-fixture bound or the exclusion sentence while the suite stays green); silent
  incorrect success of the generator (rewriting a surface to something the tests do
  not check); secret exposure; irreversible loss of authoritative data.
- Must recover: none (all failures are test/CI failures with manual fix).
- Accepted failure: generator/checker divergence surfaces as a red test naming the
  surface and clause; fix is manual re-run or edit.
- Unsupported: runtime enforcement of the grant; surfaces outside the ticket and
  orchestrate skills.
- Evidence owed: a test proving every surface carries its required clauses from the
  canonical source; a test proving deleting the safe-fixture qualifier from any
  surface fails; byte-cap check for both agents/openai.yaml descriptions.
- Why: the grant is a prose consent contract with twelve live copies; drift is the
  harm. Disposition: copied into the work order on ticket 258.

## Open questions

(none)

## Spawned tasks

(none)
