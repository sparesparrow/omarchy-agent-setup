# Reused MCP-Prompts patterns

This plugin selectively adapts the local domain model from `sparesparrow/mcp-prompts`:

- stable prompt IDs and semantic versions;
- descriptive metadata with category and tags;
- declared template variables;
- query by category or tag;
- retrieval of an exact version or the latest version;
- variable application through a small CLI.

The adaptation is intentionally a read-only local catalog backed by Git. Prompt bodies remain ordinary reviewed files, while `prompt-catalog/catalog.json` provides validated metadata. The renderer is provider-neutral and does not execute its output.

The following source-project features are deliberately excluded: AWS, DynamoDB, S3, SQS, Lambda, PostgreSQL, HTTP and MCP servers, Docker, Stripe and subscription tiers, user accounts, authentication, telemetry, CloudWatch, remote CRUD, event buses, rate limits, and automatic prompt generation. They would add credentials, network access, billing exposure, mutable infrastructure, or unnecessary dependencies.

The source repository is design inspiration rather than a package, service, or runtime dependency. Git commits and pull requests remain the only version-history and publication mechanism.
