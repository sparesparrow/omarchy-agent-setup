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

## Role handoff dispatcher

Create a job directory containing non-empty `PLAN.md`, `TASKS.md`, and
`ACCEPTANCE.md` files (the canonical formats are in `templates/`). Then inspect
the quota-safe execution decision without launching an agent:

```bash
python3 orchestration/handoff_dispatcher.py \
  --router-state ~/.local/state/omarchy-agents/state.json \
  route .agents/my-job --phase execute --dry-run
```

After the executor writes `HANDOFF.md`, use `--phase evaluate`; the result names
Grok or a fresh Gemini session and points it at `EVALUATION.md`. Record an
evaluator result with `failed <job-dir>` or `passed <job-dir>`. Two recorded
failures return the job to Claude for replanning. A pass resets the loop counter
and returns ownership to the user.

The dispatcher only validates trusted handoff files and prints JSON decisions.
It does not start agents, read research report text, spend quota, access OAuth
sessions, push, open pull requests, or merge. An `ask` or `pause` action must be
resolved by the user; Claude is never selected automatically as evaluator.
Research jobs may use `.agents/research/<job-id>/` as their job directory after
their planning files are created.
