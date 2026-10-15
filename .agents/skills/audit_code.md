---
name: audit-code
description: >
  Skill for the QA/Software Tester to audit Django and Flutter code. Executes the prompt-generate-validate loop by running PyTest or Flutter tests against the source code, self-correcting on compiler feedback.
---

# Code Auditing Skill

## Overview
This skill dictates a rigid procedural loop for the QA/Software Tester. Instead of bloating the main AGENTS.md, this skill is loaded dynamically when testing is required.

## Workflow

### 1. Requirements Assessment
- Assess the raw code against the approved `requirements.md` and `api_contract.md`.
- Hunt for unhandled errors, logical flaws, or edge cases (e.g., negative inventory, split payments).

### 2. Test Execution
- For Django: Execute the PyTest suite using MCP test commands.
- For Flutter: Execute `flutter test` via the Flutter CLI MCP.

### 3. Feedback Loop
- If an error is detected, analyze the traceback.
- Generate a fix and repeat the test.
- **CRITICAL STOP:** If consecutive test failures exceed the threshold (3 times), halt execution and request Human Intervention.
