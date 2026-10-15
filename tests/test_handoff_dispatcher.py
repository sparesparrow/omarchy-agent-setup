import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER = ROOT / "orchestration" / "handoff_dispatcher.py"


class HandoffDispatcherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.job = root / "job"
        self.job.mkdir()
        for name in ("PLAN.md", "TASKS.md", "ACCEPTANCE.md"):
            (self.job / name).write_text(f"# {name}\n", encoding="utf-8")
        self.state = root / "router-state.json"

    def tearDown(self):
        self.temporary.cleanup()

    def run_dispatcher(self, *arguments):
        return subprocess.run(
            [sys.executable, str(DISPATCHER), "--router-state", str(self.state), *arguments],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def output(self, result):
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)

    def test_default_execute_and_evaluate_handoff(self):
        execute = self.output(self.run_dispatcher("route", str(self.job), "--phase", "execute", "--dry-run"))
        self.assertEqual(("codex", "HANDOFF.md"), (execute["agent"], Path(execute["write"]).name))
        (self.job / "HANDOFF.md").write_text("# Handoff\n\n## Status: DONE\n", encoding="utf-8")
        evaluate = self.output(self.run_dispatcher("route", str(self.job), "--phase", "evaluate"))
        self.assertEqual(("grok", "EVALUATION.md"), (evaluate["agent"], Path(evaluate["write"]).name))

    def test_quota_fallbacks_and_never_auto_selects_claude(self):
        subprocess.run([sys.executable, str(ROOT / "router/router.py"), "exhausted", "codex"],
                       env={"ROUTER_STATE": str(self.state)}, check=True, capture_output=True, text=True)
        result = self.output(self.run_dispatcher("route", str(self.job), "--phase", "execute"))
        self.assertEqual("gemini", result["agent"])
        subprocess.run([sys.executable, str(ROOT / "router/router.py"), "exhausted", "grok"],
                       env={"ROUTER_STATE": str(self.state)}, check=True, capture_output=True, text=True)
        ask = self.output(self.run_dispatcher("route", str(self.job), "--phase", "evaluate"))
        self.assertEqual("ask", ask["action"])
        self.assertNotEqual("claude", ask.get("agent"))

    def test_two_failures_return_to_claude_for_replanning(self):
        first = self.output(self.run_dispatcher("failed", str(self.job)))
        self.assertEqual("FAIL", first["recorded"])
        self.assertEqual("run", first["action"])
        second = self.output(self.run_dispatcher("failed", str(self.job)))
        self.assertEqual(("replan", "claude"), (second["action"], second["agent"]))

    def test_pass_completes_and_resets_failure_counter(self):
        self.run_dispatcher("failed", str(self.job))
        passed = self.output(self.run_dispatcher("passed", str(self.job)))
        self.assertEqual(("complete", "user"), (passed["action"], passed["next_owner"]))
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(0, state["failed_loops"])

    def test_missing_required_file_blocks_without_traceback(self):
        (self.job / "TASKS.md").unlink()
        result = self.run_dispatcher("route", str(self.job), "--phase", "execute")
        self.assertEqual(2, result.returncode)
        self.assertIn("BLOCKED: missing or empty handoff file", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
