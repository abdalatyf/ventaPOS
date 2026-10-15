# VentaPOS NextGen — Sub-Agent Delegation Protocol

This document formalizes the multi-agent pipeline used to tackle large, cross-cutting features. It defines *when* to spawn sub-agents and *how* to coordinate them using Antigravity's `invoke_subagent` tooling.

## 1. When to Delegate

- **Simple Lookup (< 3 files)**: Do it directly. Do not spawn agents.
- **Broad Research (5+ files or multiple domains)**: Spawn a `research` subagent (using `flash` model) to survey the codebase and return a summary.
- **Complex Multi-File Implementation**: Use the **4-Persona Pipeline** outlined below.

## 2. The 4-Persona Pipeline

When an objective spans multiple architectural layers (e.g., adding a new dimension that requires DB, API, and UI changes), the orchestrator must coordinate the following sub-agent personas:

| Persona | Agent Type | Goal | Inputs Provided | Outputs Expected |
|---|---|---|---|---|
| **1. Architect** | `research` (flash) | Plan the system changes | `requirements.md`, `CODEBASE_MAP.md`, `AGENTS.md` | A numbered markdown checklist (`task.md`) with NO actual code. |
| **2. Viewer** | `research` (flash) | Extract context safely | Search intent, exact file paths | Snippets of existing code needed by the Editor. |
| **3. Editor** | `self` (inherit) | Write the code | Single file target, specific step from the plan | Diffs / modified files. |
| **4. Reviewer** | `research` (flash) | Adversarial validation | The applied diff, `AGENTS.md` Red Lines | "APPROVED" or "REJECTED" with line numbers. |

## 3. VentaPOS-Specific Delegation Rules

1. **Context Isolation**: NEVER feed the Editor agent the exploratory history. The Editor must only receive the precise function/file it needs to edit, and the single instruction from the plan. This prevents context bloat and hallucination.
2. **Anchor Page Enforcement**: When dispatching an Editor to build a new UI component, ALWAYS pass it the structural patterns from `POS.jsx`. 
3. **The Reviewer's Guardrail**: The Reviewer agent must ALWAYS be provided the 10 Red Lines from `AGENTS.md §2`. Its primary job is to ensure the Editor did not hallucinate a forbidden feature (e.g., `.delete()` or a Customer model).
4. **Volume Limits**: Respect the `hooks.json` threshold. Never let an Editor modify more than 50 files without a hard human approval gate.
5. **Testing Finality**: The orchestrator must not mark the pipeline complete until a final agent runs the `VERIFY` phase (Phase 5: `manage.py test` and `npm run build`).

## 4. Example `invoke_subagent` Blueprint

```json
{
  "Subagents": [
    {
      "TypeName": "research",
      "Role": "Architect",
      "Model": "flash",
      "Prompt": "Read CODEBASE_MAP.md and requirements.md. Create a step-by-step implementation plan for [FEATURE]. Output a markdown checklist only."
    },
    {
      "TypeName": "research",
      "Role": "Reviewer",
      "Model": "flash",
      "Prompt": "Act as a hostile reviewer. Review this proposed plan against the Red Lines in AGENTS.md §2. Point out any architectural drift."
    }
  ]
}
```
