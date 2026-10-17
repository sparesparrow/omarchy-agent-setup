import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("repo_setup", Path(__file__).resolve().parents[1] / "setup/github-repositories.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class RepositorySetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def repo(self, name="mia", directory="existing"):
        path = self.root / directory
        subprocess.run(["git", "init", "-q", str(path)], check=True)
        subprocess.run(["git", "-C", str(path), "remote", "add", "origin", f"git@github.com:sparesparrow/{name}.git"], check=True)
        return path

    def test_exact_inventory(self):
        self.assertEqual(len(MOD.NAMES), 26)
        self.assertEqual(len(set(MOD.NAMES)), 26)
        self.assertIn("1984", MOD.NAMES)

    def test_origins(self):
        for url in ("git@github.com:sparesparrow/mia.git", "https://github.com/sparesparrow/mia", "ssh://git@github.com/sparesparrow/mia.git"):
            self.assertEqual(MOD.origin_name(url), "mia")
        for url in ("git@evil.com:sparesparrow/mia.git", "https://github.com/other/mia.git", "https://github.com.evil/sparesparrow/mia", "https://token@github.com/sparesparrow/mia.git"):
            self.assertIsNone(MOD.origin_name(url))

    def test_discovery_uses_origin_not_folder(self):
        path = self.repo(directory="renamed")
        self.assertEqual(MOD.discover([self.root], 4)["mia"], [path])

    def test_depth_limit(self):
        self.repo(directory="deep/nested")
        self.assertEqual(MOD.discover([self.root], 1)["mia"], [])

    def test_symlink_directory_not_scanned(self):
        path = self.repo()
        other = self.root / "scan"
        other.mkdir()
        (other / "link").symlink_to(path, target_is_directory=True)
        self.assertEqual(MOD.discover([other], 4)["mia"], [])

    def test_multiple_clones(self):
        first = self.repo(directory="one")
        second = self.repo(directory="two")
        self.assertEqual(MOD.discover([self.root, self.root], 4)["mia"], [first, second])

    def test_skills_and_idempotency(self):
        path = self.repo()
        (path / "AGENTS.md").write_text("user rules")
        (path / "CLAUDE.md").write_text("user claude rules")
        self.assertEqual(MOD.install_skills(path, "mia"), 6)
        self.assertEqual(MOD.install_skills(path, "mia"), 0)
        self.assertEqual((path / "AGENTS.md").read_text(), "user rules")
        self.assertEqual((path / "CLAUDE.md").read_text(), "user claude rules")
        for role in MOD.ROLES:
            text = (path / f".agents/skills/omarchy-mia-{role}/SKILL.md").read_text()
            self.assertIn("name: omarchy-mia-" + role, text)
            self.assertIn("description:", text)

    def test_wrong_repo_rejected(self):
        with self.assertRaises(ValueError):
            MOD.install_skills(self.repo(), "libertin")

    def test_conflict_not_overwritten(self):
        path = self.repo()
        MOD.install_skills(path, "mia")
        target = path / ".agents/skills/omarchy-mia-executor/SKILL.md"
        target.write_text("custom")
        with self.assertRaises(ValueError):
            MOD.install_skills(path, "mia")
        self.assertEqual(target.read_text(), "custom")

    def test_symlink_write_rejected(self):
        path = self.repo()
        outside = self.root / "outside"
        outside.mkdir()
        (path / ".agents").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            MOD.install_skills(path, "mia")
        self.assertEqual(list(outside.iterdir()), [])

    def test_plan_creates_nothing(self):
        target = self.root / "missing"
        with patch("builtins.print"), patch.object(MOD, "confirm", side_effect=AssertionError("no prompt")):
            self.assertEqual(MOD.main(["--root", str(target)]), 0)
        self.assertFalse(target.exists())

    def test_declined_apply_creates_nothing(self):
        target = self.root / "missing"
        with patch("builtins.print"), patch.object(MOD, "confirm", return_value=False):
            self.assertEqual(MOD.main(["--root", str(target), "--apply"]), 0)
        self.assertFalse(target.exists())

    def test_existing_occupied_target_is_preserved(self):
        occupied = self.root / "mia"
        occupied.mkdir()
        (occupied / "data").write_text("keep")
        with patch("builtins.print"), patch.object(MOD, "confirm", return_value=False):
            self.assertEqual(MOD.main(["--root", str(self.root), "--apply"]), 1)
        self.assertEqual((occupied / "data").read_text(), "keep")

    def test_no_automatic_ssh_generation(self):
        key = self.root / "ssh/key"
        with patch.object(MOD, "confirm", return_value=False), patch.object(MOD, "run") as run:
            MOD.ssh_setup(key)
        run.assert_not_called()
        self.assertFalse(key.exists())

    def test_ssh_wrong_account_blocks_upload(self):
        key = self.root / "key"
        key.write_text("fake private fixture")
        Path(str(key) + ".pub").write_text("fake public fixture")
        result = subprocess.CompletedProcess([], 0, stdout="other-user\n")
        with patch.dict(MOD.os.environ, {"SSH_AUTH_SOCK": ""}), patch.object(MOD, "confirm", return_value=True), patch.object(MOD, "run", return_value=result) as run:
            with self.assertRaises(ValueError):
                MOD.ssh_setup(key)
        self.assertFalse(any("add" in call.args[0] for call in run.call_args_list))


if __name__ == "__main__":
    unittest.main()
