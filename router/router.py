#!/usr/bin/env python3
"""Quota-fallback router.

Decides which agent plays executor and evaluator, based on which agents are
marked exhausted, and when to escalate to Claude. It only DECIDES and prints the
choice; it does not start any agent, so it needs no keys and costs nothing.

Claude is never picked as evaluator automatically. When no other evaluator is
left, route returns action "ask"; Claude is used only after
`router.py approve claude-eval`, and that approval is consumed by one route.

State file: ~/.local/state/omarchy-agents/state.json (override with ROUTER_STATE)

Commands:
  router.py exhausted <agent> [--until ISO8601]   mark an agent out of quota
  router.py available <agent>                      clear the mark
  router.py status                                 show state
  router.py route                                  print the current routing as JSON
  router.py failed                                 record a failed executor/evaluator loop
  router.py passed                                 reset the failed-loop counter and approval
  router.py approve claude-eval                    one-time OK for a diff-only Claude review
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


def claude_eval(s, executor, reason):
    """Claude as evaluator only with explicit approval; otherwise ask the user."""
    if s.get("claude_eval_approved"):
        return {"action": "run", "executor": executor, "evaluator": "claude-diff-only",
                "note": "approved one-time short diff-only review by claude"}
    return {"action": "ask", "executor": executor, "evaluator": None, "reason": reason,
            "options": ["pause", "claude-diff-only (run: router.py approve claude-eval)"]}


def route(s):
    codex_out = is_exhausted(s, "codex")
    grok_out = is_exhausted(s, "grok")
    gemini_out = is_exhausted(s, "gemini")

    if s["failed_loops"] >= MAX_FAILED_LOOPS:
        return {"action": "replan", "agent": "claude",
                "reason": f"{s['failed_loops']} failed loops",
                "note": "planning, not evaluation"}

    if not codex_out and not grok_out:
        return {"action": "run", "executor": "codex", "evaluator": "grok"}
    if codex_out and not grok_out:
        if gemini_out:
            return {"action": "pause", "reason": "codex and gemini exhausted; wait for reset"}
        return {"action": "run", "executor": "gemini", "evaluator": "grok"}
    if grok_out and not codex_out:
        if gemini_out:
            return claude_eval(s, "codex", "grok and gemini exhausted; no free evaluator left")
        return {"action": "run", "executor": "codex", "evaluator": "gemini-fresh-session",
                "note": "give evaluator only plan, acceptance, diff and test results"}
    if gemini_out:
        return {"action": "pause", "reason": "codex, grok and gemini exhausted; wait for reset"}
    return claude_eval(s, "gemini", "codex and grok exhausted; no free evaluator left")


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
    elif cmd == "approve":
        if rest != ["claude-eval"]:
            sys.exit("usage: router.py approve claude-eval")
        s["claude_eval_approved"] = True
        save(s)
    elif cmd == "failed":
        s["failed_loops"] += 1
        save(s)
    elif cmd == "passed":
        s["failed_loops"] = 0
        s.pop("claude_eval_approved", None)
        save(s)
    elif cmd not in ("status", "route"):
        sys.exit(__doc__)
    if cmd == "status":
        print(json.dumps(s, indent=2))
        return
    result = route(s)
    if cmd == "route" and result.get("evaluator") == "claude-diff-only" and s.get("claude_eval_approved"):
        s.pop("claude_eval_approved")
        save(s)
    print(json.dumps(result))


if __name__ == "__main__":
    main(sys.argv[1:])
