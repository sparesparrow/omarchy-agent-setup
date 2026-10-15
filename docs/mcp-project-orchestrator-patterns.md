# Reused MCP Project Orchestrator patterns

This plugin selectively adapts four portable ideas from `sparesparrow/mcp-project-orchestrator`:

- discover templates from directories containing versioned `template.json` metadata;
- declare required and default variables rather than embedding project assumptions in prompts;
- render several workflow artifacts from one validated context;
- list and select reusable project templates through a small command-line interface.

The local adaptation uses only the Python standard library and generates the existing `PLAN.md`, `TASKS.md`, and `ACCEPTANCE.md` contracts. It adds focused templates for Python, embedded, and Hyprland work, matching issue #14.

It intentionally excludes AWS integrations, Terraform, OpenSSL/FIPS deployment, Cursor configuration, Conan packaging, Docker scaffolding, Mermaid rendering, generated prompt dumps, automotive examples, and long-running MCP servers. Those features are useful in the source project but would expand this plugin's permissions, dependencies, and scope.

The source repository remains design inspiration, not a package or runtime dependency. Templates should be ported individually, reviewed, and tested here.
