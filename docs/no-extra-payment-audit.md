# No-extra-payment audit

Run before first use and after every tool update. All items must be unchecked-to-checked "nothing is enabled".

## Authentication
- [ ] Every agent uses browser OAuth login only.
- [ ] No API keys in shell profiles, `.env` files, or agent config (`grep -ri "api_key\|_API_KEY" ~ --include="*.env" --include=".*rc"`).
- [ ] No Anthropic auth in the Omarchy Steward OMP profile.

## Per-provider billing
- [ ] Claude: no usage credits or extra usage enabled.
- [ ] Cursor: on-demand usage disabled.
- [ ] Antigravity / Google: no billing project or overage attached.
- [ ] OpenAI / Codex: no API billing, free tier only.
- [ ] Grok / X: no paid upgrade.
- [ ] Perplexity: no API usage billing.

## Safeguards
- [ ] No auto top-up on any account.
- [ ] Agents stop on upgrade, payment, login or CAPTCHA prompts.
- [ ] `git push`, PR creation and merge need explicit confirmation.

Plan names and limits change often: verify each setting in the provider's own account page.
