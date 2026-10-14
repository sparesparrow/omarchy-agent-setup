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

    def test_grok_and_gemini_out(self):
        r = router.route(state(out=["grok", "gemini"]))
        self.assertEqual(r["evaluator"], "claude-diff-only")

    def test_codex_and_gemini_out_pauses(self):
        self.assertEqual(router.route(state(out=["codex", "gemini"]))["action"], "pause")

    def test_all_out_pauses(self):
        self.assertEqual(router.route(state(out=["codex", "grok", "gemini"]))["action"], "pause")

    def test_codex_and_grok_out(self):
        r = router.route(state(out=["codex", "grok"]))
        self.assertEqual((r["executor"], r["evaluator"]), ("gemini", "claude-diff-only"))

    def test_escalates_after_two_failures(self):
        r = router.route(state(failed=2))
        self.assertEqual((r["action"], r["agent"]), ("replan", "claude"))


if __name__ == "__main__":
    unittest.main()
