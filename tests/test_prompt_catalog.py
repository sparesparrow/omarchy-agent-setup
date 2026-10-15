import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("prompt_catalog", ROOT / "orchestration/prompt_catalog.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PromptCatalogTests(unittest.TestCase):
    def load(self):
        catalog = MODULE.PromptCatalog(ROOT, ROOT / "prompt-catalog/catalog.json")
        catalog.load()
        return catalog

    def test_catalog_filters_and_latest_lookup(self):
        catalog = self.load()
        self.assertEqual("1.0.0", catalog.get("role.evaluator").version)
        self.assertEqual(
            ["role.evaluator", "role.executor"],
            [item.prompt_id for item in catalog.list(category="role", tag="evidence")],
        )

    def test_render_defaults_and_rejects_unknown_values(self):
        entry = self.load().get("workflow.task-brief")
        rendered = entry.render({"goal": "Keep scope small", "allowed_files": "src/**", "acceptance": "tests pass"})
        self.assertIn("Keep scope small", rendered)
        self.assertIn("English", rendered)
        with self.assertRaises(MODULE.CatalogError):
            entry.render({"goal": "x", "allowed_files": "x", "acceptance": "x", "surprise": "x"})

    def test_render_treats_variable_values_as_literal_text(self):
        entry = self.load().get("workflow.task-brief")
        rendered = entry.render(
            {"goal": "Keep {{danger}} literal", "allowed_files": "src/**", "acceptance": "tests pass"}
        )
        self.assertIn("Keep {{danger}} literal", rendered)

    def test_output_overwrite_requires_force(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prompt.md"
            MODULE.write_output(path, "first", False)
            with self.assertRaises(MODULE.CatalogError):
                MODULE.write_output(path, "second", False)
            MODULE.write_output(path, "second", True)
            self.assertEqual("second", path.read_text())

    def test_metadata_is_relative_and_version_is_strict(self):
        catalog = self.load()
        metadata = catalog.get("role.executor").metadata()
        self.assertEqual("prompts/executor-codex.md", metadata["source"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "prompt.md").write_text("hello")
            data = {
                "schema_version": 1,
                "prompts": [{
                    "id": "test.prompt", "name": "Test", "description": "Test", "category": "test",
                    "tags": ["test"], "version": "1.0.0junk", "source": "prompt.md", "variables": {}
                }]
            }
            path = root / "catalog.json"
            path.write_text(json.dumps(data))
            with self.assertRaises(MODULE.CatalogError):
                MODULE.PromptCatalog(root, path).load()

    def test_catalog_requires_exact_top_level_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "catalog.json"
            path.write_text(json.dumps({"schema_version": 1, "prompts": [], "surprise": True}))
            with self.assertRaises(MODULE.CatalogError):
                MODULE.PromptCatalog(root, path).load()

    def test_rejects_required_variable_with_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "prompt.md").write_text("{{ value }}")
            data = {
                "schema_version": 1,
                "prompts": [{
                    "id": "test.prompt", "name": "Test", "description": "Test", "category": "test",
                    "tags": ["test"], "version": "1.0.0", "source": "prompt.md",
                    "variables": {"value": {"required": True, "default": "unsafe"}}
                }]
            }
            path = root / "catalog.json"
            path.write_text(json.dumps(data))
            with self.assertRaises(MODULE.CatalogError):
                MODULE.PromptCatalog(root, path).load()

    def test_rejects_unsafe_source_path_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root.parent / f"{root.name}-outside.md"
            outside.write_text("hello")
            try:
                base = {
                    "id": "test.prompt", "name": "Test", "description": "Test", "category": "test",
                    "tags": ["test"], "version": "1.0.0", "source": "../escape.md", "variables": {}
                }
                path = root / "catalog.json"
                path.write_text(json.dumps({"schema_version": 1, "prompts": [base]}))
                with self.assertRaises(MODULE.CatalogError):
                    MODULE.PromptCatalog(root, path).load()
                (root / "linked.md").symlink_to(outside)
                symlinked = copy.deepcopy(base)
                symlinked["source"] = "linked.md"
                path.write_text(json.dumps({"schema_version": 1, "prompts": [symlinked]}))
                with self.assertRaises(MODULE.CatalogError):
                    MODULE.PromptCatalog(root, path).load()
            finally:
                outside.unlink(missing_ok=True)

    def test_rejects_malformed_or_mismatched_variables(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "catalog.json"
            base = {
                "id": "test.prompt", "name": "Test", "description": "Test", "category": "test",
                "tags": ["test"], "version": "1.0.0", "source": "prompt.md",
                "variables": {"value": {"required": True}}
            }
            for source in ("{{ value", "{{ other }}"):
                (root / "prompt.md").write_text(source)
                path.write_text(json.dumps({"schema_version": 1, "prompts": [base]}))
                with self.assertRaises(MODULE.CatalogError):
                    MODULE.PromptCatalog(root, path).load()


if __name__ == "__main__":
    unittest.main()
