# Writing for agents — negation and the cache/environment distinction

Adapted from Matt Pocock's writing-for-agents (github.com/mattpocock/skills), fetched 2026-08-06.

This skill's own [`SKILL.md`](../SKILL.md) and [`GLOSSARY.md`](../GLOSSARY.md) already
cover invocation, the two loads, the information hierarchy, completion criteria, leading
words, and pruning's single-source-of-truth/relevance/sediment/no-op cluster — this file
holds only the two upstream levers that aren't in either: negation, and the distinction
between a cache and the environment it copies.

## Negation

Telling the agent what *not* to do puts the forbidden behavior directly in context and
makes it more available, not less — "don't use em-dashes" activates em-dashes. State the
positive target instead ("use short sentences and parens for asides") so the banned
behavior never gets named.

Keep a bare prohibition only as a hard guardrail with no honest positive phrasing, and
even then pair it with the positive target so the agent has somewhere to put its
attention. A document with several stacked prohibitions and no positive counterpart for
any of them is a document steering by what to avoid instead of what to do — flag it.

## Cache vs. environment

The environment — `package.json`, config files, `--help` output, the directory layout —
is already a source of truth. A document that restates it is a cache, and a cache only
earns its keep when the lookup it replaces is expensive. Document the unwritten
convention or the gotcha the environment can't confess; skip the one-command lookup the
agent can just run.

A line that just repeats what `--help`, a manifest file, or a directory listing already
says is not **relevance**'s failure mode (it may well still be true) — it's a cache with
no expensive lookup behind it, and it should go.
