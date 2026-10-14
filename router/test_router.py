import os
import tempfile
import unittest
from pathlib import Path

os.environ["ROUTER_STATE"] = str(Path(tempfile.mkdtemp()) / "state.json")

import router  # noqa: E402


def state(**kw):
    s = {"exhausted": {}, "failed_loops": 0}
    s["exhausted"].update({k: "manual" for k in kw.get("out", [])})
    s["failed_loops"] = kw.get("failed", 0)
    if kw.get("approved"):
        s["claude_eval_approved"] = True
    return s


class RouteTests(unittest.TestCase):
    def test_default(self):
        r = router.route(state())
        self.assertEqual((r["executor"], r["evaluator"]), ("codex", "grok"))

    def test_codex_out(self):
        r = router.route(state(out=["codex"]))
        self.assertEqual((r["executor"], r["evaluator"]), ("gemini", "grok"))

    def test_grok_out(self):
        r = router.route(state(out=["grok"]))
        self.assertEqual((r["executor"], r["evaluator"]), ("codex", "gemini-fresh-session"))

    def test_grok_and_gemini_out_asks(self):
        r = router.route(state(out=["grok", "gemini"]))
        self.assertEqual(r["action"], "ask")
        self.assertIsNone(r["evaluator"])
        self.assertEqual(r["executor"], "codex")

    def test_codex_and_gemini_out_pauses(self):
        self.assertEqual(router.route(state(out=["codex", "gemini"]))["action"], "pause")

    def test_all_out_pauses(self):
        self.assertEqual(router.route(state(out=["codex", "grok", "gemini"]))["action"], "pause")

    def test_codex_and_grok_out_asks(self):
        r = router.route(state(out=["codex", "grok"]))
        self.assertEqual((r["action"], r["executor"], r["evaluator"]), ("ask", "gemini", None))
        self.assertEqual(r["options"][0], "pause")

    def test_escalates_after_two_failures(self):
        r = router.route(state(failed=2))
        self.assertEqual((r["action"], r["agent"]), ("replan", "claude"))

    def test_replan_ignores_approval(self):
        r = router.route(state(failed=2, approved=True))
        self.assertEqual(r["action"], "replan")
        self.assertNotIn("evaluator", r)

    def test_claude_never_without_approval(self):
        for out in (["grok", "gemini"], ["codex", "grok"]):
            self.assertNotEqual(router.route(state(out=out)).get("evaluator"), "claude-diff-only")

    def test_claude_after_approval(self):
        for out in (["grok", "gemini"], ["codex", "grok"]):
            r = router.route(state(out=out, approved=True))
            self.assertEqual((r["action"], r["evaluator"]), ("run", "claude-diff-only"))


class ApprovalCliTests(unittest.TestCase):
    def setUp(self):
        router.STATE = Path(tempfile.mkdtemp()) / "state.json"
        router.save(state(out=["grok", "gemini"]))

    def run_cmd(self, *argv):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            router.main(list(argv))
        return buf.getvalue()

    def test_approval_is_consumed_once(self):
        self.run_cmd("approve", "claude-eval")
        self.assertIn("claude-diff-only", self.run_cmd("route"))
        self.assertIn('"ask"', self.run_cmd("route"))

    def test_status_does_not_consume(self):
        self.run_cmd("approve", "claude-eval")
        self.run_cmd("status")
        self.assertIn("claude-diff-only", self.run_cmd("route"))

    def test_passed_clears_approval(self):
        self.run_cmd("approve", "claude-eval")
        self.run_cmd("passed")
        self.assertIn('"ask"', self.run_cmd("route"))

    def test_approve_needs_argument(self):
        with self.assertRaises(SystemExit):
            self.run_cmd("approve")


if __name__ == "__main__":
    unittest.main()
