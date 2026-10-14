# Research synthesis

Turns the raw reports in `.agents/research/<job-id>/inbox/` into a short brief so Claude does not read full reports.

## Use
```bash
python3 research/synthesis/build_task.py .agents/research/issue-123
```
Give `synthesis-task.md` to Gemini (fallback: Codex). It writes `synthesis.md` and `conflicts.md`. Give Claude only those two files and the top source links.

## Design choices
- The helper never reads report text, so injected instructions cannot affect it.
- The prompt tells the agent to treat reports as data and to write only the two outputs.
- Agreement between reports is not treated as proof; shared sources are flagged.

## Not done yet
- Untested with real reports. Source checking depends on the agent being able to open the links.
- No automatic hand-off from the dispatcher (#3); run the helper by hand for now.
- Stronger sanitising of report text belongs to #12 (prompt-injection guard).
