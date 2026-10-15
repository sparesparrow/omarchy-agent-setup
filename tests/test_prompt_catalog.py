import json
import tempfile
import unittest
from pathlib import Path

from orchestration.prompt_catalog import CatalogError, PromptCatalog, parse_variables, write_output


ROOT = Path(__file__).resolve().parents[1]


class PromptCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = PromptCatalog(ROOT, ROOT / "prompt-catalog/catalog.json")
        self.catalog.load()

    def test_catalog_contains_role_and_workflow_prompts(self):
        self.assertEqual(
            {entry.prompt_id for entry in self.catalog.list()},
            {"role.orchestrator", "role.executor", "role.evaluator", "workflow.task-brief"},
        )

    def test_filters_by_category_and_tag(self):
        roles = self.catalog.list(category="role")
        evidence = self.catalog.list(tag="evidence")
        self.assertEqual(len(roles), 3)
        self.assertEqual({entry.prompt_id for entry in evidence}, {
            "role.executor", "role.evaluator", "workflow.task-brief"
        })

    def test_get_selects_latest_semantic_version(self):
        entry = self.catalog.get("role.orchestrator")
        self.assertEqual(entry.version, "1.0.0")
        self.assertEqual(self.catalog.get("role.orchestrator", "1.0.0"), entry)

    def test_metadata_keeps_relative_source_path(self):
        entry = self.catalog.get("role.orchestrator")
        self.assertEqual(entry.metadata()["source"], "prompts/orchestrator-claude.md")

    def test_renders_required_and_default_variables(self):
        rendered = self.catalog.get("workflow.task-brief").render({
            "goal": "Keep scope bounded",
            "allowed_files": "prompts/**",
            "acceptance": "Catalog tests pass",
        })
        self.assertIn("Keep scope bounded", rendered)
        self.assertIn("English", rendered)
        self.assertNotIn("{{", rendered)

    def test_preserves_token_like_text_in_supplied_values(self):
        rendered = self.catalog.get("workflow.task-brief").render({
            "goal": "Document {{raw_token}}",
            "allowed_files": "docs/**",
            "acceptance": "The example remains literal",
        })
        self.assertIn("{{raw_token}}", rendered)

    def test_rejects_missing_and_unknown_variables(self):
        entry = self.catalog.get("workflow.task-brief")
        with self.assertRaisesRegex(CatalogError, "missing required variable"):
            entry.render({})
        with self.assertRaisesRegex(CatalogError, "unknown variables"):
            entry.render({
                "goal": "x", "allowed_files": "y", "acceptance": "z", "secret": "no"
            })

    def test_rejects_unknown_prompt_and_duplicate_cli_variables(self):
        with self.assertRaisesRegex(CatalogError, "prompt not found"):
            self.catalog.get("role.missing")
        with self.assertRaisesRegex(CatalogError, "duplicate variable"):
            parse_variables(["goal=a", "goal=b"])

    def test_refuses_output_overwrite_and_directory_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "prompt.md"
            output.write_text("keep")
            with self.assertRaisesRegex(CatalogError, "refusing to overwrite"):
                write_output(output, "replace", False)
            self.assertEqual(output.read_text(), "keep")
            directory = Path(tmp) / "directory"
            directory.mkdir()
            with self.assertRaisesRegex(CatalogError, "output is a directory"):
                write_output(directory, "replace", True)

    def test_catalog_rejects_source_metadata_variable_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            root.joinpath("prompt.md").write_text("Hello {{name}}")
            data = {
                "schema_version": 1,
                "prompts": [{
                    "id": "test.prompt", "name": "Test", "description": "Test prompt",
                    "category": "test", "tags": ["test"], "version": "1.0.0",
                    "source": "prompt.md", "variables": {}
                }]
            }
            root.joinpath("catalog.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(CatalogError, "source variables differ"):
                PromptCatalog(root, root / "catalog.json").load()

    def test_catalog_rejects_malformed_template_variable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            root.joinpath("prompt.md").write_text("Hello {{Name}}")
            data = {
                "schema_version": 1,
                "prompts": [{
                    "id": "test.prompt", "name": "Test", "description": "Test prompt",
                    "category": "test", "tags": ["test"], "version": "1.0.0",
                    "source": "prompt.md", "variables": {}
                }]
            }
            root.joinpath("catalog.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(CatalogError, "malformed template variable"):
                PromptCatalog(root, root / "catalog.json").load()


if __name__ == "__main__":
    unittest.main()
