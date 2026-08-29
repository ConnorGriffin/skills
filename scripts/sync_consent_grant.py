#!/usr/bin/env python3
"""Synchronize or verify generated worker-egress consent grant surfaces."""

import argparse
import sys
from pathlib import Path

from consent_grant import (
    CANONICAL_DISPATCH_GRANT,
    CLAUSE_SURFACES,
    DESCRIPTION_BYTE_CAPS,
    GENERATED_SURFACES,
)


def rendered_block(indent):
    return "\n".join(f"{indent}{line}" for line in CANONICAL_DISPATCH_GRANT.splitlines())


def split_surface(source, before, after):
    if source.count(before) != 1:
        raise ValueError("span anchors are not unique")
    prefix, tail = source.split(before, 1)
    if after not in tail:
        raise ValueError("closing span anchor is missing")
    current, suffix = tail.split(after, 1)
    return prefix + before, current, after + suffix


def process_generated_surfaces(repository, *, write):
    failures = []
    for name, surface in GENERATED_SURFACES.items():
        path = repository / surface["path"]
        try:
            source = path.read_text(encoding="utf-8")
            prefix, current, suffix = split_surface(
                source, surface["before"], surface["after"]
            )
        except (OSError, ValueError) as error:
            failures.append(f"{name}: generated span: {error}")
            continue
        expected = rendered_block(surface["indent"]) + "\n\n"
        if current == expected:
            continue
        if write:
            path.write_text(prefix + expected + suffix, encoding="utf-8")
        else:
            failures.append(f"{name}: generated block differs from canonical source")
    return failures


def compact(source):
    return " ".join(source.split()).lower()


def check_clause_surfaces(repository):
    failures = []
    for name, surface in CLAUSE_SURFACES.items():
        path = repository / surface["path"]
        try:
            source = path.read_text(encoding="utf-8")
            _, current, _ = split_surface(source, surface["before"], surface["after"])
        except (OSError, ValueError) as error:
            failures.append(f"{name}: surface span: {error}")
            continue
        current = compact(current)
        for clause_name, clause in surface["clauses"].items():
            if compact(clause) not in current:
                failures.append(f"{name}: {clause_name} missing")
    return failures


def check_description_byte_caps(repository):
    failures = []
    for name, limit in DESCRIPTION_BYTE_CAPS.items():
        surface = CLAUSE_SURFACES[name]
        path = repository / surface["path"]
        try:
            source = path.read_text(encoding="utf-8")
            _, description, _ = split_surface(
                source, surface["before"], surface["after"]
            )
        except (OSError, ValueError) as error:
            failures.append(f"{name}: description span: {error}")
            continue
        byte_count = len(description.encode("utf-8"))
        if byte_count > limit:
            failures.append(
                f"{name}: {byte_count} UTF-8 bytes exceeds the {limit} UTF-8 bytes cap"
            )
    return failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("sync", "check"))
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parents[1]
    )
    arguments = parser.parse_args()
    failures = process_generated_surfaces(
        arguments.repo.resolve(), write=arguments.mode == "sync"
    )
    failures.extend(check_clause_surfaces(arguments.repo.resolve()))
    failures.extend(check_description_byte_caps(arguments.repo.resolve()))
    for failure in failures:
        print(f"consent-grant: {failure}", file=sys.stderr)
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
