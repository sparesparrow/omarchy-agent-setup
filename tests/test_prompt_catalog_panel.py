import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PromptCatalogPanelTests(unittest.TestCase):
    def test_catalog_action_opens_only_local_guide(self):
        panel = (ROOT / "Panel.qml").read_text(encoding="utf-8")
        actions = re.findall(r"\{\s*titleKey:.*?\n    \}", panel, re.DOTALL)
        matches = [action for action in actions if 'titleKey: "action.catalog.title"' in action]
        self.assertEqual(len(matches), 1)
        self.assertIn('detailKey: "action.catalog.detail"', matches[0])
        self.assertIn('command: ["xdg-open", pluginDir + "/prompt-catalog/README.md"]', matches[0])
        self.assertEqual(matches[0].count("command:"), 1)
        self.assertTrue((ROOT / "prompt-catalog/README.md").is_file())

    def test_panel_keys_match_both_locales(self):
        panel = (ROOT / "Panel.qml").read_text(encoding="utf-8")
        keys = re.findall(r'(?:titleKey|detailKey): "([a-z0-9.]+)"', panel)
        keys += re.findall(r'strings\.t\("([a-z0-9.]+)"\)', panel)
        self.assertEqual(len(keys), len(set(keys)))
        for locale in ("en", "cs"):
            with self.subTest(locale=locale):
                catalog = json.loads((ROOT / f"i18n/{locale}.json").read_text(encoding="utf-8"))
                self.assertEqual(set(keys), set(catalog))
                self.assertTrue(all(isinstance(value, str) and value.strip() for value in catalog.values()))

    def test_panel_text_remains_plain(self):
        panel = (ROOT / "Panel.qml").read_text(encoding="utf-8")
        blocks = re.findall(r"Text\s*\{(.*?)\n\s*\}", panel, re.DOTALL)
        self.assertGreaterEqual(len(blocks), 3)
        for block in blocks:
            self.assertIn("textFormat: Text.PlainText", block)

    def test_all_five_actions_keep_structured_arguments_and_resolve_local_targets(self):
        panel = (ROOT / "Panel.qml").read_text(encoding="utf-8")
        actions = re.findall(r"\{\s*titleKey:.*?\n    \}", panel, re.DOTALL)
        expected = {
            "action.research.title": 'command: ["bash", pluginDir + "/workspace/research-workspace.sh"]',
            "action.plan.title": 'command: ["omarchy-agent-prompt", "Read " + pluginDir',
            "action.catalog.title": 'command: ["xdg-open", pluginDir + "/prompt-catalog/README.md"]',
            "action.audit.title": 'command: ["xdg-open", pluginDir + "/docs/no-extra-payment-audit.md"]',
            "action.notes.title": 'command: ["xdg-open", pluginDir + "/research/README.md"]',
        }
        self.assertEqual(len(actions), 5)
        for title, command in expected.items():
            with self.subTest(action=title):
                match = [action for action in actions if f'titleKey: "{title}"' in action]
                self.assertEqual(len(match), 1)
                self.assertIn(command, match[0])
                self.assertNotRegex(match[0], r"bash\s+-c|shellQuote|execDetached")

        # Exercise the same argv boundary against a temporary installation path
        # with spaces. This is a subprocess contract check, not live QML execution.
        with tempfile.TemporaryDirectory(prefix="agent plugin path ") as directory:
            root = Path(directory)
            target = root / "prompt-catalog" / "README.md"
            target.parent.mkdir()
            target.write_text("local guide", encoding="utf-8")
            capture = root / "capture.py"
            capture.write_text(
                "import json,sys; print(json.dumps(sys.argv[1:]))\n", encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, str(capture), "xdg-open", str(target)],
                check=True, capture_output=True, text=True,
            )
            self.assertEqual(json.loads(result.stdout), ["xdg-open", str(target)])
            self.assertTrue(target.is_file())


if __name__ == "__main__":
    unittest.main()
