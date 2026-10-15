#!/usr/bin/env python3
"""Validate, query, and render the repository's local prompt catalog."""

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

TOKEN = re.compile(r"{{\s*([a-z][a-z0-9_]*)\s*}}")
PROMPT_ID = re.compile(r"[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+")
VARIABLE = re.compile(r"[a-z][a-z0-9_]*")
VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


class CatalogError(ValueError):
    pass


def safe_relative_path(value, field):
    path = PurePosixPath(value) if isinstance(value, str) else None
    if not path or path.is_absolute() or ".." in path.parts:
        raise CatalogError(f"unsafe {field}: {value!r}")
    return path


@dataclass(frozen=True)
class PromptVersion:
    prompt_id: str
    name: str
    description: str
    category: str
    tags: tuple[str, ...]
    version: str
    source: Path
    variables: dict

    @property
    def version_key(self):
        return tuple(int(part) for part in self.version.split("."))

    def template(self):
        try:
            return self.source.read_text(encoding="utf-8")
        except OSError as error:
            raise CatalogError(f"cannot read {self.source}: {error}") from error

    def render(self, supplied):
        unknown = sorted(set(supplied) - set(self.variables))
        if unknown:
            raise CatalogError(f"unknown variables: {', '.join(unknown)}")
        values = {}
        for name, spec in self.variables.items():
            value = supplied.get(name, spec.get("default"))
            if value is None and spec.get("required", False):
                raise CatalogError(f"missing required variable: {name}")
            values[name] = "" if value is None else str(value)
        content = TOKEN.sub(lambda match: values[match.group(1)], self.template())
        if TOKEN.search(content):
            raise CatalogError("rendered prompt contains unresolved variables")
        return content

    def metadata(self):
        return {
            "id": self.prompt_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tags": list(self.tags),
            "version": self.version,
            "source": str(self.source),
            "variables": self.variables,
        }


class PromptCatalog:
    def __init__(self, repo_root, catalog_path):
        self.repo_root = repo_root.resolve()
        self.catalog_path = catalog_path
        self.entries = {}

    def load(self):
        try:
            data = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CatalogError(f"cannot load {self.catalog_path}: {error}") from error
        if data.get("schema_version") != 1 or not isinstance(data.get("prompts"), list):
            raise CatalogError("catalog requires schema_version 1 and a prompts list")
        entries = {}
        for raw in data["prompts"]:
            entry = self._parse_entry(raw)
            key = (entry.prompt_id, entry.version)
            if key in entries:
                raise CatalogError(f"duplicate prompt version: {entry.prompt_id}@{entry.version}")
            entries[key] = entry
        if not entries:
            raise CatalogError("prompt catalog is empty")
        self.entries = entries
        return entries

    def _parse_entry(self, raw):
        required = {"id", "name", "description", "category", "tags", "version", "source", "variables"}
        if not isinstance(raw, dict) or set(raw) != required:
            raise CatalogError("every prompt must contain exactly the documented metadata fields")
        if not PROMPT_ID.fullmatch(raw["id"]):
            raise CatalogError(f"invalid prompt id: {raw['id']!r}")
        if not VERSION.fullmatch(raw["version"]):
            raise CatalogError(f"invalid semantic version: {raw['version']!r}")
        for field in ("name", "description", "category"):
            if not isinstance(raw[field], str) or not raw[field].strip():
                raise CatalogError(f"{raw['id']}: {field} must be a non-empty string")
        if not isinstance(raw["tags"], list) or not all(isinstance(tag, str) and tag for tag in raw["tags"]):
            raise CatalogError(f"{raw['id']}: tags must be non-empty strings")
        if len(raw["tags"]) != len(set(raw["tags"])):
            raise CatalogError(f"{raw['id']}: tags must be unique")
        source_relative = safe_relative_path(raw["source"], "source")
        source = (self.repo_root / source_relative).resolve()
        try:
            source.relative_to(self.repo_root)
        except ValueError as error:
            raise CatalogError(f"source escapes repository: {raw['source']}") from error
        if not source.is_file():
            raise CatalogError(f"prompt source does not exist: {raw['source']}")
        variables = raw["variables"]
        if not isinstance(variables, dict):
            raise CatalogError(f"{raw['id']}: variables must be an object")
        for name, spec in variables.items():
            if not VARIABLE.fullmatch(name) or not isinstance(spec, dict):
                raise CatalogError(f"{raw['id']}: invalid variable {name!r}")
            if set(spec) - {"required", "default", "description"}:
                raise CatalogError(f"{raw['id']}: unsupported metadata for variable {name}")
            if "required" in spec and not isinstance(spec["required"], bool):
                raise CatalogError(f"{raw['id']}: required must be boolean for {name}")
            if spec.get("required") and "default" in spec:
                raise CatalogError(f"{raw['id']}: required variable {name} cannot have a default")
        tokens = set(TOKEN.findall(source.read_text(encoding="utf-8")))
        if tokens != set(variables):
            raise CatalogError(
                f"{raw['id']}: source variables differ; source={sorted(tokens)}, metadata={sorted(variables)}"
            )
        return PromptVersion(raw["id"], raw["name"], raw["description"], raw["category"],
                             tuple(raw["tags"]), raw["version"], source, variables)

    def get(self, prompt_id, version=None):
        candidates = [entry for (entry_id, _), entry in self.entries.items() if entry_id == prompt_id]
        if version is not None:
            candidates = [entry for entry in candidates if entry.version == version]
        if not candidates:
            suffix = f"@{version}" if version else ""
            raise CatalogError(f"prompt not found: {prompt_id}{suffix}")
        return max(candidates, key=lambda entry: entry.version_key)

    def list(self, category=None, tag=None, all_versions=False):
        entries = list(self.entries.values())
        if category:
            entries = [entry for entry in entries if entry.category == category]
        if tag:
            entries = [entry for entry in entries if tag in entry.tags]
        if not all_versions:
            latest = {}
            for entry in entries:
                current = latest.get(entry.prompt_id)
                if current is None or entry.version_key > current.version_key:
                    latest[entry.prompt_id] = entry
            entries = list(latest.values())
        return sorted(entries, key=lambda entry: (entry.prompt_id, entry.version_key))


def parse_variables(items):
    values = {}
    for item in items:
        if "=" not in item:
            raise CatalogError(f"variable must be NAME=VALUE: {item}")
        name, value = item.split("=", 1)
        if not VARIABLE.fullmatch(name) or name in values:
            raise CatalogError(f"invalid or duplicate variable: {name}")
        values[name] = value
    return values


def write_output(path, content, force):
    if path.exists() and not force:
        raise CatalogError(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main(argv=None):
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=repo_root / "prompt-catalog/catalog.json")
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list")
    listing.add_argument("--category")
    listing.add_argument("--tag")
    listing.add_argument("--all-versions", action="store_true")
    show = sub.add_parser("show")
    show.add_argument("prompt_id")
    show.add_argument("--version")
    render = sub.add_parser("render")
    render.add_argument("prompt_id")
    render.add_argument("--version")
    render.add_argument("--var", action="append", default=[])
    render.add_argument("--output", type=Path)
    render.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        catalog = PromptCatalog(repo_root, args.catalog)
        catalog.load()
        if args.command == "list":
            for entry in catalog.list(args.category, args.tag, args.all_versions):
                print(f"{entry.prompt_id}\t{entry.version}\t{entry.category}\t{','.join(entry.tags)}")
            return 0
        entry = catalog.get(args.prompt_id, args.version)
        if args.command == "show":
            print(json.dumps(entry.metadata(), indent=2, sort_keys=True))
            return 0
        content = entry.render(parse_variables(args.var))
        if args.output:
            write_output(args.output, content, args.force)
            print(args.output)
        else:
            print(content, end="" if content.endswith("\n") else "\n")
        return 0
    except (CatalogError, OSError) as error:
        parser.exit(2, f"BLOCKED: {error}\n")


if __name__ == "__main__":
    main()
