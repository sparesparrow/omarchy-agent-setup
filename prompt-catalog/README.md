# Local prompt catalog

The catalog adapts the portable prompt entity from `sparesparrow/mcp-prompts`: stable ID, name, description, category, tags, semantic version, source, and declared variables. It remains local, file-backed, read-only, and dependency-free.

```bash
# Latest version of each prompt
python3 orchestration/prompt_catalog.py list

# Filter metadata
python3 orchestration/prompt_catalog.py list --category role --tag evidence

# Inspect one exact version
python3 orchestration/prompt_catalog.py show role.evaluator --version 1.0.0

# Render to stdout
python3 orchestration/prompt_catalog.py render workflow.task-brief \
  --var 'goal=Reject malformed dispatch jobs' \
  --var 'allowed_files=research/**' \
  --var 'acceptance=Focused tests pass and malformed input is rejected'

# Render to a new file
python3 orchestration/prompt_catalog.py render workflow.task-brief \
  --var 'goal=Validate the plugin' \
  --var 'allowed_files=Panel.qml test.sh' \
  --var 'acceptance=./test.sh passes' \
  --output /tmp/task-brief.md
```

Catalog validation rejects duplicate versions, unsafe paths, malformed semantic versions, mismatched variables, unknown render values, and missing required values. Output files are not overwritten unless `--force` is explicit.

The tool never starts an MCP or HTTP server, executes a rendered prompt, invokes an agent, sends telemetry, accesses a network or database, or mutates the catalog. Git remains the storage, history, review, and rollback layer.
