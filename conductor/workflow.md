# Workflow Guidelines

## Continuous Documentation & GitHub MCP
> **NEW RULE ENFORCED:** Every time the AI makes a code commit (using standard git or GitHub MCP), the AI MUST synchronously update the corresponding `conductor/` and `architecture/` docs in the same workflow. Documentation is never left behind.

## Code Quality Rules
- AI agents will adhere to strict quality gates: IDOR checks, performance reviews (N+1), and E2E testing.
- No direct database schema changes without updating the central architectural models first.
- The UI MUST be verified for Arabic RTL compatibility on every feature.
