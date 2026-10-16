# Plan

Run: `20261016T164500Z-agent-setup-reinstall`  
Repository: `/home/sparrow/omarchy-agent-setup`  
Source commit: `cf681a1e022fce4f7ac3686bdd616ab290768646`

1. Read repository instructions and source, inspect Omarchy plugin APIs and the installed copy, and preserve the existing installation/configuration.
2. Run existing tests before modifications; replace only obsolete assertions after verifying the supported panel API.
3. Run repository, research, router, shell, Python, catalog, and manifest checks; use isolated existing fixtures and mocked argv tests.
4. Synchronize the local checkout to the stable plugin ID, validate and compare deployable content, enable only if needed, and perform supported shell IPC smoke checks.
5. Repeat synchronization, restore temporary state, record the feature matrix, evidence, limitations, and rollback instructions.

Scope excludes agent execution, browser MCP setup, provider/network activity, credentials, and GitHub writes.
