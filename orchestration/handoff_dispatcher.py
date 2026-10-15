#!/usr/bin/env python3
"""Dry-run dispatcher for orchestrator, executor, and evaluator handoffs."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "router" / "router.py"
REQUIRED = ("PLAN.md", "TASKS.md", "ACCEPTANCE.md")


class DispatchError(ValueError):
    pass


def validated_job_dir(value: str) -> Path:
    job = Path(value).resolve()
    if not job.is_dir():
        raise DispatchError(f"job directory not found: {job}")
    for name in REQUIRED:
        path = job / name
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            raise DispatchError(f"missing or empty handoff file: {path}")
    return job


def router_command(state: Path, *arguments: str) -> dict:
    environment = os.environ.copy()
    environment["ROUTER_STATE"] = str(state.resolve())
    result = subprocess.run(
        [sys.executable, str(ROUTER), *arguments],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise DispatchError(result.stderr.strip() or result.stdout.strip() or "quota router failed")
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise DispatchError("quota router returned invalid JSON") from error
    if not isinstance(output, dict):
        raise DispatchError("quota router returned a non-object")
    return output


def decision(job: Path, state: Path, phase: str) -> dict:
    routed = router_command(state, "route")
    action = routed.get("action")
    result = {"job_dir": str(job), "phase": phase, "dry_run": True, "action": action}
    if action == "run":
        result["agent"] = routed["executor" if phase == "execute" else "evaluator"]
        result["read"] = [str(job / name) for name in REQUIRED]
        if phase == "execute":
            result["write"] = str(job / "HANDOFF.md")
        else:
            handoff = job / "HANDOFF.md"
            if not handoff.is_file() or not handoff.read_text(encoding="utf-8").strip():
                raise DispatchError(f"missing or empty handoff file: {handoff}")
            result["read"].append(str(handoff))
            result["write"] = str(job / "EVALUATION.md")
    elif action == "replan":
        result.update({"phase": "replan", "agent": "claude", "reason": routed.get("reason")})
    else:
        result["reason"] = routed.get("reason")
        if "options" in routed:
            result["options"] = routed["options"]
    if routed.get("reminders"):
        result["reminders"] = routed["reminders"]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--router-state", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    route = sub.add_parser("route")
    route.add_argument("job_dir")
    route.add_argument("--phase", choices=("execute", "evaluate"), required=True)
    route.add_argument("--dry-run", action="store_true", help="document that no agent is launched")
    failed = sub.add_parser("failed")
    failed.add_argument("job_dir")
    passed = sub.add_parser("passed")
    passed.add_argument("job_dir")
    args = parser.parse_args(argv)
    try:
        job = validated_job_dir(args.job_dir)
        if args.command == "route":
            output = decision(job, args.router_state, args.phase)
        elif args.command == "failed":
            routed = router_command(args.router_state, "failed")
            output = decision(job, args.router_state, "execute")
            output["recorded"] = "FAIL"
            if routed.get("action") == "replan":
                output.update({"action": "replan", "phase": "replan", "agent": "claude",
                               "reason": routed.get("reason")})
        else:
            router_command(args.router_state, "passed")
            output = {"job_dir": str(job), "phase": "complete", "dry_run": True,
                      "action": "complete", "recorded": "PASS", "next_owner": "user"}
    except (DispatchError, OSError, UnicodeError) as error:
        parser.exit(2, f"BLOCKED: {error}\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
