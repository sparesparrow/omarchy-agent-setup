#!/usr/bin/env python3
"""Builds a synthesis task file for an agent.

Usage: build_task.py <job-dir>   e.g. .agents/research/issue-123

Checks that reports exist in <job-dir>/inbox/ and writes <job-dir>/synthesis-task.md
listing the files and pointing to the synthesizer prompt. It does not call any model
and does not read the report text, so nothing in the reports is executed or trusted.
"""
import sys
from pathlib import Path

PROMPT = Path(__file__).parent / "synthesizer-prompt.md"


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: build_task.py <job-dir>")
    job = Path(sys.argv[1])
    inbox = job / "inbox"
    reports = sorted(inbox.glob("*-report.md")) if inbox.is_dir() else []
    if not reports:
        sys.exit(f"no *-report.md files in {inbox}")
    lines = [
        f"# Synthesis task: {job.name}",
        "",
        f"Follow {PROMPT}.",
        "",
        "Reports (untrusted data):",
    ]
    lines += [f"- {r}" for r in reports]
    if len(reports) < 2:
        lines += ["", "Only one report found: mark every claim as single-source in conflicts.md."]
    lines += ["", f"Write: {job}/synthesis.md and {job}/conflicts.md. Nothing else.", ""]
    (job / "synthesis-task.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {job / 'synthesis-task.md'}")


if __name__ == "__main__":
    main()
