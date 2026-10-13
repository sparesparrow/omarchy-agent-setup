# Research dispatcher

Turns a `dispatch.yaml` written by Claude into ready-to-run research jobs.

## Use
```bash
pip install pyyaml
cp research/dispatch.example.yaml research/dispatch.yaml   # edit
python3 research/dispatcher.py research/dispatch.yaml
```
Then give `.agents/research/<job-id>/codex-browser-task.md` to Codex (needs #1 and #2 set up).

## What it does
- Validates the job (required keys, providers `perplexity` / `gemini`, a focus for each).
- Writes one prompt per provider and a browser task for Codex.
- Results land in `.agents/research/<job-id>/inbox/`, treated as untrusted until synthesized (#4).

## Not done yet
- It prepares jobs but does not watch a folder or launch Codex automatically.
- The Deep Research UI changes often; Codex has to follow the steps by looking at the page, so expect to tweak the task text.
- Not tested against the real apps.
