# Reused MIA agent patterns

This plugin adapts the portable control-plane pattern from `sparesparrow/mia`:

- an orchestrator owns planning, dependencies and routing;
- one executor owns implementation for a bounded task;
- an independent evaluator owns the acceptance verdict;
- work moves through explicit artifacts rather than shared assumptions;
- claims are limited to recorded evidence.

The adaptation intentionally excludes MIA-specific vehicle behavior, ElevenLabs deployment and voice configuration, smart-home tools, images, API-server setup, and mandatory role-playing personas. Those assets serve MIA's product experience and are not prerequisites for reliable Omarchy coding workflows.

The plugin adds a compact evidence contract to each executor handoff: Claim, Proof, Not proven, Safety, and Next owner. This makes simulated or unit-tested behavior visibly different from live desktop, hardware, browser-login, or external-service validation.

MIA remains the upstream inspiration, not a runtime dependency or vendored subtree. Future improvements should be ported deliberately and tested here rather than copied wholesale.
