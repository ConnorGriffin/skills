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
EXPECTED = {
    "drive-local-webapp",
    "code-review",
    "pr-body",
    "say-less",
    "cbm-onboard",
    "ci-design",
    "codebase-design",
    "domain-modeling",
    "spin-worktree",
    "research",
    "implement",
    "tdd",
    "review",
    "prototype",
    "scope",
    "wayfinder",
    "plan-review",
    "persona-review",
    "ui-craft",
    "orchestrate",
    "writing-for-agents",
    "handoff",
    "preflight",
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
    skill_dir = SKILLS / "persona-review"
    if not skill_dir.exists():
        return
    for path in skill_dir.rglob("*"):
        if path.is_file():
            relative = path.relative_to(skill_dir).as_posix()
            if relative not in PERSONA_REVIEW_ALLOWLIST:
                fail(
                    errors,
                    f"skills/persona-review: file not on the allowlist: {relative}",
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


def is_digest(value: object) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"sha256:[0-9a-f]{64}", value))


def validate_evidence_examples(errors: list[str]) -> None:
    contract = evidence_json(CONTRACT, errors)
    positive = evidence_json(POSITIVE_EXAMPLES, errors)
    negative = evidence_json(NEGATIVE_EXAMPLES, errors)
    if not isinstance(contract, dict) or not isinstance(positive, dict) or not isinstance(negative, dict):
        return
    required_contract_fields = {
        "producer_envelope_fields", "producer_fact_fields", "source_fields",
        "review_subject_fields", "content_subject_fields", "producer_kinds",
        "validation_states", "review_actions", "lineage_relations", "link_fields",
        "max_links", "failure_envelope_fields", "failure_fact_fields", "failure_classes",
    }
    if not required_contract_fields <= set(contract):
        return
    observations = positive.get("observations")
    if set(positive) != {"observations"} or not isinstance(observations, list) or not observations:
        fail(errors, "docs/evidence/examples/positive.json: contains observations only")
        return
    producer_fields = set(contract["producer_envelope_fields"])
    producer_fact_fields = set(contract["producer_fact_fields"])
    source_fields = set(contract["source_fields"])
    review_subject_fields = set(contract["review_subject_fields"])
    content_subject_fields = set(contract["content_subject_fields"])
    producer_kinds = set(contract["producer_kinds"])
    states = set(contract["validation_states"])
    actions = set(contract["review_actions"])
    relations = set(contract["lineage_relations"])
    failure_fields = set(contract["failure_envelope_fields"])
    failure_fact_fields = set(contract["failure_fact_fields"])
    failure_classes = set(contract["failure_classes"])
    snapshots: dict[str, set[str]] = {}
    for index, observation in enumerate(observations):
        prefix = f"docs/evidence/examples/positive.json: observation {index}"
        if isinstance(observation, dict) and observation.get("envelope_kind") == "failure":
            if set(observation) != failure_fields:
                fail(errors, f"{prefix}: failure envelope fields are not closed")
                continue
            failure = observation["failure"]
            if not isinstance(failure, dict) or set(failure) != failure_fact_fields:
                fail(errors, f"{prefix}: failure fields are not closed")
            elif (failure["failure_class"] not in failure_classes or
                  failure["validation_state"] not in states or
                  failure["normalizer_version"] != "v2" or
                  not is_digest(failure["signature_digest"])):
                fail(errors, f"{prefix}: invalid failure class, validation state, or digest")
            source = observation["source"]
            subject = observation["subject"]
            if not isinstance(source, dict) or set(source) != source_fields:
                fail(errors, f"{prefix}: source fields are not closed")
            if not isinstance(subject, dict) or set(subject) not in (review_subject_fields, content_subject_fields):
                fail(errors, f"{prefix}: subject fields are not a contract subject")
            continue
        if not isinstance(observation, dict) or set(observation) != producer_fields:
            fail(errors, f"{prefix}: producer envelope fields are not closed")
            continue
        producer = observation["producer"]
        source = observation["source"]
        subject = observation["subject"]
        if not isinstance(producer, dict) or set(producer) != producer_fact_fields:
            fail(errors, f"{prefix}: producer fields are not closed")
        elif (producer["producer_kind"] not in producer_kinds or
              producer["validation_state"] not in states or
              (producer["review_action"] is not None and producer["review_action"] not in actions) or
              producer["normalizer_version"] != "v2" or not is_digest(producer["fact_digest"])):
            fail(errors, f"{prefix}: invalid producer_kind, validation_state, review_action, or digest")
        if not isinstance(source, dict) or set(source) != source_fields:
            fail(errors, f"{prefix}: source fields are not closed")
        elif (source["content_hash_algorithm"] != "sha256" or not is_digest(source["content_hash"]) or
              not all(isinstance(source[field], str) and source[field] for field in ("authority_kind", "locator", "repository", "revision", "scope"))):
            fail(errors, f"{prefix}: source must contain normalized authority facts")
        if not isinstance(subject, dict) or set(subject) not in (review_subject_fields, content_subject_fields):
            fail(errors, f"{prefix}: subject fields are not a contract subject")
        elif not isinstance(subject.get("revision"), str) or not subject["revision"]:
            fail(errors, f"{prefix}: subject lacks an immutable revision")
        elif "content_digest" in subject and not is_digest(subject["content_digest"]):
            fail(errors, f"{prefix}: content subject lacks a normalized digest")
        elif subject.get("subject_kind") == "working_tree_snapshot":
            snapshots.setdefault(subject["subject"], set()).add(subject["revision"])
        if not is_digest(observation["observation_id"]) or not isinstance(observation["observed_at"], str):
            fail(errors, f"{prefix}: observation identity is not normalized")
        links = observation["links"]
        if not isinstance(links, list) or len(links) > contract["max_links"]:
            fail(errors, f"{prefix}: invalid links")
        for link in links:
            if not isinstance(link, dict) or set(link) != set(contract["link_fields"]) or link["relation"] not in relations:
                fail(errors, f"{prefix}: link fields or relation are invalid")
    if not any(len(revisions) > 1 for revisions in snapshots.values()):
        fail(errors, "docs/evidence/examples/positive.json: needs distinct dirty snapshots at one HEAD")

    invalid = negative.get("invalid_observations")
    prohibited = {"candidate", "proposal", "promotion", "lesson"}
    if set(negative) != {"invalid_observations"} or not isinstance(invalid, list):
        fail(errors, "docs/evidence/examples/negative.json: invalid fixture shape")
        return
    for fixture in invalid:
        if not isinstance(fixture, dict) or fixture.get("producer_kind") not in prohibited:
            fail(errors, "docs/evidence/examples/negative.json: fixture does not reject a prohibited kind")
        elif fixture["producer_kind"] in producer_kinds:
            fail(errors, "docs/evidence/examples/negative.json: prohibited kind is admitted")
        if fixture.get("producer_kind") == "lesson" and fixture.get("validation_state") != "unvalidated":
            fail(errors, "docs/evidence/examples/negative.json: lesson fixture must prove unvalidated rejection")


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


def main() -> int:
    errors: list[str] = []
    actual = {path.name for path in SKILLS.iterdir() if path.is_dir()}
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
