# Evaluation

## Verdict: PASS | FAIL

## Acceptance checklist

## Blocking findings

## Non-blocking findings

## Evidence (file:line, commands or artifacts)

## Unverified claims

## Setup script checklist

- Every install, write or enable sits behind `confirm`.
- No `curl | bash` and no unconfirmed `sudo`.
- `bash -n` passes on the new script.
- A new panel action updates `Panel.qml`, both `i18n/*.json`, `README.md` and the `expected_actions` in `test.sh` in the same change.
- External URLs, paths and plugin IDs are listed in `Upstream` of the handoff and marked verified or unverified.

## Remediation criteria

## Next owner: EXECUTOR | ORCHESTRATOR | USER
