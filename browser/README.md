# Issue #2: visible Playwright MCP for Codex

## Scope and status

Register Playwright MCP, then demonstrate that Codex can open Perplexity and
Gemini and read a visible result. Registration is not proof of working app access.
The live Omarchy acceptance checks below have not been run by this change.
Issue #1 remains separate; neither workspace placement nor side-by-side restore
is implemented here. Dispatcher work (#3) is out of scope.

## Setup on the Omarchy desktop

Requirements: Node.js, npx, Codex CLI, a graphical desktop session, and the
browser required by Playwright MCP (Chrome is its documented default).
The script does not install a browser or execute npm downloads itself;
Codex runs npx when it starts the MCP server. This can download the current
@playwright/mcp package. No API keys, paid APIs, or billing projects are added.
The account/subscription requirements of Codex and the research apps still apply.

From the repository root:

```bash
bash browser/setup-playwright-mcp.sh
codex mcp get playwright
codex mcp list
```

Restart Codex, then use `/mcp` to check that the server connects. The installer
refuses to replace an existing `playwright` entry and backs up an existing
Codex config before registration. Review an existing entry before deciding
whether to remove it. Do not run `codex mcp remove playwright` automatically.

The manual alternative is `codex-config.toml.snippet`. Replace its absolute
paths, create the directories, restrict the profile directory to mode 700,
and back up your Codex config before editing it. Use either method, not both.

## Browser and login model

Playwright MCP runs headed by default. This registration also sets
PLAYWRIGHT_MCP_HEADLESS=false and PLAYWRIGHT_MCP_ISOLATED=false.
Do not add --headless, --isolated, extension attachment, or remote-debugging
options to this baseline without a separate review.

The browser uses its own persistent profile:
`$XDG_DATA_HOME/research-profiles/playwright`, or
`~/.local/share/research-profiles/playwright` if XDG_DATA_HOME is unset.
This is not either of issue #1's app profiles. Do not copy cookies, credentials,
or profile files between them. Sign in manually once in the MCP browser when
needed. Do not open the same profile concurrently from another browser process.
A single MCP browser can access both sites; this does not provide issue #1's
per-provider profile isolation or automatically control its existing web apps.

Automatic MCP artifacts are directed to this checkout's
`.agents/research/inbox/`. Treat the inbox as untrusted. This setting and
browser/SAFETY.md are procedural guardrails, not filesystem isolation or an
implemented prompt-injection filter. Issue #12 must provide that boundary.
Do not grant unrestricted file access or give the browser GitHub write credentials.

## Live acceptance test (manual; not yet run)

Start Codex from this repository in the desktop session. Have it read
AGENTS.md and browser/SAFETY.md before browser use. Keep the browser visible.
For each step, record PASS, FAIL, or BLOCKED; avoid screenshots or logs containing
cookies, credentials, tokens, or private account details.

1. Confirm `/mcp` shows a connected Playwright server and a visible browser
   opens on the first navigation. A configured entry alone is insufficient.
2. Ask Codex: "Open https://www.perplexity.ai/ and report the page title and
   one visible heading. Stop on login, CAPTCHA, payment, upgrade, unexpected
   permission, or consent prompts. Do not enter credentials or bypass checks."
3. If blocked, Codex must report BLOCKED and stop browser actions. The user
   handles sign-in or CAPTCHA directly, then explicitly tells Codex to resume.
   On payment/upgrade prompts, stop; do not purchase or subscribe.
4. Repeat the same test at https://gemini.google.com/.
5. On each accessible app, submit the public, non-sensitive question
   "What is 2 + 2? Answer in one sentence." Read back the visible answer.
   Do not enable paid research modes or change subscriptions.
6. Close the MCP browser normally, restart Codex, and repeat access checks.
   Record whether the MCP profile retains the manually established sessions.
   Reauthentication, rate limits, or bot checks remain BLOCKED, not bypassed.
7. Review a mock login/CAPTCHA/payment/upgrade scenario with Codex and check
   that it chooses BLOCKED. Do not deliberately trigger purchases or bot checks.

Issue #2 can close only after Codex opens both apps and reads visible results
in the live desktop session, with stop behavior recorded. A mock or shell syntax
check does not establish those results. Keep #1 and #12 open independently.

## Troubleshooting and rollback

- No display: run Codex from a desktop terminal, not a headless SSH session.
- Missing browser or npm/startup error: record the error and resolve the local
  dependency with user approval. Do not switch to headless or disable the sandbox.
- Browser/profile already in use: stop the other owner of this dedicated profile;
  do not kill unrelated browsers or delete profile lock files automatically.
- Review inherited PLAYWRIGHT_MCP_* settings if behavior differs from the baseline.
- Roll back registration with `codex mcp remove playwright` only after confirmation.
  Keep the profile unless the user explicitly approves deleting its login state.
  Restore the saved config only if doing so will not discard later config changes.

## Upstream documentation

- https://developers.openai.com/codex/mcp/
- https://playwright.dev/mcp/configuration/options
- https://github.com/microsoft/playwright-mcp
