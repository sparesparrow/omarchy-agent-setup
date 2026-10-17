import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_ACTIONS = {
    "action.research.title": 'command: ["bash", pluginDir + "/workspace/research-workspace.sh"]',
    "action.openclaw.title": 'command: ["bash", pluginDir + "/setup/openclaw-cs.sh"]',
    "action.voxtype.title": 'command: ["bash", pluginDir + "/setup/voxtype.sh"]',
    "action.plugins.title": 'command: ["bash", pluginDir + "/setup/plugins.sh"]',
    "action.ecosystem.title": 'command: ["bash", pluginDir + "/setup/omarchy-ecosystem.sh"]',
    "action.omp.title": 'command: ["bash", pluginDir + "/setup/omp-presets.sh"]',
    "action.mia.title": 'command: ["bash", pluginDir + "/setup/mia-voice.sh"]',
    "action.catalog.title": 'command: ["xdg-open", pluginDir + "/prompt-catalog/README.md"]',
    "action.mcp.title": 'command: ["bash", pluginDir + "/setup/mcp-skills.sh"]',
    "action.team.title": 'command: ["bash", pluginDir + "/setup/agent-team.sh"]',
    "action.repositories.title": 'command: ["bash", pluginDir + "/setup/github-repositories.sh"]',
}
REMOVED_ACTIONS = ("action.plan.title", "action.audit.title", "action.notes.title")


def panel_actions():
    panel = (ROOT / "Panel.qml").read_text(encoding="utf-8")
    return panel, re.findall(r"\{\s*titleKey:.*?\n    \}", panel, re.DOTALL)


class PromptCatalogPanelTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is required to execute panel JavaScript")
    def test_keyboard_navigation_reaches_every_action_and_wraps(self):
        panel, actions = panel_actions()
        functions = []
        for name in ("moveFocus", "activateFocused"):
            match = re.search(rf"  function {name}\([^)]*\) \{{.*?\n  \}}", panel, re.DOTALL)
            self.assertIsNotNone(match, name)
            functions.append("root." + name + " = " + match.group(0).strip().replace(name, "", 1))
        action_array = re.search(r"readonly property var actions: (\[.*?\n  \])", panel, re.DOTALL)
        self.assertIsNotNone(action_array)
        script = """
const assert = require('node:assert/strict');
const pluginDir = '/test plugin';
const dispatched = [];
const root = {focusIndex: 0, language: 'cs', run: command => dispatched.push(command)};
root.actions = ACTIONS;
FUNCTIONS
const count = root.actions.length + 2;
root.activateFocused();
assert.equal(root.language, 'en');
root.moveFocus(1);
root.activateFocused();
assert.equal(root.language, 'cs');
for (let index = 0; index < root.actions.length; index++) {
    root.moveFocus(1);
    assert.equal(root.focusIndex, index + 2);
    root.activateFocused();
}
assert.deepEqual(dispatched, root.actions.map(action => action.command));
root.moveFocus(1);
assert.equal(root.focusIndex, 0);
for (let index = count - 1; index >= 0; index--) {
    root.moveFocus(-1);
    assert.equal(root.focusIndex, index);
}
""".replace("ACTIONS", action_array.group(1)).replace("FUNCTIONS", "\n".join(functions))
        result = subprocess.run(
            [shutil.which("node"), "-e", script], capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

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
            recorded = calls.read_text(encoding="utf-8").splitlines()
            self.assertEqual(recorded[0], 'dispatch hl.dsp.focus({ workspace = "7" })')
            self.assertCountEqual(
                recorded,
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
        _, actions = panel_actions()
        matches = [action for action in actions if 'titleKey: "action.catalog.title"' in action]
        self.assertEqual(len(matches), 1)
        self.assertIn('detailKey: "action.catalog.detail"', matches[0])
        self.assertIn(EXPECTED_ACTIONS["action.catalog.title"], matches[0])
        self.assertEqual(matches[0].count("command:"), 1)
        self.assertTrue((ROOT / "prompt-catalog/README.md").is_file())

    def test_panel_keys_match_both_locales(self):
        panel, _ = panel_actions()
        keys = re.findall(r'(?:titleKey|detailKey): "([a-z0-9.]+)"', panel)
        keys += re.findall(r'root\.t\("([a-z0-9.]+)"\)', panel)
        self.assertEqual(len(keys), len(set(keys)))
        for locale in ("en", "cs"):
            with self.subTest(locale=locale):
                catalog = json.loads((ROOT / f"i18n/{locale}.json").read_text(encoding="utf-8"))
                self.assertEqual(set(keys), set(catalog))
                self.assertTrue(all(isinstance(value, str) and value.strip() for value in catalog.values()))

    def test_panel_text_remains_plain(self):
        panel, _ = panel_actions()
        blocks = re.findall(r"Text\s*\{(.*?)\n\s*\}", panel, re.DOTALL)
        self.assertGreaterEqual(len(blocks), 3)
        for block in blocks:
            self.assertIn("textFormat: Text.PlainText", block)

    def test_removed_actions_are_absent_from_panel_and_catalogs(self):
        panel, _ = panel_actions()
        for removed in REMOVED_ACTIONS:
            prefix = removed.removesuffix(".title")
            with self.subTest(action=removed):
                self.assertNotIn(removed, panel)
                for locale in ("en", "cs"):
                    catalog = json.loads((ROOT / f"i18n/{locale}.json").read_text(encoding="utf-8"))
                    self.assertFalse([key for key in catalog if key.startswith(prefix + ".")])

    def test_all_actions_keep_structured_arguments_and_resolve_local_targets(self):
        _, actions = panel_actions()
        self.assertEqual(len(actions), len(EXPECTED_ACTIONS))
        for title, command in EXPECTED_ACTIONS.items():
            with self.subTest(action=title):
                match = [action for action in actions if f'titleKey: "{title}"' in action]
                self.assertEqual(len(match), 1)
                self.assertIn(command, match[0])
                self.assertEqual(match[0].count("command:"), 1)
                self.assertNotRegex(match[0], r"bash\s+-c|shellQuote|execDetached")
                target = re.search(r'"/([^"]+)"\]', command).group(1)
                self.assertTrue((ROOT / target).is_file(), target)

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
            for command in EXPECTED_ACTIONS.values():
                relative = re.search(r'"/([^"]+)"\]', command).group(1)
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("fixture", encoding="utf-8")
            capture = root / "capture.py"
            capture.write_text(
                "import json,sys; print(json.dumps(sys.argv[1:]))\n", encoding="utf-8"
            )
            for title, command in EXPECTED_ACTIONS.items():
                with self.subTest(action=title):
                    match = [action for action in actions if f'titleKey: "{title}"' in action]
                    self.assertEqual(len(match), 1)
                    command_match = re.search(r"command:\s*(\[.*?\])", match[0], re.DOTALL)
                    self.assertIsNotNone(command_match)
                    argv = evaluate_qml_string_array(command_match.group(1), root)
                    self.assertIsInstance(argv, list)
                    self.assertTrue(all(isinstance(arg, str) for arg in argv))
                    expected_argv = evaluate_qml_string_array(command.removeprefix("command: "), root)
                    self.assertEqual(argv, expected_argv)
                    self.assertEqual(len(argv), 2)
                    self.assertTrue(Path(argv[1]).is_file())
                    result = subprocess.run(
                        [sys.executable, str(capture), *argv],
                        check=True, capture_output=True, text=True,
                    )
                    self.assertEqual(json.loads(result.stdout), argv)
                    self.assertTrue("bash -c" not in " ".join(argv))


if __name__ == "__main__":
    unittest.main()
