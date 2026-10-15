import copy
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("workflow_templates", ROOT / "orchestration/workflow_templates.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WorkflowTemplateTests(unittest.TestCase):
    def manager(self):
        manager = MODULE.TemplateManager(ROOT / "project-templates")
        manager.discover()
        return manager

    def test_discovers_expected_templates(self):
        self.assertEqual({"embedded", "hyprland", "python"}, set(self.manager().templates))

    def test_renders_python_contracts_and_preserves_literal_variable_text(self):
        template = self.manager().templates["python"]
        with tempfile.TemporaryDirectory() as directory:
            paths = template.render(Path(directory), {
                "title": "Add {{literal}} validation",
                "goal": "Reject invalid jobs",
                "allowed_files": "research/**",
            })
            self.assertEqual({"PLAN.md", "TASKS.md", "ACCEPTANCE.md"}, {path.name for path in paths})
            self.assertIn("Add {{literal}} validation", (Path(directory) / "PLAN.md").read_text())

    def test_refuses_overwrite_before_writing_any_file(self):
        template = self.manager().templates["python"]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            existing = output / "TASKS.md"
            existing.write_text("keep")
            with self.assertRaises(MODULE.TemplateError):
                template.render(output, {"title": "x", "goal": "y", "allowed_files": "z"})
            self.assertEqual("keep", existing.read_text())
            self.assertFalse((output / "PLAN.md").exists())

    def test_force_replaces_all_files(self):
        template = self.manager().templates["python"]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for name in ("PLAN.md", "TASKS.md", "ACCEPTANCE.md"):
                (output / name).write_text("old")
            template.render(output, {"title": "x", "goal": "y", "allowed_files": "z"}, force=True)
            self.assertNotEqual("old", (output / "PLAN.md").read_text())

    def test_auto_detection_for_each_project_type(self):
        cases = {"pyproject.toml": "python", "platformio.ini": "embedded", "hyprland.conf": "hyprland"}
        manager = self.manager()
        for marker, expected in cases.items():
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                (Path(directory) / marker).write_text("")
                self.assertEqual(expected, manager.detect(Path(directory)).name)

    def test_ambiguous_and_unknown_detection_are_blocked(self):
        manager = self.manager()
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            with self.assertRaises(MODULE.TemplateError):
                manager.detect(repo)
            (repo / "pyproject.toml").write_text("")
            (repo / "platformio.ini").write_text("")
            with self.assertRaises(MODULE.TemplateError):
                manager.detect(repo)

    def test_required_and_unknown_variables_are_rejected(self):
        template = self.manager().templates["embedded"]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(MODULE.TemplateError):
                template.render(Path(directory), {"title": "x", "goal": "y"})
            with self.assertRaises(MODULE.TemplateError):
                template.render(Path(directory), {
                    "title": "x", "goal": "y", "allowed_files": "z", "unexpected": "no"
                })

    def test_metadata_paths_are_safe_and_version_is_strict(self):
        for template in self.manager().templates.values():
            for item in template.files:
                self.assertFalse(Path(item["source"]).is_absolute())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "PLAN.md.tmpl").write_text("hello")
            metadata = {
                "name": root.name,
                "description": "test",
                "version": "1.0.0junk",
                "markers": ["x"],
                "variables": {},
                "files": [{"source": "PLAN.md.tmpl", "destination": "PLAN.md"}],
            }
            (root / "template.json").write_text(json.dumps(metadata))
            with self.assertRaises(MODULE.TemplateError):
                MODULE.WorkflowTemplate.load(root)

    def test_rejects_required_variable_with_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "PLAN.md.tmpl").write_text("{{ value }}")
            metadata = {
                "name": root.name, "description": "test", "version": "1.0.0", "markers": ["x"],
                "variables": {"value": {"required": True, "default": "unsafe"}},
                "files": [{"source": "PLAN.md.tmpl", "destination": "PLAN.md"}],
            }
            (root / "template.json").write_text(json.dumps(metadata))
            with self.assertRaises(MODULE.TemplateError):
                MODULE.WorkflowTemplate.load(root)

    def test_rejects_duplicate_destination_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / "demo"
            root.mkdir()
            (root / "one.tmpl").write_text("one")
            outside = parent / "outside.tmpl"
            outside.write_text("outside")
            metadata = {
                "name": "demo", "description": "test", "version": "1.0.0", "markers": ["x"],
                "variables": {},
                "files": [
                    {"source": "one.tmpl", "destination": "same.md"},
                    {"source": "one.tmpl", "destination": "same.md"},
                ],
            }
            (root / "template.json").write_text(json.dumps(metadata))
            with self.assertRaises(MODULE.TemplateError):
                MODULE.WorkflowTemplate.load(root)
            (root / "escape.tmpl").symlink_to(outside)
            metadata["files"] = [{"source": "escape.tmpl", "destination": "safe.md"}]
            (root / "template.json").write_text(json.dumps(metadata))
            with self.assertRaises(MODULE.TemplateError):
                MODULE.WorkflowTemplate.load(root)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_rejects_output_symlink_escape(self):
        template = self.manager().templates["python"]
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            output = base / "output"
            outside = base / "outside"
            output.mkdir()
            outside.mkdir()
            (output / "PLAN.md").symlink_to(outside / "PLAN.md")
            with self.assertRaises(MODULE.TemplateError):
                template.render(output, {"title": "x", "goal": "y", "allowed_files": "z"}, force=True)


if __name__ == "__main__":
    unittest.main()
