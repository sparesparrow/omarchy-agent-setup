import json
import ast
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PromptCatalogPanelTests(unittest.TestCase):
    def test_research_workspace_uses_supported_dispatch_and_isolates_profiles(self):
        with tempfile.TemporaryDirectory(prefix="research workspace test ") as directory:
            root = Path(directory)
            bindir = root / "bin"
            bindir.mkdir()
            calls = root / "calls.jsonl"
            hyprctl = bindir / "hyprctl"
            launcher = bindir / "omarchy-launch-webapp"
            sleeper = bindir / "sleep"
            hyprctl.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$CALLS\"\n", encoding="utf-8"
            )
            launcher.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$CALLS\"\n", encoding="utf-8"
            )
            sleeper.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            for executable in (hyprctl, launcher, sleeper):
                executable.chmod(0o755)

            env = os.environ.copy()
            env.update({"HOME": str(root / "home"), "PATH": f"{bindir}:/usr/bin:/bin",
                        "CALLS": str(calls), "RESEARCH_WS": "7"})
            subprocess.run(
                ["bash", str(ROOT / "workspace/research-workspace.sh")],
                check=True, capture_output=True, text=True, env=env, timeout=5,
            )
            self.assertEqual(
                calls.read_text(encoding="utf-8").splitlines(),
                [
                    'dispatch hl.dsp.focus({ workspace = "7" })',
                    'https://www.perplexity.ai/ --user-data-dir=' + str(root / "home/.local/share/research-profiles/perplexity"),
                    'https://gemini.google.com/ --user-data-dir=' + str(root / "home/.local/share/research-profiles/gemini"),
                ],
            )
            for profile in ("perplexity", "gemini"):
                self.assertTrue((root / f"home/.local/share/research-profiles/{profile}").is_dir())

            calls.unlink()
            invalid_env = env | {"RESEARCH_WS": '4"; touch /tmp/not-allowed'}
            result = subprocess.run(
                ["bash", str(ROOT / "workspace/research-workspace.sh")],
                capture_output=True, text=True, env=invalid_env, timeout=5,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("positive workspace number", result.stderr)
            self.assertFalse(calls.exists())

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
        keys += re.findall(r'root\.t\("([a-z0-9.]+)"\)', panel)
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
        expected_targets = {
            "action.research.title": ["bash", "/workspace/research-workspace.sh"],
            "action.plan.title": ["omarchy-agent-prompt", None],
            "action.catalog.title": ["xdg-open", "/prompt-catalog/README.md"],
            "action.audit.title": ["xdg-open", "/docs/no-extra-payment-audit.md"],
            "action.notes.title": ["xdg-open", "/research/README.md"],
        }
        self.assertEqual(len(actions), 5)

        def evaluate_qml_string_array(expression, plugin_dir):
            expression = re.sub(r"\bpluginDir\b", repr(str(plugin_dir)), expression)
            tree = ast.parse(expression, mode="eval")

            def value(node):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    return node.value
                if isinstance(node, ast.List):
                    return [value(item) for item in node.elts]
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                    return value(node.left) + value(node.right)
                raise AssertionError(f"unsupported action argument syntax: {ast.dump(node)}")

            return value(tree.body)

        # Resolve the actual QML array expressions against an installation path
        # with spaces, then pass each argv through a harmless capture process.
        with tempfile.TemporaryDirectory(prefix="agent plugin path ") as directory:
            root = Path(directory)
            for relative in (
                "workspace/research-workspace.sh", "AGENTS.md",
                "prompts/orchestrator-claude.md", "prompt-catalog/README.md",
                "docs/no-extra-payment-audit.md", "research/README.md",
            ):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("fixture", encoding="utf-8")
            capture = root / "capture.py"
            capture.write_text(
                "import json,sys; print(json.dumps(sys.argv[1:]))\n", encoding="utf-8"
            )
            for title, target_parts in expected_targets.items():
                with self.subTest(action=title):
                    match = [action for action in actions if f'titleKey: "{title}"' in action]
                    self.assertEqual(len(match), 1)
                    command_match = re.search(r"command:\s*(\[.*?\])", match[0], re.DOTALL)
                    self.assertIsNotNone(command_match)
                    argv = evaluate_qml_string_array(command_match.group(1), root)
                    self.assertIsInstance(argv, list)
                    self.assertTrue(all(isinstance(arg, str) for arg in argv))
                    self.assertEqual(argv[0], target_parts[0])
                    if target_parts[1] is not None:
                        self.assertIn(str(root) + target_parts[1], argv[1])
                    else:
                        self.assertIn(str(root) + "/AGENTS.md", argv[1])
                        self.assertIn(str(root) + "/prompts/orchestrator-claude.md", argv[1])
                    result = subprocess.run(
                        [sys.executable, str(capture), *argv],
                        check=True, capture_output=True, text=True,
                    )
                    self.assertEqual(json.loads(result.stdout), argv)
                    self.assertTrue("bash -c" not in " ".join(argv))


if __name__ == "__main__":
    unittest.main()
