# Design

The public interface is the literal workflow command. Its frontmatter description
is the catalog summary, `agents/openai.yaml` supplies the user-visible Codex UI
default prompt, and its `## Invocation` section is the full agent contract. All
three surfaces name the same material fields, and behavior tests hold those fields
together without demanding byte-identical prose.

The skills remain model-invoked because composition is real: `epic` reaches
`ticket`, and chunked ticket execution reaches `orchestrate`. Intentional user
invocation covers every mandatory dispatch the workflow routes, including nested
review and nested Orchestrate work. Automatic activation outside an invoked parent
workflow asks once before its first external dispatch. No parser, provenance
artifact, approval state machine, or byte filter is introduced.

The normative egress boundary lives once in each skill's Invocation section.
Frontmatter summarizes it, the OpenAI manifest makes the literal request available
as user text, and the Codex dispatch reference points back to the invoking skill's
contract and supplies the matching adapter-specific rationale. Generic delegation
authority remains separate: it resolves whether a required sub-agent may exist,
while this change resolves whether repository bytes may cross into that worker
invocation. The contract declares authority for a guardian to match; it does not
filter prompt bytes or alter platform approval policy.
