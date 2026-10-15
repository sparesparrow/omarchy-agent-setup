# Research intake (#12) and dispatcher (#3)

## Layout and migration

All paths are relative to this checkout, not the calling working directory:

- `.agents/research/jobs/<job-id>/`: trusted orchestrator prompts.
- `.agents/research/inbox/<job-id>/`: raw browser exports.
- `.agents/research/reviewed/<job-id>/`: reviewed JSON snapshots, still untrusted.

Job IDs are 1-64 ASCII letters/digits/underscores/hyphens, starting with a letter
or digit. output.directory must exactly equal `.agents/research/inbox/<job-id>`.
Edit older jobs explicitly; no automatic migration or deletion occurs.
Existing artifacts are never overwritten. Use a fresh job ID after a partial run.

## Prepare and export

Requires Python 3 on Linux and PyYAML; install dependencies only with approval.
Use trusted orchestrator YAML, not research content:

```bash
python3 research/dispatcher.py research/dispatch.example.yaml
```

Give `.agents/research/jobs/issue-123/codex-browser-task.md` to the browser agent.
Export only perplexity-report.md and gemini-report.md to the job inbox. Stop on
login, CAPTCHA, payment or upgrade prompts. Do not feed raw exports back into a
tool-enabled agent. No watcher/browser launcher is added. #3 remains open.
The #2 PR configures the parent inbox for MCP artifacts; select this job's inbox
explicitly for report exports. The helper ignores other artifacts.

## Human review gate

Run outside an agent session:

```bash
python3 research/input_guard.py issue-123 perplexity
python3 research/input_guard.py issue-123 gemini
```

Output is metadata only. Exit 2 = NEEDS_REVIEW; 3 = QUARANTINED/BLOCKED;
0 = reviewed snapshot created. Raw bytes remain in the inbox. Known override,
role, shell/secret-access patterns and hidden formatting are blocked, not silently
stripped and released. Symlinks, hardlinks, special files, oversized/non-UTF-8,
empty and control-character reports fail closed. False positives are possible.

For NEEDS_REVIEW, a human inspects the exact raw report in a non-agent editor,
removes instructions or replaces it with a factual extract as needed, rescans,
and approves the resulting SHA256:

```bash
python3 research/input_guard.py issue-123 perplexity --approve-sha256 <SHA256>
```

Repeat for Gemini. Only matching bytes are saved in a new
`reviewed/<job-id>/<provider>-<sha256>.json`. trust remains untrusted.
Quarantined reports cannot be released by passing a digest. No automatic
quarantine override exists. Human edits need a new scan/review/digest.

## Limitations: issue #12 stays open

Screening cannot remove or detect every instruction. Novel, multilingual, encoded
or semantic attacks can pass patterns, but still require review. JSON encoding
and trust labels are not enforcement boundaries. Approval is procedural, not
an identity check: a same-user agent could invoke the helper itself. Do not grant
agents approval-command access or reviewed-output write access.

These helpers use descriptor-relative no-symlink opens/creates for fixed paths;
they do not sandbox Playwright/Codex or constrain arbitrary same-user processes.
New directories use 700 and outputs 600; existing permissions are unchanged.
Browser output-dir settings and export instructions are not filesystem isolation.

Synthesis must run in a separately enforced, tool-less worker: no shell, network,
credentials or host-secret mounts; only explicit read-only report snapshots.
Its output also remains untrusted and cannot authorize executor actions.
That worker, OS/tool permission enforcement, and #4 handoff integration are NOT
implemented here. #12 stays open pending those and adversarial end-to-end tests.
Do not rename reviewed data as AGENTS.md or another trusted instruction file.

## Offline tests

```bash
python3 -m unittest discover -s research -p 'test_input_guard.py' -v
```

The plugin test.sh is unchanged; run this suite explicitly. Unit tests do not
establish a complete security boundary or live browser acceptance.

Rationale: least privilege and execution-side permission checks are required,
not just filtering and labels:
https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
