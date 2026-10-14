#!/usr/bin/env python3
"""Quota-fallback router.

Decides which agent plays executor and evaluator, based on which agents are
marked exhausted, and when to escalate to Claude. It only DECIDES and prints the
choice; it does not start any agent, so it needs no keys and costs nothing.

State file: ~/.local/state/omarchy-agents/state.json (override with ROUTER_STATE)

Commands:
  router.py exhausted <agent> [--until ISO8601]   mark an agent out of quota
  router.py available <agent>                      clear the mark
  router.py status                                 show state
  router.py route                                  print the current routing as JSON
  router.py failed                                 record a failed executor/evaluator loop
  router.py passed                                 reset the failed-loop counter
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENTS = {"claude", "codex", "grok", "gemini"}
MAX_FAILED_LOOPS = 2
STATE = Path(os.environ.get("ROUTER_STATE", Path.home() / ".local/state/omarchy-agents/state.json"))


def now():
    return datetime.now(timezone.utc)


def load():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"exhausted": {}, "failed_loops": 0}


def save(s):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=2), encoding="utf-8")


def is_exhausted(s, agent):
    until = s["exhausted"].get(agent)
    if until is None:
        return False
    if until == "manual":
        return True
    return now() < datetime.fromisoformat(until)


def route(s):
    codex_out = is_exhausted(s, "codex")
    grok_out = is_exhausted(s, "grok")
    gemini_out = is_exhausted(s, "gemini")

    if s["failed_loops"] >= MAX_FAILED_LOOPS:
        return {"action": "replan", "agent": "claude", "reason": f"{s['failed_loops']} failed loops"}

    if not codex_out and not grok_out:
        return {"action": "run", "executor": "codex", "evaluator": "grok"}
    if codex_out and not grok_out:
        if gemini_out:
            return {"action": "pause", "reason": "codex and gemini exhausted; wait for reset"}
        return {"action": "run", "executor": "gemini", "evaluator": "grok"}
    if grok_out and not codex_out:
        if gemini_out:
            return {"action": "run", "executor": "codex", "evaluator": "claude-diff-only",
                    "note": "grok and gemini exhausted; short diff-only review by claude"}
        return {"action": "run", "executor": "codex", "evaluator": "gemini-fresh-session",
                "note": "give evaluator only plan, acceptance, diff and test results"}
    if gemini_out:
        return {"action": "pause", "reason": "codex, grok and gemini exhausted; wait for reset"}
    return {"action": "run", "executor": "gemini", "evaluator": "claude-diff-only",
            "note": "codex and grok exhausted; or pause until quotas reset"}


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd, rest = argv[0], argv[1:]
    s = load()
    if cmd in ("exhausted", "available"):
        if not rest or rest[0] not in AGENTS:
            sys.exit(f"agent must be one of {sorted(AGENTS)}")
        agent = rest[0]
        if cmd == "available":
            s["exhausted"].pop(agent, None)
        else:
            until = "manual"
            if "--until" in rest:
                until = datetime.fromisoformat(rest[rest.index("--until") + 1]).astimezone(timezone.utc).isoformat()
            s["exhausted"][agent] = until
        save(s)
    elif cmd == "failed":
        s["failed_loops"] += 1
        save(s)
    elif cmd == "passed":
        s["failed_loops"] = 0
        save(s)
    elif cmd not in ("status", "route"):
        sys.exit(__doc__)
    if cmd == "status":
        print(json.dumps(s, indent=2))
    else:
        print(json.dumps(route(s)))


if __name__ == "__main__":
    main(sys.argv[1:])
