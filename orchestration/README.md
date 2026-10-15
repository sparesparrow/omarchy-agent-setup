# Workflow templates

List available project types:

```bash
python3 orchestration/workflow_templates.py list
```

Render a workflow explicitly:

```bash
python3 orchestration/workflow_templates.py render python \
  --output .agents/example \
  --var 'title=Validate dispatch jobs' \
  --var 'goal=Reject malformed dispatch files' \
  --var 'allowed_files=research/**'
```

Use `render auto --repo /path/to/project` only when exactly one project type matches. Ambiguous and unknown repositories stop with `BLOCKED`; choose the template explicitly instead. Existing files are not overwritten unless `--force` is supplied.

The rendered files are planning artifacts only. Rendering does not execute generated commands, install packages, access credentials, invoke MCP servers, or modify the target project outside the selected output directory.
