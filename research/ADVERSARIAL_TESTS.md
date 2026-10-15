# Adversarial CLI pipeline tests (#12)

```bash
python3 -m unittest discover -s research -p 'test_adversarial_e2e.py' -v
```

Requires Linux, Python 3 and the dispatcher's existing PyYAML dependency.
The suite copies the current production dispatcher, intake guard and example
job into a fresh temporary checkout for every test. It invokes their real CLIs
in subprocesses from outside that checkout; it does not mock their functions.
Each command has a 10-second timeout. Concurrent-test children are cleaned up.
Reports are synthetic browser exports; all secrets and shell-marker targets are
fake files under the temporary test directory. Child environments use a minimal
PATH/HOME and do not inherit credential environment variables. No browser,
network requests, real credentials, purchases, services or API calls are used.

## Covered pipeline and attacks

Trusted job -> real dispatcher -> simulated browser exports -> real intake CLI
-> explicit digest review -> reviewed snapshots (still untrusted).

- Both providers, exact-byte/digest binding, preserved trust labels and mode 600.
- Override/role/shell/exfiltration corpus; Unicode compatibility, hidden formatting
  and HTML comments; even an exact approval digest cannot release quarantined data.
- Novel, Czech and base64 payloads: demonstrate that known-pattern screening misses
  attacks, but the default route still requires review and releases nothing.
- Report replacement, stale approval, duplicate release and concurrent approvals.
- Path traversal, report/inbox/output symlinks, hardlinks, FIFOs/directories,
  malformed UTF-8, empty/control-character exports, size limits and missing reports.
- Unexpected AGENTS.md in the inbox is not consumed; dispatcher output escapes
  and symlinked prompt targets cannot overwrite the fake secret.

Canary checks show that these CLI invocations did not leak/modify the particular
fake file or execute the marker payload. They do NOT prove the test user lacked
permission to read it, nor that a model/agent could not act on an instruction.
Automated digest approval is a test fixture, not human-approval authentication.
The suite intentionally documents the lack of a complete security boundary.

## Still required before closing #12

The tool-less synthesis worker and OS/tool permission boundary are not implemented
on this branch. No test here claims to validate them. A full-system acceptance run
must use the actual configured browser, agent and synthesis runtime and record:

1. Raw, novel/encoded/multilingual report instructions cannot trigger tools,
   shell actions or secret reads, even if the model attempts those actions.
2. The real synthesis identity cannot read a fake secret outside its mounts,
   write approved snapshots or invoke the approval command; attempts fail at the
   permission layer, with a benign positive control proving the worker ran.
3. Captured tool/audit events demonstrate denied attempts and no successful
   writes/reads, rather than relying solely on unchanged canaries or model text.
4. Provider exports and reviewed-snapshot handoff use the same canonical paths;
   malicious synthesis output remains untrusted to the executor.

Those full-system tests are BLOCKED, not passed or silently skipped. Supply only
fake secrets in an approved disposable environment; never use production secrets.
This patch changes tests and test documentation only. Production code, workflows,
credentials, issue status and plugin test.sh are unchanged.
