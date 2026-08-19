#!/usr/bin/env python3
"""Validate public skill structure and catch common disclosure mistakes."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CATEGORIES = {"workflows", "drivers", "tools"}
EXPECTED = {
    "workflows/scope",
    "workflows/review",
    "drivers/wayfinder",
    "drivers/implement",
    "drivers/openspec-adopt",
    "drivers/ui-craft",
    "drivers/orchestrate",
    "drivers/ticket",
    "tools/cbm-onboard",
    "tools/ci-design",
    "tools/code-review",
    "tools/codebase-design",
    "tools/domain-modeling",
    "tools/drive-local-webapp",
    "tools/handoff",
    "tools/persona-review",
    "tools/plan-review",
    "tools/pr-body",
    "tools/preflight",
    "tools/prototype",
    "tools/research",
    "tools/say-less",
    "tools/spin-worktree",
    "tools/tdd",
    "tools/writing-for-agents",
}
EVIDENCE = ROOT / "docs" / "evidence"
CONTRACT = EVIDENCE / "contract-v2.json"
PROVENANCE = EVIDENCE / "contract-v2.provenance.json"
CONTRACT_SHA256 = "6c7a5a6d4d44a94466b87a2206f2fc5660bcaf096dde8c39eaf915d08781f3de"
CONTRACT_PROVENANCE = {
    "upstream_repository": "ConnorGriffin/agentflow",
    "upstream_commit": "98d67d3b4a3f72d243e4765075d4a6728f6c46d1",
    "source_path": "docs/evidence/contract-v2.json",
    "source_git_blob": "1311a40215442b1142f1d1f165160c5f7eaf51ca",
    "file_sha256": CONTRACT_SHA256,
}
POSITIVE_EXAMPLES = EVIDENCE / "examples" / "positive.json"
NEGATIVE_EXAMPLES = EVIDENCE / "examples" / "negative.json"
FORBIDDEN = (
    re.compile("/" + "Users/"),
    re.compile("~/" + "Code/" + "ConnorGriffin"),
    re.compile("Connor's " + r"(?:real browser|rule)"),
    re.compile("nt" + "fy", re.IGNORECASE),
    re.compile("t" + "connect", re.IGNORECASE),
    re.compile(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    # Employer markers. Working tree only: history predating this guard keeps whatever
    # it already published, and adding these to HISTORY_PATTERN would fail every run.
    re.compile("tan" + "ium", re.IGNORECASE),
    re.compile(r"\bgit" + r"\.corp\b", re.IGNORECASE),
    re.compile(r"\b" + "DEV" + r"OPS-\d+\b"),
    re.compile(r"\b(?:" + "CHG" + "|" + "INC" + r")\d{6,}\b"),
    re.compile("service" + "-now", re.IGNORECASE),
    re.compile("j" + r"ira\.corp", re.IGNORECASE),
    re.compile(r"~/\.config/" + "j" + "ira-ticket/"),
)
PERSONA_REVIEW_ALLOWLIST = {
    "SKILL.md",
    "agents/openai.yaml",
}
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HISTORY_PATTERN = "|".join(
    (
        "/" + "Users/",
        "~/" + "Code/" + "ConnorGriffin",
        "Connor's " + "(real browser|rule)",
        "nt" + "fy",
        "t" + "connect",
        "BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY",
        "gh[pousr]_[A-Za-z0-9_]{20,}",
        "AKIA[0-9A-Z]{16}",
        "sk-[A-Za-z0-9]{20,}",
        "xox[baprs]-[A-Za-z0-9-]{10,}",
    )
)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def tracked_files(errors: list[str]) -> list[Path]:
    """Files the repository would publish: tracked plus staged, never ignored ones.

    Walking the filesystem instead would let a gitignored local artifact (a build
    cache, a screenshot, .DS_Store) fail validation and block a push.
    """
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--exclude-standard"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if listing.returncode != 0:
        fail(errors, f"file listing failed: {listing.stderr.decode().strip()}")
        return []
    paths = []
    for entry in listing.stdout.decode().split("\0"):
        if not entry:
            continue
        path = ROOT / entry
        if path.is_file() and "node_modules" not in path.parts:
            paths.append(path)
    return paths


def validate_frontmatter(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        fail(errors, f"{path.relative_to(ROOT)}: missing YAML frontmatter")
        return
    fields = {
        line.split(":", 1)[0].strip()
        for line in match.group(1).splitlines()
        if ":" in line
    }
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        field, _, value = line.partition(":")
        field = field.strip()
        value = value.strip()
        quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'"
        if not quoted and ": " in value:
            fail(
                errors,
                f"{path.relative_to(ROOT)}: {field} value contains ': ' unquoted; "
                "wrap the value in double quotes",
            )
    required = {"name", "description"}
    allowed = required | {"disable-model-invocation"}
    if fields < required or fields - allowed:
        fail(
            errors,
            f"{path.relative_to(ROOT)}: frontmatter must contain name and description, "
            "plus an optional disable-model-invocation",
        )
    if "disable-model-invocation" in fields:
        value_match = re.search(
            r"^disable-model-invocation:\s*(.+)$", match.group(1), re.MULTILINE
        )
        if not value_match or value_match.group(1).strip() != "true":
            fail(
                errors,
                f"{path.relative_to(ROOT)}: disable-model-invocation must be true when present",
            )
    name_match = re.search(r"^name:\s*(.+)$", match.group(1), re.MULTILINE)
    if not name_match or name_match.group(1).strip() != path.parent.name:
        fail(errors, f"{path.relative_to(ROOT)}: name must match directory")
    if len(text.splitlines()) > 500:
        fail(errors, f"{path.relative_to(ROOT)}: exceeds 500 lines")


def validate_links(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for target in LINK.findall(text):
        target = target.split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        resolved = (path.parent / target).resolve()
        if ROOT not in resolved.parents and resolved != ROOT:
            fail(errors, f"{path.relative_to(ROOT)}: link escapes repository: {target}")
        elif not resolved.exists():
            fail(errors, f"{path.relative_to(ROOT)}: broken link: {target}")


def validate_persona_review_allowlist(errors: list[str]) -> None:
    skill_dir = SKILLS / "tools" / "persona-review"
    if not skill_dir.exists():
        return
    for path in skill_dir.rglob("*"):
        if path.is_file():
            relative = path.relative_to(skill_dir).as_posix()
            if relative not in PERSONA_REVIEW_ALLOWLIST:
                fail(
                    errors,
                    f"skills/tools/persona-review: file not on the allowlist: {relative}",
                )


def validate_evidence_contract(errors: list[str]) -> None:
    if not CONTRACT.is_file():
        fail(errors, "docs/evidence/contract-v2.json: missing vendored contract")
    elif hashlib.sha256(CONTRACT.read_bytes()).hexdigest() != CONTRACT_SHA256:
        fail(errors, "docs/evidence/contract-v2.json: bytes differ from pinned upstream blob")

    if not PROVENANCE.is_file():
        fail(errors, "docs/evidence/contract-v2.provenance.json: missing provenance")
        return
    try:
        provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail(errors, f"docs/evidence/contract-v2.provenance.json: invalid JSON: {error.msg}")
        return
    if provenance != CONTRACT_PROVENANCE:
        fail(errors, "docs/evidence/contract-v2.provenance.json: does not match pinned upstream facts")


def evidence_json(path: Path, errors: list[str]) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(errors, f"{path.relative_to(ROOT)}: missing")
    except json.JSONDecodeError as error:
        fail(errors, f"{path.relative_to(ROOT)}: invalid JSON: {error.msg}")
    return None


EVIDENCE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,127}$")
EVIDENCE_DIGEST = re.compile(r"^[a-f0-9]{32,128}$")
EVIDENCE_SHA = re.compile(r"^[a-f0-9]{40,64}$")
WORKING_TREE_SUBJECT = re.compile(
    r"^base:([a-f0-9]{40,64})/head:([a-f0-9]{40,64})$"
)
EVIDENCE_FORBIDDEN_FIELDS = frozenset({
    "prompt", "prompts", "transcript", "transcripts", "source_body",
    "source_bodies", "secret", "secrets", "finding", "summary", "summaries",
    "grounding", "payload", "payloads", "excerpt", "body", "text", "raw",
    "metadata", "reason",
})
EVIDENCE_PRODUCER_KINDS = frozenset({
    "claim", "criterion", "decision", "decline", "delegation", "disposition",
    "finding", "fix", "objection", "review_action", "revision", "settlement",
    "slice", "verification", "verdict",
})
EVIDENCE_LINEAGE_MATRIX = {
    "derives_from": (
        EVIDENCE_PRODUCER_KINDS,
        EVIDENCE_PRODUCER_KINDS | {"failure_observation"},
    ),
    "governs": (
        frozenset({"decision", "disposition", "verdict"}),
        frozenset({"claim", "criterion", "delegation", "slice", "finding",
                   "review_action", "fix", "verification"}),
    ),
    "addresses": (
        frozenset({"finding", "review_action", "fix"}),
        frozenset({"failure_observation", "finding", "objection"}),
    ),
    "delegates": (
        frozenset({"delegation", "slice"}),
        frozenset({"claim", "criterion", "decision", "delegation"}),
    ),
    "implements": (
        frozenset({"revision", "fix"}),
        frozenset({"criterion", "decision", "finding", "review_action"}),
    ),
    "verifies": (
        frozenset({"verification", "verdict"}),
        frozenset({"claim", "criterion", "decision", "finding", "fix",
                   "verification"}),
    ),
    "refutes": (
        frozenset({"verification", "verdict"}),
        frozenset({"claim", "criterion", "decision", "finding", "fix",
                   "verification"}),
    ),
    "revises": (
        frozenset({"revision", "decision", "disposition", "objection", "fix"}),
        frozenset({"claim", "criterion", "decision", "disposition", "objection",
                   "revision", "finding", "fix"}),
    ),
    "settles": (
        frozenset({"settlement"}),
        frozenset({"claim", "decision", "disposition", "verdict", "fix",
                   "verification"}),
    ),
}
EVIDENCE_REQUIRED_RELATION = {
    "fix": "addresses",
    "settlement": "settles",
    "delegation": "delegates",
    "slice": "derives_from",
}


def is_evidence_id(value: object) -> bool:
    return isinstance(value, str) and bool(EVIDENCE_ID.fullmatch(value))


def is_evidence_digest(value: object) -> bool:
    return isinstance(value, str) and bool(EVIDENCE_DIGEST.fullmatch(value))


def is_evidence_sha(value: object) -> bool:
    return isinstance(value, str) and bool(EVIDENCE_SHA.fullmatch(value))


def has_forbidden_evidence_field(value: object) -> bool:
    if isinstance(value, dict):
        return bool(set(value) & EVIDENCE_FORBIDDEN_FIELDS) or any(
            has_forbidden_evidence_field(item) for item in value.values()
        )
    if isinstance(value, list):
        return any(has_forbidden_evidence_field(item) for item in value)
    return False


def evidence_strings(
    value: dict[str, object],
    names: set[str],
    prefix: str,
    errors: list[str],
) -> bool:
    valid = True
    for name in names:
        if not isinstance(value.get(name), str) or not value[name]:
            fail(errors, f"{prefix}: {name} must be a nonempty string")
            valid = False
    return valid


def validate_evidence_subject(
    subject: object,
    prefix: str,
    errors: list[str],
    snapshots: dict[str, set[str]],
    snapshot_counts: dict[str, int],
) -> str | None:
    if not isinstance(subject, dict):
        fail(errors, f"{prefix}: subject must be an object")
        return None
    subject_kind = subject.get("subject_kind")
    expected = (
        {"subject_kind", "subject", "revision"}
        if subject_kind == "review"
        else {"subject_kind", "subject", "revision", "locator", "content_digest"}
        if subject_kind in {"issue", "document"}
        else set()
    )
    if not isinstance(subject_kind, str) or subject_kind not in {
        "review",
        "issue",
        "document",
    }:
        fail(errors, f"{prefix}: invalid subject_kind")
        return None
    if set(subject) != expected:
        fail(errors, f"{prefix}: subject fields are not closed")
        return subject_kind
    if not evidence_strings(subject, expected, prefix, errors):
        return subject_kind
    if subject_kind == "review":
        if not is_evidence_id(subject["subject"]):
            fail(errors, f"{prefix}: subject must follow the upstream ID grammar")
        if not is_evidence_sha(subject["revision"]):
            fail(errors, f"{prefix}: review revision must be 40-64 lowercase hex")
            return subject_kind
        match = WORKING_TREE_SUBJECT.fullmatch(subject["subject"])
        if match:
            if len(subject["revision"]) != 64:
                fail(errors, f"{prefix}: working-tree snapshot revision must be SHA-256")
            snapshots.setdefault(subject["subject"], set()).add(subject["revision"])
            snapshot_counts[subject["subject"]] = (
                snapshot_counts.get(subject["subject"], 0) + 1
            )
        return subject_kind
    for name in ("subject", "revision", "locator"):
        if not is_evidence_id(subject[name]):
            fail(errors, f"{prefix}: {name} must follow the upstream ID grammar")
    if not is_evidence_digest(subject["content_digest"]):
        fail(errors, f"{prefix}: content_digest must be raw lowercase hex")
    return subject_kind


def validate_evidence_source(
    source: object,
    source_fields: set[str],
    prefix: str,
    errors: list[str],
    snapshot_subject: object,
) -> str | None:
    if not isinstance(source, dict):
        fail(errors, f"{prefix}: source must be an object")
        return None
    if set(source) != source_fields:
        fail(errors, f"{prefix}: source fields are not closed")
        return None
    if not evidence_strings(source, source_fields, prefix, errors):
        return None
    for name in (
        "authority_kind",
        "repository",
        "locator",
        "content_hash_algorithm",
        "scope",
    ):
        if not is_evidence_id(source[name]):
            fail(errors, f"{prefix}: source {name} must follow the upstream ID grammar")
    if not is_evidence_digest(source["content_hash"]):
        fail(errors, f"{prefix}: source content_hash must be raw lowercase hex")
    authority_kind = source["authority_kind"]
    if authority_kind == "github":
        if not is_evidence_sha(source["revision"]):
            fail(errors, f"{prefix}: github source revision must be 40-64 lowercase hex")
    elif authority_kind == "repository":
        if source["revision"] != f"sha256:{source['content_hash']}":
            fail(errors, f"{prefix}: repository source revision must bind content_hash")
    else:
        fail(errors, f"{prefix}: invalid source authority_kind")
    if isinstance(snapshot_subject, str):
        match = WORKING_TREE_SUBJECT.fullmatch(snapshot_subject)
        if match and source["revision"] != match.group(2):
            fail(errors, f"{prefix}: snapshot head must match source revision")
    return source["repository"] if isinstance(source["repository"], str) else None


def validate_failure_facts(
    failure: object,
    failure_classes: set[str],
    states: set[str],
    prefix: str,
    errors: list[str],
) -> str | None:
    if not isinstance(failure, dict):
        fail(errors, f"{prefix}: failure must be an object")
        return None
    failure_class = failure.get("failure_class")
    base = {
        "failure_class",
        "validation_state",
        "signature_digest",
        "normalizer_version",
    }
    expected = (
        base | {"reviewed_parent_revision", "fixer_revision"}
        if failure_class == "fix_introduced_defect"
        else base
    )
    if set(failure) != expected:
        fail(errors, f"{prefix}: failure fields are not closed")
        return failure_class if isinstance(failure_class, str) else None
    if not evidence_strings(failure, expected, prefix, errors):
        return failure_class if isinstance(failure_class, str) else None
    if failure_class not in failure_classes:
        fail(errors, f"{prefix}: invalid failure_class")
    if failure["validation_state"] not in states:
        fail(errors, f"{prefix}: invalid validation_state")
    if not is_evidence_digest(failure["signature_digest"]):
        fail(errors, f"{prefix}: signature_digest must be raw lowercase hex")
    if not is_evidence_id(failure["normalizer_version"]):
        fail(errors, f"{prefix}: invalid normalizer_version")
    for name in ("reviewed_parent_revision", "fixer_revision"):
        if name in failure and not is_evidence_sha(failure[name]):
            fail(errors, f"{prefix}: {name} must be 40-64 lowercase hex")
    return failure_class if isinstance(failure_class, str) else None


def validate_producer_facts(
    producer: object,
    producer_kinds: set[str],
    states: set[str],
    actions: set[str],
    prefix: str,
    errors: list[str],
) -> str | None:
    if not isinstance(producer, dict):
        fail(errors, f"{prefix}: producer must be an object")
        return None
    producer_kind = producer.get("producer_kind")
    base = {
        "producer_kind",
        "fact_digest",
        "normalizer_version",
        "validation_state",
    }
    expected = base | ({"review_action"} if producer_kind == "review_action" else set())
    if set(producer) != expected:
        fail(errors, f"{prefix}: producer fields or review_action are not closed")
        return producer_kind if isinstance(producer_kind, str) else None
    if not evidence_strings(producer, expected, prefix, errors):
        return producer_kind if isinstance(producer_kind, str) else None
    if producer_kind not in producer_kinds:
        fail(errors, f"{prefix}: invalid producer_kind")
    if producer["validation_state"] not in states:
        fail(errors, f"{prefix}: invalid validation_state")
    if not is_evidence_digest(producer["fact_digest"]):
        fail(errors, f"{prefix}: fact_digest must be raw lowercase hex")
    if not is_evidence_id(producer["normalizer_version"]):
        fail(errors, f"{prefix}: invalid normalizer_version")
    if producer_kind == "review_action" and producer["review_action"] not in actions:
        fail(errors, f"{prefix}: invalid review_action")
    return producer_kind if isinstance(producer_kind, str) else None


def validate_evidence_links(
    links: object,
    producer_kind: str | None,
    link_fields: set[str],
    relations: set[str],
    max_links: int,
    prefix: str,
    errors: list[str],
) -> list[tuple[str, str]]:
    if not isinstance(links, list):
        fail(errors, f"{prefix}: links must be a list")
        return []
    if len(links) > max_links:
        fail(errors, f"{prefix}: lineage exceeds the upstream bound")
    valid_links: list[tuple[str, str]] = []
    pairs: set[tuple[str, str]] = set()
    for position, link in enumerate(links):
        if not isinstance(link, dict) or set(link) != link_fields:
            fail(errors, f"{prefix}: link fields or relation are invalid")
            continue
        ordinal = link.get("ordinal")
        relation = link.get("relation")
        target = link.get("target_event_id")
        if isinstance(ordinal, bool) or not isinstance(ordinal, int):
            fail(errors, f"{prefix}: link ordinal must be an integer")
        elif ordinal != position or not 0 <= ordinal <= 31:
            fail(errors, f"{prefix}: lineage links must have dense ordinals")
        if not isinstance(relation, str) or not relation:
            fail(errors, f"{prefix}: link fields or relation are invalid")
            continue
        if relation not in relations:
            fail(errors, f"{prefix}: invalid lineage relation")
            continue
        if (
            producer_kind is None
            or producer_kind not in EVIDENCE_LINEAGE_MATRIX[relation][0]
        ):
            fail(errors, f"{prefix}: illegal lineage direction")
        if not is_evidence_id(target):
            fail(errors, f"{prefix}: target_event_id must follow the upstream ID grammar")
            continue
        pair = (relation, target)
        if pair in pairs:
            fail(errors, f"{prefix}: lineage links must be unique")
        pairs.add(pair)
        valid_links.append(pair)
    required = EVIDENCE_REQUIRED_RELATION.get(producer_kind)
    if required is not None and all(relation != required for relation, _ in valid_links):
        fail(errors, f"{prefix}: required lineage is missing for {producer_kind}")
    return valid_links


def validate_evidence_examples(errors: list[str]) -> None:
    contract = evidence_json(CONTRACT, errors)
    positive = evidence_json(POSITIVE_EXAMPLES, errors)
    negative = evidence_json(NEGATIVE_EXAMPLES, errors)
    if (
        not isinstance(contract, dict)
        or not isinstance(positive, dict)
        or not isinstance(negative, dict)
    ):
        return
    required_contract_fields = {
        "producer_envelope_fields",
        "producer_fact_fields",
        "source_fields",
        "review_subject_fields",
        "content_subject_fields",
        "producer_kinds",
        "validation_states",
        "review_actions",
        "lineage_relations",
        "link_fields",
        "max_links",
        "failure_envelope_fields",
        "failure_fact_fields",
        "failure_classes",
    }
    if not required_contract_fields <= set(contract):
        fail(errors, "docs/evidence/contract-v2.json: incomplete manifest")
        return
    observations = positive.get("observations")
    if (
        set(positive) != {"observations"}
        or not isinstance(observations, list)
        or not observations
    ):
        fail(errors, "docs/evidence/examples/positive.json: contains observations only")
        return

    producer_fields = set(contract["producer_envelope_fields"])
    source_fields = set(contract["source_fields"])
    producer_kinds = set(contract["producer_kinds"])
    states = set(contract["validation_states"])
    actions = set(contract["review_actions"])
    relations = set(contract["lineage_relations"])
    failure_fields = set(contract["failure_envelope_fields"])
    failure_classes = set(contract["failure_classes"])
    link_fields = set(contract["link_fields"])
    max_links = contract["max_links"]

    observation_ids = [
        item.get("observation_id")
        for item in observations
        if isinstance(item, dict)
    ]
    string_ids = [item for item in observation_ids if isinstance(item, str)]
    if len(string_ids) != len(set(string_ids)):
        fail(errors, "docs/evidence/examples/positive.json: duplicate observation_id")

    snapshots: dict[str, set[str]] = {}
    snapshot_counts: dict[str, int] = {}
    seen_events: dict[str, tuple[str, str | None]] = {}
    seen_producer_kinds: set[str] = set()
    seen_failure_classes: set[str] = set()

    for index, observation in enumerate(observations):
        prefix = f"docs/evidence/examples/positive.json: observation {index}"
        if not isinstance(observation, dict):
            fail(errors, f"{prefix}: observation must be an object")
            continue
        if has_forbidden_evidence_field(observation):
            fail(errors, f"{prefix}: contains a prohibited captured-content field")
        observation_id = observation.get("observation_id")
        if not is_evidence_id(observation_id):
            fail(errors, f"{prefix}: observation_id must follow the upstream ID grammar")
        observed_at = observation.get("observed_at")
        if (
            isinstance(observed_at, bool)
            or not isinstance(observed_at, int)
            or observed_at < 0
        ):
            fail(errors, f"{prefix}: observed_at must be a nonnegative integer")

        envelope_kind = observation.get("envelope_kind")
        expected_fields = (
            failure_fields
            if envelope_kind == "failure_observation"
            else producer_fields
            if envelope_kind == "producer_fact"
            else set()
        )
        if envelope_kind not in {"failure_observation", "producer_fact"}:
            fail(errors, f"{prefix}: invalid envelope_kind")
            continue
        if set(observation) != expected_fields:
            fail(errors, f"{prefix}: {envelope_kind} envelope fields are not closed")
            continue

        subject = observation["subject"]
        validate_evidence_subject(
            subject, prefix, errors, snapshots, snapshot_counts
        )
        subject_name = subject.get("subject") if isinstance(subject, dict) else None
        repository = validate_evidence_source(
            observation["source"], source_fields, prefix, errors, subject_name
        )

        event_kind: str | None
        links: list[tuple[str, str]] = []
        if envelope_kind == "failure_observation":
            failure_class = validate_failure_facts(
                observation["failure"], failure_classes, states, prefix, errors
            )
            event_kind = "failure_observation"
            if failure_class in failure_classes:
                seen_failure_classes.add(failure_class)
        else:
            producer_kind = validate_producer_facts(
                observation["producer"],
                producer_kinds,
                states,
                actions,
                prefix,
                errors,
            )
            event_kind = producer_kind
            if producer_kind in producer_kinds:
                seen_producer_kinds.add(producer_kind)
            links = validate_evidence_links(
                observation["links"],
                producer_kind,
                link_fields,
                relations,
                max_links,
                prefix,
                errors,
            )

        for relation, target in links:
            target_event = seen_events.get(target)
            if target_event is None:
                fail(errors, f"{prefix}: lineage must target an earlier observation")
                continue
            target_kind, target_repository = target_event
            if repository is not None and target_repository != repository:
                fail(errors, f"{prefix}: lineage target belongs to another repository")
            if target_kind not in EVIDENCE_LINEAGE_MATRIX[relation][1]:
                fail(errors, f"{prefix}: illegal lineage direction")
        if is_evidence_id(observation_id) and event_kind is not None:
            seen_events[observation_id] = (event_kind, repository)

    if seen_producer_kinds != producer_kinds:
        fail(errors, "docs/evidence/examples/positive.json: producer kind matrix is incomplete")
    if seen_failure_classes != failure_classes:
        fail(errors, "docs/evidence/examples/positive.json: failure class matrix is incomplete")
    if any(
        snapshot_counts[subject] != len(revisions)
        for subject, revisions in snapshots.items()
    ) or not any(len(revisions) > 1 for revisions in snapshots.values()):
        fail(
            errors,
            "docs/evidence/examples/positive.json: needs distinct dirty snapshots at one HEAD",
        )

    invalid = negative.get("invalid_observations")
    invalid_failures = negative.get("invalid_failures")
    prohibited = {"candidate", "proposal", "promotion", "lesson"}
    prohibited_failures = {"candidate", "policy_state", "worker_failure"}
    if (
        set(negative) != {"invalid_observations", "invalid_failures"}
        or not isinstance(invalid, list)
        or not isinstance(invalid_failures, list)
    ):
        fail(errors, "docs/evidence/examples/negative.json: invalid fixture shape")
        return
    for fixture in invalid:
        if (
            not isinstance(fixture, dict)
            or not isinstance(fixture.get("producer_kind"), str)
            or fixture["producer_kind"] not in prohibited
        ):
            fail(
                errors,
                "docs/evidence/examples/negative.json: fixture does not reject a prohibited kind",
            )
            continue
        if fixture["producer_kind"] in producer_kinds:
            fail(
                errors,
                "docs/evidence/examples/negative.json: prohibited kind is admitted",
            )
        if (
            fixture["producer_kind"] == "lesson"
            and fixture.get("validation_state") != "unvalidated"
        ):
            fail(
                errors,
                "docs/evidence/examples/negative.json: lesson fixture must prove unvalidated rejection",
            )
    for fixture in invalid_failures:
        if (
            not isinstance(fixture, dict)
            or not isinstance(fixture.get("failure_class"), str)
            or fixture["failure_class"] not in prohibited_failures
        ):
            fail(
                errors,
                "docs/evidence/examples/negative.json: fixture does not reject a prohibited failure class",
            )
        elif fixture["failure_class"] in failure_classes:
            fail(
                errors,
                "docs/evidence/examples/negative.json: prohibited failure class is admitted",
            )


def validate_reachable_history(errors: list[str]) -> None:
    commits = subprocess.run(
        ["git", "rev-list", "--all"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if commits.returncode != 0:
        fail(errors, f"history scan failed: {commits.stderr.strip()}")
        return
    for revision in commits.stdout.splitlines():
        scan = subprocess.run(
            ["git", "grep", "-I", "-q", "-E", HISTORY_PATTERN, revision, "--", "."],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
        if scan.returncode == 0:
            fail(errors, f"reachable history contains a forbidden value at {revision}")
        elif scan.returncode != 1:
            fail(errors, f"history content scan failed at {revision}")

    objects = subprocess.run(
        ["git", "rev-list", "--objects", "--all"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if objects.returncode != 0:
        fail(errors, f"history path scan failed: {objects.stderr.strip()}")
        return
    for line in objects.stdout.splitlines():
        _, separator, object_path = line.partition(" ")
        if not separator:
            continue
        for pattern in FORBIDDEN:
            if pattern.search(object_path):
                fail(errors, f"reachable history contains a forbidden path")


def discover_skills(errors: list[str]) -> set[str]:
    actual: set[str] = set()
    for entry in SKILLS.iterdir():
        if entry.is_file():
            fail(errors, f"skills/{entry.name}: file directly under skills/, not a category")
            continue
        if entry.name not in CATEGORIES:
            fail(errors, f"skills/{entry.name}: directory is not a recognized category")
            continue
        for skill_dir in entry.iterdir():
            if skill_dir.is_dir():
                actual.add(f"{entry.name}/{skill_dir.name}")
    return actual


def main() -> int:
    errors: list[str] = []
    actual = discover_skills(errors)
    if actual != EXPECTED:
        fail(errors, f"skills: expected {sorted(EXPECTED)}, found {sorted(actual)}")

    tracked_candidates = tracked_files(errors)
    for path in tracked_candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            fail(errors, f"{path.relative_to(ROOT)}: unexpected binary file")
            continue
        for pattern in FORBIDDEN:
            if pattern.search(text):
                fail(errors, f"{path.relative_to(ROOT)}: forbidden pattern {pattern.pattern!r}")
        if path.suffix == ".md":
            validate_links(path, errors)

    for skill in sorted(EXPECTED):
        skill_file = SKILLS / skill / "SKILL.md"
        if not skill_file.exists():
            fail(errors, f"skills/{skill}: missing SKILL.md")
            continue
        validate_frontmatter(skill_file, errors)
        metadata = SKILLS / skill / "agents" / "openai.yaml"
        if not metadata.exists():
            fail(errors, f"skills/{skill}: missing agents/openai.yaml")

    validate_persona_review_allowlist(errors)
    validate_evidence_contract(errors)
    validate_evidence_examples(errors)
    validate_reachable_history(errors)

    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"validated {len(EXPECTED)} skills and {len(tracked_candidates)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
