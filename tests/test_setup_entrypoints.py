import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class SetupEntrypointTests(unittest.TestCase):
    def test_panel_uses_setup_scripts_and_drops_removed_actions(self):
        panel = (ROOT / "Panel.qml").read_text(encoding="utf-8")
        self.assertNotIn("action.audit.title", panel)
        self.assertNotIn("action.notes.title", panel)
        for script in (
            "setup/openclaw-cs.sh",
            "setup/voxtype.sh",
            "setup/plugins.sh",
            "setup/omp-presets.sh",
            "setup/mcp-skills.sh",
        ):
            self.assertIn(script, panel)
            self.assertTrue((ROOT / script).is_file())

    def test_catalog_contains_project_and_openclaw_prompts(self):
        catalog = json.loads((ROOT / "prompt-catalog/catalog.json").read_text(encoding="utf-8"))
        ids = {item["id"] for item in catalog["prompts"]}
        self.assertTrue({"openclaw.agent-router", "project.mia", "project.libertin", "project.human-action", "workflow.project-orchestration", "setup.mcp-skills"} <= ids)
