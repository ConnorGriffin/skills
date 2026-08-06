---
name: writing-great-skills
description: Write, review, or audit a skill or CLAUDE.md/AGENTS.md against the pointer, load, and pruning vocabulary in references/writing-for-agents.md. Hand-only — invoke with /writing-great-skills to draft or review a skill, or /writing-great-skills doctor to audit the loaded estate.
---

# Writing great skills

User-invoked only — this skill doesn't trigger itself; reach for it by name when
writing a skill, reviewing one, or auditing the estate.

## Writing or reviewing a skill

Read [`references/writing-for-agents.md`](references/writing-for-agents.md) first; it's
the vocabulary this skill applies. Then:

1. **Description first.** Front-load the trigger word, one trigger per branch, cut
   identity the body already carries. If the skill only ever fires by hand, say so in
   the description and write it for a human skimming a list, not for autonomous
   matching.
2. **Place every piece of content on the hierarchy.** In-file step (what runs, in
   order), in-file reference (flat facts consulted on demand), or disclosed reference
   (pushed to a sibling file, reached by a pointer). Run the branching test: if every
   branch needs it, keep it in-file; if only some branches reach it, disclose it.
3. **Give every step a completion criterion** that's checkable and demands real work,
   not "understanding reached."
4. **Reach for a leading word before writing three sentences of restatement.** Positive
   phrasing first; a prohibition only as a hard guardrail, paired with its positive
   target.
5. **Prune before shipping.** One source of truth per meaning, no restating what the
   environment already answers, no no-op sentences. If a sentence changes nothing when
   deleted, delete the whole sentence.

## Doctor

An estate audit verb, report-only — it never edits a skill or a `CLAUDE.md`/`AGENTS.md`,
it reports findings for a human to act on. Invoke with `/writing-great-skills doctor`.

Six passes: measure the always-loaded surface (the `CLAUDE.md`/`AGENTS.md` import chain,
every installed skill's description, chars and estimated tokens per component and in
total); sweep descriptions for synonym-stuffed triggers, mechanism the body already
carries, hand-only skills that read like autonomous triggers, and cross-skill trigger
overlap; sweep the always-loaded chain for duplicated rules, conditional sections that
belong behind a pointer, stacked negations, no-ops, and sediment; verify every finding
against a direct grep or read before reporting it — a finding without quoted evidence is
dropped; report ranked findings worst first, accuracy risks above token costs, with
estimated recoverable tokens, fixes left as operator judgment calls; and refresh by
re-fetching the upstream source and diffing it against the adapted reference, flagging
drift for a human rewrite rather than auto-updating.

Full step detail, including exact file locations to walk and the refresh diff mechanics,
is in [`references/doctor.md`](references/doctor.md).
