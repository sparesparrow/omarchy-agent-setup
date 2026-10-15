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

    def test_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            output.joinpath("PLAN.md").write_text("keep")
            with self.assertRaisesRegex(TemplateError, "refusing to overwrite"):
                self.templates["python"].render(output, {
                    "title": "x", "goal": "y", "allowed_files": "z"
                })
            self.assertEqual(output.joinpath("PLAN.md").read_text(), "keep")

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


if __name__ == "__main__":
    unittest.main()
