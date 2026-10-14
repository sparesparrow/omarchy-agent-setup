#!/usr/bin/env python3
"""Validates synthesis outputs for a job.

Usage: check_outputs.py <job-dir>   e.g. .agents/research/issue-123

Checks that synthesis.md and conflicts.md exist and are not empty, and that
synthesis.md is at most 1200 words. Exit code 0 = OK, 1 = problem found.
It only counts words; it does not interpret the text.
"""
import sys
from pathlib import Path

MAX_WORDS = 1200
REQUIRED = ("synthesis.md", "conflicts.md")


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: check_outputs.py <job-dir>")
    job = Path(sys.argv[1])
    problems = []
    for name in REQUIRED:
        path = job / name
        if not path.is_file():
            problems.append(f"missing: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            problems.append(f"empty: {path}")
        elif name == "synthesis.md":
            words = len(text.split())
            if words > MAX_WORDS:
                problems.append(f"too long: {path} has {words} words (max {MAX_WORDS})")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)
    print(f"OK: {job}")


if __name__ == "__main__":
    main()
