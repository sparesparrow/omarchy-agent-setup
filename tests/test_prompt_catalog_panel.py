import json
from pathlib import Path
import re
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


if __name__ == "__main__":
    unittest.main()
