import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "router/router.py"


class RouterCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.state = Path(self.temporary.name) / "state.json"

    def tearDown(self):
        self.temporary.cleanup()

    def run_router(self, *args):
        environment = os.environ.copy()
        environment["ROUTER_STATE"] = str(self.state)
        return subprocess.run(
            [sys.executable, str(ROUTER), *args],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def state_data(self):
        return json.loads(self.state.read_text(encoding="utf-8"))

    def output_data(self, result):
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)

    def test_exhausted_marks_agent_and_routes_to_fallback(self):
        result = self.run_router("exhausted", "codex")
        self.assertEqual("manual", self.state_data()["exhausted"]["codex"])
        self.assertEqual(
            {
                "action": "run",
                "executor": "gemini",
                "evaluator": "grok",
                "reminders": [
                    "codex stays exhausted until cleared with: router.py available codex"
                ],
            },
            self.output_data(result),
        )

    def test_expired_until_makes_agent_available_and_clears_marker(self):
        expired = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        result = self.run_router("exhausted", "codex", "--until", expired)
        self.assertNotIn("codex", self.state_data()["exhausted"])
        self.assertEqual(
            {"action": "run", "executor": "codex", "evaluator": "grok"},
            self.output_data(result),
        )

    def test_future_until_keeps_agent_exhausted_without_manual_reminder(self):
        future = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        result = self.run_router("exhausted", "codex", "--until", future)
        output = self.output_data(result)
        self.assertEqual("gemini", output["executor"])
        self.assertNotIn("reminders", output)

    def test_invalid_until_reports_clear_error_without_traceback_or_state(self):
        result = self.run_router("exhausted", "codex", "--until", "tomorrow-ish")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("invalid --until value", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(self.state.exists())

    def test_missing_until_value_reports_usage_without_traceback(self):
        result = self.run_router("exhausted", "codex", "--until")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("usage: router.py exhausted", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_available_clears_exhausted_agent(self):
        self.run_router("exhausted", "codex")
        result = self.run_router("available", "codex")
        self.assertNotIn("codex", self.state_data()["exhausted"])
        self.assertEqual(
            {"action": "run", "executor": "codex", "evaluator": "grok"},
            self.output_data(result),
        )

    def test_failed_increments_counter_and_replans_after_second_loop(self):
        first = self.run_router("failed")
        self.assertEqual(1, self.state_data()["failed_loops"])
        self.assertEqual("run", self.output_data(first)["action"])

        second = self.run_router("failed")
        self.assertEqual(2, self.state_data()["failed_loops"])
        self.assertEqual(
            {
                "action": "replan",
                "agent": "claude",
                "reason": "2 failed loops",
                "note": "planning, not evaluation",
            },
            self.output_data(second),
        )

    def test_passed_resets_counter_and_one_time_approval(self):
        self.run_router("failed")
        self.run_router("approve", "claude-eval")
        result = self.run_router("passed")
        state = self.state_data()
        self.assertEqual(0, state["failed_loops"])
        self.assertNotIn("claude_eval_approved", state)
        self.assertEqual(
            {"action": "run", "executor": "codex", "evaluator": "grok"},
            self.output_data(result),
        )


if __name__ == "__main__":
    unittest.main()
