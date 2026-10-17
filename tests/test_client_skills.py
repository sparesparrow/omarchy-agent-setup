import argparse
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("client_skills", Path(__file__).resolve().parents[1] / "setup/client-skills.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class ClientSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)

    def test_native_global_paths(self):
        expected = {"omp": ".omp/agent/skills", "opencode": ".config/opencode/skills", "openclaw": ".openclaw/skills", "grok-build": ".grok/skills", "grok-cli": ".agents/skills"}
        for client, suffix in expected.items():
            self.assertEqual(M.global_root(client, self.home, {}), self.home / suffix)

    def test_environment_overrides(self):
        for client, key in (("opencode", "OPENCODE_CONFIG_DIR"), ("openclaw", "OPENCLAW_STATE_DIR"), ("grok-build", "GROK_HOME")):
            root = self.home / key
            self.assertEqual(M.global_root(client, self.home, {key: str(root)}), root / "skills")
        self.assertEqual(M.global_root("opencode", self.home, {"XDG_CONFIG_HOME": str(self.home / "xdg")}), self.home / "xdg/opencode/skills")

    def test_omp_profile_must_be_explicit(self):
        with self.assertRaises(ValueError):
            M.global_root("omp", self.home, {"OMP_PROFILE": "work"})
        chosen = self.home / "omp/profiles/work/agent"
        self.assertEqual(M.global_root("omp", self.home, {"OMP_PROFILE": "work"}, chosen), chosen / "skills")

    def test_install_is_idempotent(self):
        target = self.home / "skills/omarchy-team-executor/SKILL.md"
        entries = [(target, M.global_skill("executor"))]
        self.assertEqual(M.install(entries), 1)
        self.assertEqual(M.install(entries), 0)
        self.assertIn("name: omarchy-team-executor", target.read_text())

    def test_group_conflict_writes_nothing(self):
        first, conflict = self.home / "first", self.home / "conflict"
        conflict.write_text("user")
        with self.assertRaises(ValueError):
            M.install([(first, "new"), (conflict, "replacement")])
        self.assertFalse(first.exists())
        self.assertEqual(conflict.read_text(), "user")

    def test_symlink_rejected(self):
        target = self.home / "real"
        target.mkdir()
        (self.home / "link").symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError):
            M.install([(self.home / "link/SKILL.md", "text")])
        self.assertEqual(list(target.iterdir()), [])

    def test_global_plan_is_read_only(self):
        with patch.object(M.Path, "home", return_value=self.home), patch.dict(M.os.environ, {}, clear=True), patch("builtins.print"), patch.object(M, "confirm", side_effect=AssertionError):
            self.assertEqual(M.main(["--scope", "global", "--clients", "omp", "opencode", "openclaw", "grok-build", "grok-cli"]), 0)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_selected_role_only(self):
        with patch.object(M.Path, "home", return_value=self.home), patch.dict(M.os.environ, {}, clear=True), patch("builtins.print"), patch.object(M, "confirm", return_value=True):
            self.assertEqual(M.main(["--scope", "global", "--clients", "omp", "--roles", "evaluator", "--apply"]), 0)
        installed = list(self.home.rglob("SKILL.md"))
        self.assertEqual(len(installed), 1)
        self.assertIn("evaluator", str(installed[0]))

    def test_real_clone_discovery_and_project_copy(self):
        repo = self.home / "renamed"
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", "git@github.com:sparesparrow/mia.git"], check=True)
        text = "---\nname: omarchy-mia-evaluator\ndescription: Test review\n---\n\nReview only.\n"
        source = repo / ".agents/skills/omarchy-mia-evaluator/SKILL.md"
        source.parent.mkdir(parents=True)
        source.write_text(text)
        with patch("builtins.print"), patch.object(M, "confirm", return_value=True):
            self.assertEqual(M.main(["--scope", "project", "--root", str(self.home), "--roles", "evaluator", "--clients", "omp", "opencode", "openclaw", "grok-build", "grok-cli", "--apply"]), 0)
        for root in (".omp/skills", ".opencode/skills", ".agents/skills", ".grok/skills"):
            self.assertEqual((repo / root / "omarchy-mia-evaluator/SKILL.md").read_text(), text)

    def test_missing_project_source_blocks_global_writes(self):
        args = argparse.Namespace(scope="both", clients=["omp"], roles=["evaluator"], omp_agent_dir=None, root=self.home, search_root=[], depth=4)
        with patch.object(M, "discover", return_value={"mia": [self.home]}):
            with self.assertRaises(FileNotFoundError):
                list(M.groups(args, self.home, {}))
        self.assertEqual(list(self.home.iterdir()), [])

    def test_invalid_source_header(self):
        source = self.home / ".agents/skills/omarchy-mia-evaluator/SKILL.md"
        source.parent.mkdir(parents=True)
        source.write_text("---\nname: rogue\ndescription: wrong\n---\n")
        with self.assertRaises(ValueError):
            M.project_skill(self.home, "mia", "evaluator")

    def test_unselected_grok_is_not_installed(self):
        with patch.object(M.Path, "home", return_value=self.home), patch.dict(M.os.environ, {}, clear=True), patch("builtins.print"), patch.object(M, "confirm", return_value=True):
            self.assertEqual(M.main(["--scope", "global", "--apply"]), 0)
        self.assertFalse((self.home / ".grok").exists())
        self.assertFalse((self.home / ".agents").exists())


if __name__ == "__main__":
    unittest.main()
