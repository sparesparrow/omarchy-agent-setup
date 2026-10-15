#!/usr/bin/env python3
"""Discover, validate, select and render agent workflow templates."""

import argparse
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

TOKEN = re.compile(r"{{\s*([a-z][a-z0-9_]*)\s*}}")
NAME = re.compile(r"[a-z][a-z0-9-]*")
VARIABLE = re.compile(r"[a-z][a-z0-9_]*")
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")


class TemplateError(ValueError):
    pass


def safe_relative_path(value, field):
    path = PurePosixPath(value) if isinstance(value, str) else None
    if not path or path.is_absolute() or ".." in path.parts:
        raise TemplateError(f"unsafe {field}: {value!r}")
    return path


def ensure_within(path: Path, root: Path, field: str):
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError as error:
        raise TemplateError(f"{field} escapes its root: {path}") from error


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
        allowed = required | {"markers"}
        if not isinstance(metadata, dict) or set(metadata) - allowed:
            raise TemplateError(f"{metadata_path}: unsupported metadata fields")
        missing = sorted(required - metadata.keys())
        if missing:
            raise TemplateError(f"{metadata_path}: missing {', '.join(missing)}")
        name = metadata["name"]
        if not isinstance(name, str) or not NAME.fullmatch(name) or name != directory.name:
            raise TemplateError(f"{metadata_path}: invalid or mismatched name")
        if not isinstance(metadata["description"], str) or not metadata["description"].strip():
            raise TemplateError(f"{metadata_path}: description must be a non-empty string")
        if not isinstance(metadata["version"], str) or not VERSION.fullmatch(metadata["version"]):
            raise TemplateError(f"{metadata_path}: version must be MAJOR.MINOR.PATCH")
        if not isinstance(metadata["variables"], dict) or not isinstance(metadata["files"], list):
            raise TemplateError(f"{metadata_path}: variables must be an object and files a list")
        variables = metadata["variables"]
        for variable, spec in variables.items():
            if not isinstance(variable, str) or not VARIABLE.fullmatch(variable) or not isinstance(spec, dict):
                raise TemplateError(f"{metadata_path}: invalid variable {variable!r}")
            if set(spec) - {"required", "default", "description"}:
                raise TemplateError(f"{metadata_path}: unsupported metadata for variable {variable}")
            if "required" in spec and not isinstance(spec["required"], bool):
                raise TemplateError(f"{metadata_path}: required must be boolean for {variable}")
            if spec.get("required") and "default" in spec:
                raise TemplateError(f"{metadata_path}: required variable {variable} cannot have a default")
            if "description" in spec and not isinstance(spec["description"], str):
                raise TemplateError(f"{metadata_path}: description must be a string for {variable}")
        markers = metadata.get("markers", [])
        if not isinstance(markers, list) or not markers or not all(isinstance(item, str) and item for item in markers):
            raise TemplateError(f"{metadata_path}: markers must be a non-empty list of strings")
        files = []
        destinations = set()
        root = directory.resolve()
        for item in metadata["files"]:
            if not isinstance(item, dict) or set(item) != {"source", "destination"}:
                raise TemplateError(f"{metadata_path}: every file needs source and destination")
            source_relative = safe_relative_path(item["source"], "source")
            destination = safe_relative_path(item["destination"], "destination")
            if str(destination) in destinations:
                raise TemplateError(f"{metadata_path}: duplicate destination: {destination}")
            destinations.add(str(destination))
            source = directory / source_relative
            ensure_within(source, root, "source")
            if not source.is_file():
                raise TemplateError(f"{metadata_path}: source does not exist: {source_relative}")
            files.append({"source": str(source_relative), "destination": str(destination)})
        if not files:
            raise TemplateError(f"{metadata_path}: files must not be empty")
        return cls(name, metadata["description"], metadata["version"], directory,
                   tuple(markers), variables, tuple(files))

    def values(self, supplied: dict[str, str]):
        unknown = sorted(set(supplied) - set(self.variables))
        if unknown:
            raise TemplateError(f"unknown variables: {', '.join(unknown)}")
        values = {}
        for name, spec in self.variables.items():
            value = supplied.get(name, spec.get("default"))
            if value is None and spec.get("required", False):
                raise TemplateError(f"missing required variable: {name}")
            values[name] = "" if value is None else str(value)
        return values

    def render(self, output: Path, supplied: dict[str, str], force: bool = False):
        values = self.values(supplied)
        output_root = output.resolve(strict=False)
        if output.exists() and not output.is_dir():
            raise TemplateError(f"output is not a directory: {output}")
        rendered = []
        for item in self.files:
            source_path = self.directory / item["source"]
            source = source_path.read_text(encoding="utf-8")
            stripped = TOKEN.sub("", source)
            if "{{" in stripped or "}}" in stripped:
                raise TemplateError(f"{item['source']}: malformed template variable")
            tokens = set(TOKEN.findall(source))
            missing = sorted(tokens - values.keys())
            if missing:
                raise TemplateError(f"{item['source']}: undeclared variables: {', '.join(missing)}")
            content = TOKEN.sub(lambda match: values[match.group(1)], source)
            target = output / item["destination"]
            ensure_within(target, output_root, "destination")
            ensure_within(target.parent, output_root, "destination parent")
            if target.exists() and target.is_dir():
                raise TemplateError(f"destination is a directory: {target}")
            if target.exists() and not force:
                raise TemplateError(f"refusing to overwrite {target}")
            rendered.append((target, content))

        staged = []
        try:
            for target, content in rendered:
                target.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent,
                                                 prefix=f".{target.name}.", delete=False) as handle:
                    handle.write(content)
                    staged.append((Path(handle.name), target))
            for temporary, target in staged:
                os.replace(temporary, target)
            return [target for _, target in staged]
        finally:
            for temporary, _ in staged:
                temporary.unlink(missing_ok=True)


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
        if not VARIABLE.fullmatch(name) or name in values:
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
