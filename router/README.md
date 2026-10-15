# Quota-fallback router

Decides executor and evaluator from which free quotas are used up. Matches the fallback table in `AGENTS.md` (#5).

Claude is never picked as evaluator automatically (#35). When no other evaluator is left, the router answers `ask` and waits for you.

| Situation | Executor | Evaluator |
|---|---|---|
| All available | Codex | Grok |
| Codex out | Gemini | Grok |
| Grok out | Codex | Fresh Gemini session |
| Grok and Gemini out | Codex | `ask`: pause, or Claude diff-only review after `approve claude-eval` |
| Codex and Grok out | Gemini | `ask`: pause, or Claude diff-only review after `approve claude-eval` |
| Codex and Gemini out, or all out | pause until quotas reset | |
| 2 failed loops | Claude replans (planning, not evaluation) | |

## Use

```bash
python3 router/router.py route
python3 router/router.py exhausted codex --until 2026-10-15T09:00:00+02:00
python3 router/router.py available codex
python3 router/router.py failed     # after a failed evaluator verdict
python3 router/router.py passed     # also clears a pending Claude approval
python3 router/router.py approve claude-eval   # one-time OK; consumed by the next route
```

Run all repository tests with:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Exhaustion lifecycle

- `--until` accepts an ISO-8601 date and time, with or without a timezone. Values are stored in UTC.
- Expired marks are removed on the next router command. An already-expired value leaves the agent available immediately.
- Invalid or missing `--until` values fail with a concise message and no Python traceback.
- Omitting `--until` creates a manual mark. Router output then includes the exact `router.py available <agent>` command required to clear it after the quota resets.

## Claude approval

When `route` returns `"action": "ask"`, choose to pause or run `approve claude-eval`. The next `route` then returns `claude-diff-only` once and clears the approval. `status` does not consume it, `passed` clears it, and `replan` is not affected.

## Limits

- It only decides; it does not start agents, and it cannot detect quota use by itself. You or a wrapper must mark an agent exhausted.
- Free-tier limits and reset times change; check each provider's own page.
- No API keys, billing, network access, or paid overage are used.
- Automated behavior is covered by isolated subprocess tests. Real-machine Omarchy verification remains tracked separately in #36.
