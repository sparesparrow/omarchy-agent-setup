#!/usr/bin/env python3
"""Discover, validate, select and render agent workflow templates."""

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

TOKEN = re.compile(r"{{\s*([a-z][a-z0-9_]*)\s*}}")
NAME = re.compile(r"[a-z][a-z0-9-]*")


class TemplateError(ValueError):
    pass


@dataclass(frozen=True)
class WorkflowTemplate:
    name: str
    description: str
    version: str
    directory: Path
    markers: tuple[str, ...]
    variables: dict
    files: tuple[dict, ...]

    @classmethod
    def load(cls, directory: Path):
        metadata_path = directory / "template.json"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise TemplateError(f"cannot load {metadata_path}: {error}") from error
        required = {"name", "description", "version", "variables", "files"}
        missing = sorted(required - metadata.keys())
        if missing:
            raise TemplateError(f"{metadata_path}: missing {', '.join(missing)}")
        name = metadata["name"]
        if not isinstance(name, str) or not NAME.fullmatch(name) or name != directory.name:
            raise TemplateError(f"{metadata_path}: invalid or mismatched name")
        if not isinstance(metadata["variables"], dict) or not isinstance(metadata["files"], list):
            raise TemplateError(f"{metadata_path}: variables must be an object and files a list")
        markers = metadata.get("markers", [])
        if not isinstance(markers, list) or not all(isinstance(item, str) and item for item in markers):
            raise TemplateError(f"{metadata_path}: markers must be non-empty strings")
        files = []
        for item in metadata["files"]:
            if not isinstance(item, dict) or set(item) != {"source", "destination"}:
                raise TemplateError(f"{metadata_path}: every file needs source and destination")
            for key in ("source", "destination"):
                value = item[key]
                path = PurePosixPath(value) if isinstance(value, str) else None
                if not path or path.is_absolute() or ".." in path.parts:
                    raise TemplateError(f"{metadata_path}: unsafe {key}")
            if not (directory / item["source"]).is_file():
                raise TemplateError(f"{metadata_path}: source does not exist: {item['source']}")
            files.append(item)
        return cls(name, metadata["description"], metadata["version"], directory,
                   tuple(markers), metadata["variables"], tuple(files))

    def values(self, supplied: dict[str, str]):
        unknown = sorted(set(supplied) - set(self.variables))
        if unknown:
            raise TemplateError(f"unknown variables: {', '.join(unknown)}")
        values = {}
        for name, spec in self.variables.items():
            if not isinstance(spec, dict):
                raise TemplateError(f"{self.name}: invalid variable metadata for {name}")
            value = supplied.get(name, spec.get("default"))
            if value is None and spec.get("required", False):
                raise TemplateError(f"missing required variable: {name}")
            values[name] = "" if value is None else str(value)
        return values

    def render(self, output: Path, supplied: dict[str, str], force: bool = False):
        values = self.values(supplied)
        rendered = []
        for item in self.files:
            source = (self.directory / item["source"]).read_text(encoding="utf-8")
            tokens = set(TOKEN.findall(source))
            missing = sorted(tokens - values.keys())
            if missing:
                raise TemplateError(f"{item['source']}: undeclared variables: {', '.join(missing)}")
            content = TOKEN.sub(lambda match: values[match.group(1)], source)
            if TOKEN.search(content):
                raise TemplateError(f"{item['source']}: unresolved variables")
            target = output / item["destination"]
            if target.exists() and not force:
                raise TemplateError(f"refusing to overwrite {target}")
            rendered.append((target, content))
        for target, content in rendered:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return [target for target, _ in rendered]


class TemplateManager:
    def __init__(self, root: Path):
        self.root = root
        self.templates = {}

    def discover(self):
        if not self.root.is_dir():
            raise TemplateError(f"template directory not found: {self.root}")
        templates = {}
        for directory in sorted(path for path in self.root.iterdir() if path.is_dir()):
            template = WorkflowTemplate.load(directory)
            if template.name in templates:
                raise TemplateError(f"duplicate template: {template.name}")
            templates[template.name] = template
        if not templates:
            raise TemplateError("no workflow templates found")
        self.templates = templates
        return templates

    def detect(self, repo: Path):
        matches = []
        for template in self.templates.values():
            if any(any(repo.glob(marker)) for marker in template.markers):
                matches.append(template)
        if len(matches) != 1:
            names = ", ".join(item.name for item in matches) or "none"
            raise TemplateError(f"auto-detection requires exactly one match; found: {names}")
        return matches[0]


def parse_variables(items):
    values = {}
    for item in items:
        if "=" not in item:
            raise TemplateError(f"variable must be NAME=VALUE: {item}")
        name, value = item.split("=", 1)
        if not re.fullmatch(r"[a-z][a-z0-9_]*", name) or name in values:
            raise TemplateError(f"invalid or duplicate variable: {name}")
        values[name] = value
    return values


def main(argv=None):
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--templates", type=Path, default=repo_root / "project-templates")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    render = sub.add_parser("render")
    render.add_argument("template", help="template name or auto")
    render.add_argument("--repo", type=Path, default=Path.cwd())
    render.add_argument("--output", type=Path, required=True)
    render.add_argument("--var", action="append", default=[])
    render.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        manager = TemplateManager(args.templates)
        templates = manager.discover()
        if args.command == "list":
            for template in templates.values():
                print(f"{template.name}\t{template.version}\t{template.description}")
            return 0
        template = manager.detect(args.repo) if args.template == "auto" else templates.get(args.template)
        if template is None:
            raise TemplateError(f"unknown template: {args.template}")
        paths = template.render(args.output, parse_variables(args.var), args.force)
        for path in paths:
            print(path)
        return 0
    except (OSError, TemplateError) as error:
        parser.exit(2, f"BLOCKED: {error}\n")


if __name__ == "__main__":
    main()
