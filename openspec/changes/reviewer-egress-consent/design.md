# Design

The public interface is the literal workflow command. Its frontmatter description
is the catalog summary, `agents/openai.yaml` supplies the user-visible Codex UI
default prompt, and its `## Invocation` section is the full agent contract. All
three surfaces name the same payload and destination, and behavior tests hold their
material semantics together.

The skills remain model-invoked because composition is real: `epic` reaches
`ticket`, and chunked ticket execution reaches `orchestrate`. Instead of disabling
model invocation, the contract distinguishes provenance:

* a literal user command carries consent for the dispatches that command defines;
* automatic or nested activation carries consent only when the literal parent
  command stated the same payload and destination;
* otherwise the agent asks once before the first external dispatch.

The normative egress boundary lives once in each skill's Invocation section.
Frontmatter summarizes it, the OpenAI manifest makes the literal request available
as user text, and the Codex dispatch reference points back to the invoking skill's
contract and supplies the matching escalation rationale. Generic delegation
authority remains separate: it resolves whether a required sub-agent may exist,
while this change resolves whether repository bytes may cross into that worker
invocation.
