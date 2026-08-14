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
    permitted_relations = {
        "claim": {"derives_from", "governs"},
        "criterion": {"derives_from", "governs"},
        "decision": {"settles", "governs"},
        "disposition": {"settles", "addresses"},
        "objection": {"derives_from", "refutes"},
        "revision": {"revises", "addresses"},
        "verdict": {"settles", "verifies"},
        "finding": {"derives_from", "refutes"},
        "review_action": {"addresses"},
        "fix": {"implements", "addresses"},
        "verification": {"verifies", "refutes"},
        "delegation": {"delegates", "derives_from"},
        "slice": {"derives_from", "governs"},
        "decline": {"settles", "addresses"},
        "settlement": {"settles", "verifies"},
    }
    required_relations = {
        "criterion": {"derives_from"},
        "decision": {"governs"},
        "disposition": {"settles", "addresses"},
        "objection": {"derives_from"},
        "revision": {"revises", "addresses"},
        "verdict": {"settles", "verifies"},
        "finding": {"derives_from"},
        "review_action": {"addresses"},
        "fix": {"implements", "addresses"},
        "delegation": {"derives_from"},
        "slice": {"derives_from", "governs"},
        "decline": {"settles", "addresses"},
        "settlement": {"settles", "verifies"},
    }
    lineage_target_kinds = {
        ("criterion", "derives_from"): {"claim"},
        ("decision", "governs"): {"criterion"},
        ("disposition", "addresses"): {"criterion"},
        ("disposition", "settles"): {"decision"},
        ("objection", "derives_from"): {"criterion"},
        ("revision", "revises"): {"criterion"},
        ("revision", "addresses"): {"objection"},
        ("verdict", "settles"): {"objection"},
        ("verdict", "verifies"): {"revision"},
        ("finding", "derives_from"): {"criterion"},
        ("finding", "refutes"): {"finding"},
        ("review_action", "addresses"): {"finding"},
        ("fix", "implements"): {"review_action"},
        ("fix", "addresses"): {"finding"},
        ("verification", "refutes"): {"objection", "finding"},
        ("verification", "verifies"): {"fix", "revision", "slice"},
        ("delegation", "derives_from"): {"criterion"},
        ("slice", "derives_from"): {"delegation"},
        ("slice", "governs"): {"criterion"},
        ("decline", "addresses"): {"slice"},
        ("decline", "settles"): {"delegation"},
        ("settlement", "settles"): {"finding", "delegation"},
        ("settlement", "verifies"): {"verification"},
    }
    snapshots: dict[str, set[str]] = {}
    snapshot_counts: dict[str, int] = {}
    observation_ids = [
        observation.get("observation_id")
        for observation in observations
        if isinstance(observation, dict)
    ]
    normalized_observation_ids = [
        observation_id
        for observation_id in observation_ids
        if isinstance(observation_id, str)
    ]
    if len(normalized_observation_ids) != len(set(normalized_observation_ids)):
        fail(errors, "docs/evidence/examples/positive.json: duplicate observation_id")
    all_observation_ids = set(normalized_observation_ids)
    observations_by_id = {
        observation["observation_id"]: observation
        for observation in observations
        if isinstance(observation, dict)
        and isinstance(observation.get("observation_id"), str)
    }
    seen_observation_ids: set[str] = set()
    seen_producer_kinds: set[str] = set()
    seen_failure_classes: set[str] = set()
    for index, observation in enumerate(observations):
        prefix = f"docs/evidence/examples/positive.json: observation {index}"
        if not isinstance(observation, dict):
            fail(errors, f"{prefix}: observation must be an object")
            continue
        observation_id = observation.get("observation_id")
        if not is_digest(observation_id) or not isinstance(observation.get("observed_at"), str):
            fail(errors, f"{prefix}: observation identity is not normalized")
        if isinstance(observation, dict) and observation.get("envelope_kind") == "failure":
            if set(observation) != failure_fields:
                fail(errors, f"{prefix}: failure envelope fields are not closed")
                continue
            failure = observation["failure"]
            if not isinstance(failure, dict) or set(failure) != failure_fact_fields:
                fail(errors, f"{prefix}: failure fields are not closed")
            elif (not isinstance(failure["failure_class"], str) or
                  failure["failure_class"] not in failure_classes or
                  not isinstance(failure["validation_state"], str) or
                  failure["validation_state"] not in states or
                  failure["normalizer_version"] != "v2" or
                  not is_digest(failure["signature_digest"])):
                fail(errors, f"{prefix}: invalid failure class, validation state, or digest")
            else:
                seen_failure_classes.add(failure["failure_class"])
            source = observation["source"]
            subject = observation["subject"]
            if not isinstance(source, dict) or set(source) != source_fields:
                fail(errors, f"{prefix}: source fields are not closed")
            elif (source["content_hash_algorithm"] != "sha256" or
                  not is_digest(source["content_hash"]) or
                  not all(isinstance(source[field], str) and source[field]
                          for field in ("authority_kind", "locator", "repository", "revision", "scope"))):
                fail(errors, f"{prefix}: source must contain normalized authority facts")
            if not isinstance(subject, dict) or set(subject) not in (review_subject_fields, content_subject_fields):
                fail(errors, f"{prefix}: subject fields are not a contract subject")
            elif not isinstance(subject.get("revision"), str) or not subject["revision"]:
                fail(errors, f"{prefix}: subject lacks an immutable revision")
            if is_digest(observation_id):
                seen_observation_ids.add(observation_id)
            continue
        if set(observation) != producer_fields:
            fail(errors, f"{prefix}: producer envelope fields are not closed")
            continue
        producer = observation["producer"]
        source = observation["source"]
        subject = observation["subject"]
        if not isinstance(producer, dict) or set(producer) != producer_fact_fields:
            fail(errors, f"{prefix}: producer fields are not closed")
        elif (not isinstance(producer["producer_kind"], str) or
              producer["producer_kind"] not in producer_kinds or
              not isinstance(producer["validation_state"], str) or
              producer["validation_state"] not in states or
              (producer["review_action"] is not None and
               (not isinstance(producer["review_action"], str) or
                producer["review_action"] not in actions)) or
              producer["normalizer_version"] != "v2" or not is_digest(producer["fact_digest"])):
            fail(errors, f"{prefix}: invalid producer_kind, validation_state, review_action, or digest")
        else:
            seen_producer_kinds.add(producer["producer_kind"])
        producer_kind = (
            producer.get("producer_kind")
            if isinstance(producer, dict)
            and isinstance(producer.get("producer_kind"), str)
            else None
        )
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
            snapshot_match = re.fullmatch(
                r"base=[0-9a-f]{40};head=[0-9a-f]{40}", subject["subject"]
            ) if isinstance(subject.get("subject"), str) else None
            if not is_digest(subject["revision"]) or not snapshot_match:
                fail(errors, f"{prefix}: working tree snapshot identity is not normalized")
            else:
                if (not isinstance(source, dict) or
                        source.get("revision") != snapshot_match.group(0).rsplit("head=", 1)[1]):
                    fail(errors, f"{prefix}: snapshot head must match source revision")
                snapshots.setdefault(subject["subject"], set()).add(subject["revision"])
                snapshot_counts[subject["subject"]] = snapshot_counts.get(subject["subject"], 0) + 1
        links = observation["links"]
        if not isinstance(links, list) or len(links) > contract["max_links"]:
            fail(errors, f"{prefix}: invalid links")
            if is_digest(observation_id):
                seen_observation_ids.add(observation_id)
            continue
        if [link.get("ordinal") for link in links if isinstance(link, dict)] != list(range(len(links))):
            fail(errors, f"{prefix}: lineage links must have dense ordinals")
        used_relations: set[str] = set()
        used_lineage: set[tuple[str, str]] = set()
        for link in links:
            if (not isinstance(link, dict) or
                    set(link) != set(contract["link_fields"]) or
                    not isinstance(link.get("relation"), str) or
                    link["relation"] not in relations or
                    not is_digest(link.get("target_event_id"))):
                fail(errors, f"{prefix}: link fields or relation are invalid")
                continue
            used_relations.add(link["relation"])
            target = link["target_event_id"]
            lineage = (link["relation"], target)
            if lineage in used_lineage:
                fail(errors, f"{prefix}: lineage links must be unique")
            used_lineage.add(lineage)
            if not is_digest(target) or target not in all_observation_ids:
                fail(errors, f"{prefix}: lineage target is not a valid observation")
            elif target not in seen_observation_ids:
                fail(errors, f"{prefix}: lineage must target an earlier observation")
            else:
                target_observation = observations_by_id[target]
                target_producer = target_observation.get("producer", {})
                expected_target_kinds = lineage_target_kinds.get(
                    (producer_kind, link["relation"])
                )
                same_lifecycle = (
                    isinstance(target_observation.get("source"), dict)
                    and isinstance(source, dict)
                    and target_observation["source"].get("repository") == source.get("repository")
                    and target_observation["source"].get("scope") == source.get("scope")
                    and (
                        target_observation["source"].get("authority_kind")
                        != source.get("authority_kind")
                        or target_observation["source"].get("locator")
                        == source.get("locator")
                    )
                )
                if (not isinstance(target_producer, dict) or
                        expected_target_kinds is None or
                        not isinstance(target_producer.get("producer_kind"), str) or
                        target_producer["producer_kind"] not in expected_target_kinds or
                        not same_lifecycle):
                    fail(errors, f"{prefix}: invalid lineage target kind or lifecycle")
        if producer_kind in permitted_relations and used_relations - permitted_relations[producer_kind]:
            fail(errors, f"{prefix}: lineage relation is not permitted for {producer_kind}")
        if producer_kind in required_relations and not required_relations[producer_kind] <= used_relations:
            fail(errors, f"{prefix}: required lineage is missing for {producer_kind}")
        if producer_kind == "verification" and not used_relations & {"verifies", "refutes"}:
            fail(errors, f"{prefix}: required lineage is missing for verification")
        if is_digest(observation_id):
            seen_observation_ids.add(observation_id)
    if seen_producer_kinds != producer_kinds:
        fail(errors, "docs/evidence/examples/positive.json: producer kind matrix is incomplete")
    if seen_failure_classes != failure_classes:
        fail(errors, "docs/evidence/examples/positive.json: failure class matrix is incomplete")
    if any(snapshot_counts[subject] != len(revisions) for subject, revisions in snapshots.items()):
        fail(errors, "docs/evidence/examples/positive.json: needs distinct dirty snapshots at one HEAD")
    if not any(len(revisions) > 1 for revisions in snapshots.values()):
        fail(errors, "docs/evidence/examples/positive.json: needs distinct dirty snapshots at one HEAD")

    invalid = negative.get("invalid_observations")
    invalid_failures = negative.get("invalid_failures")
    prohibited = {"candidate", "proposal", "promotion", "lesson"}
    prohibited_failures = {"candidate", "policy_state", "worker_failure"}
    if (set(negative) != {"invalid_observations", "invalid_failures"} or
            not isinstance(invalid, list) or not isinstance(invalid_failures, list)):
        fail(errors, "docs/evidence/examples/negative.json: invalid fixture shape")
        return
    for fixture in invalid:
        if (not isinstance(fixture, dict) or
                not isinstance(fixture.get("producer_kind"), str) or
                fixture["producer_kind"] not in prohibited):
            fail(errors, "docs/evidence/examples/negative.json: fixture does not reject a prohibited kind")
        elif fixture["producer_kind"] in producer_kinds:
            fail(errors, "docs/evidence/examples/negative.json: prohibited kind is admitted")
        if fixture.get("producer_kind") == "lesson" and fixture.get("validation_state") != "unvalidated":
            fail(errors, "docs/evidence/examples/negative.json: lesson fixture must prove unvalidated rejection")
    for fixture in invalid_failures:
        if (not isinstance(fixture, dict) or
                not isinstance(fixture.get("failure_class"), str) or
                fixture["failure_class"] not in prohibited_failures):
            fail(errors, "docs/evidence/examples/negative.json: fixture does not reject a prohibited failure class")
        elif fixture["failure_class"] in failure_classes:
            fail(errors, "docs/evidence/examples/negative.json: prohibited failure class is admitted")


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
