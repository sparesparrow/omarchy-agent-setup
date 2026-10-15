import json
import tempfile
import unittest
from pathlib import Path

from orchestration.workflow_templates import TemplateError, TemplateManager, parse_variables


ROOT = Path(__file__).resolve().parents[1]


class WorkflowTemplateTests(unittest.TestCase):
    def setUp(self):
        self.manager = TemplateManager(ROOT / "project-templates")
        self.templates = self.manager.discover()

    def test_discovers_supported_project_types(self):
        self.assertEqual(set(self.templates), {"embedded", "hyprland", "python"})

    def test_renders_python_contract_without_unresolved_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "job"
            paths = self.templates["python"].render(output, {
                "title": "Add validation", "goal": "Reject malformed jobs", "allowed_files": "research/**"
            })
            self.assertEqual({path.name for path in paths}, {"PLAN.md", "TASKS.md", "ACCEPTANCE.md"})
            text = "\n".join(path.read_text() for path in paths)
            self.assertNotIn("{{", text)
            self.assertIn("python3 -m pytest -q", text)

    def test_preserves_token_like_text_in_supplied_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "job"
            self.templates["python"].render(output, {
                "title": "Document {{raw_token}}", "goal": "Keep examples literal", "allowed_files": "docs/**"
            })
            self.assertIn("{{raw_token}}", output.joinpath("PLAN.md").read_text())

    def test_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            output.joinpath("PLAN.md").write_text("keep")
            with self.assertRaisesRegex(TemplateError, "refusing to overwrite"):
                self.templates["python"].render(output, {
                    "title": "x", "goal": "y", "allowed_files": "z"
                })
            self.assertEqual(output.joinpath("PLAN.md").read_text(), "keep")
            self.assertFalse(output.joinpath("TASKS.md").exists())

    def test_preflights_all_destinations_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            output.joinpath("TASKS.md").mkdir()
            with self.assertRaisesRegex(TemplateError, "destination is a directory"):
                self.templates["python"].render(output, {
                    "title": "x", "goal": "y", "allowed_files": "z"
                }, force=True)
            self.assertFalse(output.joinpath("PLAN.md").exists())

    def test_rejects_destination_symlink_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "output"
            outside = root / "outside"
            output.mkdir()
            outside.mkdir()
            try:
                output.joinpath("PLAN.md").symlink_to(outside / "PLAN.md")
            except OSError:
                self.skipTest("symlinks are unavailable")
            with self.assertRaisesRegex(TemplateError, "escapes its root"):
                self.templates["python"].render(output, {
                    "title": "x", "goal": "y", "allowed_files": "z"
                }, force=True)

    def test_auto_detects_all_supported_types(self):
        markers = {"python": "pyproject.toml", "embedded": "platformio.ini", "hyprland": "hyprland.conf"}
        for expected, marker in markers.items():
            with self.subTest(expected), tempfile.TemporaryDirectory() as tmp:
                Path(tmp, marker).write_text("")
                self.assertEqual(self.manager.detect(Path(tmp)).name, expected)

    def test_auto_detection_blocks_ambiguous_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "pyproject.toml").write_text("")
            Path(tmp, "platformio.ini").write_text("")
            with self.assertRaisesRegex(TemplateError, "exactly one match"):
                self.manager.detect(Path(tmp))

    def test_rejects_unknown_and_duplicate_variables(self):
        with self.assertRaises(TemplateError):
            self.templates["python"].values({"surprise": "x"})
        with self.assertRaises(TemplateError):
            parse_variables(["goal=a", "goal=b"])

    def test_metadata_sources_exist_and_destinations_are_unique(self):
        for template in self.templates.values():
            metadata = json.loads((template.directory / "template.json").read_text())
            destinations = [item["destination"] for item in metadata["files"]]
            self.assertEqual(len(destinations), len(set(destinations)))
            for item in metadata["files"]:
                self.assertTrue((template.directory / item["source"]).is_file())

    def test_rejects_invalid_metadata_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "test"
            template.mkdir()
            template.joinpath("PLAN.md.tmpl").write_text("ok")
            template.joinpath("template.json").write_text(json.dumps({
                "name": "test", "description": "test", "version": "latest", "markers": ["x"],
                "variables": {}, "files": [{"source": "PLAN.md.tmpl", "destination": "PLAN.md"}]
            }))
            with self.assertRaisesRegex(TemplateError, "MAJOR.MINOR.PATCH"):
                TemplateManager(root).discover()


if __name__ == "__main__":
    unittest.main()
