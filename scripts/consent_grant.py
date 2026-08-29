"""Canonical source for the worker-egress consent grant surfaces."""

CANONICAL_DISPATCH_GRANT = (
    "The literal invocation already granted this dispatch's transfer of the work\n"
    "order or task prompt plus the repository code, documentation, and UI fidelity\n"
    "evidence rendered from manufactured or synthetic fixtures (tracked in the\n"
    "repository or not, never real user, production, or patient data), so the\n"
    "coordinator does not re-ask. Credentials, secrets, patient data, `.env`, and\n"
    "real database contents are excluded."
)

GENERATED_SURFACES = {
    "ticket coordinator review": {
        "path": "skills/drivers/ticket/references/coordinator-mode.md",
        "before": (
            "   same shared non-blocking rule: neither ever holds up dispatching "
            "the review.\n"
        ),
        "after": "   b. Verify the result yourself",
        "indent": "   ",
    },
    "ticket start review": {
        "path": "skills/drivers/ticket/verbs/start.md",
        "before": "   body as known issues, never silently dropped.\n",
        "after": "    **Profile: hardening.**",
        "indent": "   ",
    },
    "ticket revise review": {
        "path": "skills/drivers/ticket/verbs/revise.md",
        "before": "   code changed.\n",
        "after": "8. **Push and respond.**",
        "indent": "   ",
    },
}

LONG_SAFE_FIXTURE = (
    "UI fidelity evidence rendered from manufactured or synthetic fixtures "
    "(tracked in the repository or not, never real user, production, or patient data)"
)
EXCLUSIONS = (
    "Credentials, secrets, patient data, `.env`, and real database contents are excluded."
)


def required_clauses(safe_fixture, *destinations):
    clauses = {
        "payload prompt": "work order or task prompt",
        "payload repository material": "repository code, documentation, and",
        "safe-fixture qualifier": safe_fixture,
        "exclusions": EXCLUSIONS,
    }
    for index, destination in enumerate(destinations, start=1):
        clauses[f"destination {index}"] = destination
    return clauses


def cross_parent_clauses(safe_fixture):
    clauses = required_clauses(
        safe_fixture,
        "OpenAI's Codex model service",
        "Anthropic's Claude model service",
    )
    clauses["parent scope: Codex UI"] = "Codex UI parent"
    clauses["parent scope: Claude Code"] = "Claude Code parent"
    return clauses


CLAUSE_SURFACES = {
    "ticket skill description": {
        "path": "skills/drivers/ticket/SKILL.md",
        "before": 'description: "',
        "after": '"\n---',
        "clauses": cross_parent_clauses("safe-fixture UI fidelity evidence"),
    },
    "ticket invocation": {
        "path": "skills/drivers/ticket/SKILL.md",
        "before": "## Invocation\n\n",
        "after": "Automatic activation outside an invoked parent workflow",
        "clauses": cross_parent_clauses(LONG_SAFE_FIXTURE),
    },
    "orchestrate skill description": {
        "path": "skills/drivers/orchestrate/SKILL.md",
        "before": 'description: "',
        "after": '"\n---',
        "clauses": cross_parent_clauses("safe-fixture UI fidelity evidence"),
    },
    "orchestrate invocation": {
        "path": "skills/drivers/orchestrate/SKILL.md",
        "before": "## Invocation\n\n",
        "after": "For delegated workflow work",
        "clauses": cross_parent_clauses(LONG_SAFE_FIXTURE),
    },
    "ticket OpenAI prompt": {
        "path": "skills/drivers/ticket/agents/openai.yaml",
        "before": '  default_prompt: "',
        "after": '"\n',
        "clauses": required_clauses(
            LONG_SAFE_FIXTURE, "OpenAI's Codex model service"
        ),
    },
    "orchestrate OpenAI prompt": {
        "path": "skills/drivers/orchestrate/agents/openai.yaml",
        "before": '  default_prompt: "',
        "after": '"\n',
        "clauses": required_clauses(
            LONG_SAFE_FIXTURE, "OpenAI's Codex model service"
        ),
    },
    "Codex UI approval rationale": {
        "path": "skills/drivers/orchestrate/references/dispatch-codex.md",
        "before": "## Approval rationale\n\n",
        "after": "## Worker liveness",
        "clauses": required_clauses(
            LONG_SAFE_FIXTURE, "OpenAI's Codex model service"
        ),
    },
    "Claude-to-Codex approval rationale": {
        "path": "skills/drivers/orchestrate/references/dispatch-codex-from-claude.md",
        "before": "## Approval rationale\n\n",
        "after": "## Review admission",
        "clauses": required_clauses(
            LONG_SAFE_FIXTURE, "OpenAI's Codex model service"
        ),
    },
    "Claude approval rationale": {
        "path": "skills/drivers/orchestrate/references/dispatch-claude.md",
        "before": "## Approval rationale\n\n",
        "after": "## Command surface",
        "clauses": required_clauses(
            LONG_SAFE_FIXTURE, "Anthropic's Claude model service"
        ),
    },
    "ticket triage review": {
        "path": "skills/drivers/ticket/verbs/triage.md",
        "before": "    `/plan-review`.\n",
        "after": "    When the stamped profile is hardening",
        "clauses": required_clauses(LONG_SAFE_FIXTURE),
    },
}

DESCRIPTION_BYTE_CAPS = {
    "ticket skill description": 1024,
    "orchestrate skill description": 1024,
}
