# VentaPOS NextGen — Specialized Prompt Archetypes

This file contains advanced, parameterized prompt templates designed for specific tasks. 
Use these when the Standard Prompt (`PROMPT_TEMPLATE.md`) is too generic.

> **Note on Checklist-at-End Formatting:** All constraints and "Red Lines" are placed 
> at the bottom of these templates. Do NOT move them to the top. Transformer models 
> attend most strongly to the end of a prompt.

---

## 1. The Exploration Prompt (Read-Only Analysis)
Use this when you need an agent to map out a complex feature, trace a bug's origin, or summarize a domain *without* modifying any code.

```text
Role: Architecture Explorer
Task: Analyze the [DOMAIN_DESCRIPTION] starting from [ENTRY_FILE_PATH].

Instructions:
1. Trace the execution path from the entry file down to the database models.
2. Produce a "Call Graph" summarizing which files interact with which.
3. Produce a "State Contracts" list defining the shape of data passed between layers.
4. Produce an "Impact List" of what would break if we modified this domain.

[CONSTRAINTS]
- READ-ONLY MANDATE: You are strictly forbidden from writing or modifying any code.
- Ignore third-party library internals; focus only on VentaPOS code.
- If you encounter a file over 500 lines, extract only the signatures of the relevant functions.
```

---

## 2. The Planning Prompt (Architecture Checklist)
Use this after Exploration, when you need an agent to write a step-by-step implementation plan.

```text
Role: Software Architect
Task: Create an implementation plan for [FEATURE_DESCRIPTION].

Context:
[PASTE_EXPLORATION_REPORT_HERE]

Instructions:
Write a numbered checklist of exact changes required to implement the feature. For each step, specify:
1. The target file
2. The exact function/class to modify or create
3. The expected outcome of the change

[CONSTRAINTS]
- NO CODE: Do not write the actual code implementation. Output a markdown checklist only.
- SSoT ENFORCEMENT: Verify your plan against requirements.md and UI_UX_RULES.md.
- RED LINE CHECK: Does this plan violate any of the 10 Red Lines in AGENTS.md §2? If yes, halt and explain.
- BACKWARD COMPATIBILITY: Do not break existing API contracts unless explicitly requested.
```

---

## 3. The Surgical Refactor Prompt (God File Decomposition)
Use this when you need to split a massive file (like `views.py` or `POS.jsx`) into smaller modules.

```text
Role: Refactoring Specialist
Task: Extract [DOMAIN_LOGIC] from [TARGET_FILE] into a new module at [NEW_MODULE_PATH].

Instructions:
1. Read the target file and identify all dependencies of the domain logic.
2. Create the new module with high semantic cohesion.
3. Replace the original code in the target file with a Facade or clean import.
4. Verify the application still builds/runs.

[CONSTRAINTS]
- BEHAVIORAL PARITY: 1:1 behavioral transfer only. Do NOT add new features or fix bugs during this refactor.
- ISOLATION: The new module must not create circular dependencies.
- MODULAR MIRAGE PREVENTION: Ensure the new module can be understood without reading the original file.
- Do not modify existing tests.
```

---

## 4. The Feature Injection Prompt (VentaPOS UI)
Use this for adding new frontend features or pages that must match the existing UI.

```text
Role: Frontend Engineer
Task: Implement [FEATURE] in [TARGET_DIRECTORY].

Instructions:
1. Create or modify the necessary React components.
2. Wire up the API calls using the existing `api.js` patterns.
3. Verify the UI renders correctly.

[CONSTRAINTS]
- COMPONENT REUSE: You MUST use existing components (e.g., ReportTable.jsx, ReportAutocomplete.jsx). Do not hallucinate new tables or autocompletes.
- STYLING: Stick with Tabler / Bootstrap v5 utilities. No Tailwind. No inline styles.
- UX RULES: Strictly follow UI_UX_RULES.md (e.g., Arabic-Indic numerals for display, no native date pickers).
- ANCHOR PARITY: Your implementation must match the state management and error handling patterns found in POS.jsx.
```

---

## 5. The Self-Healing Debug Prompt
Use this when a test fails or a bug is found, and you need the agent to fix it autonomously.

```text
Role: Debugging Expert
Task: Fix the bug in [FUNCTION_NAME] located in [FILE_PATH].

Traceback / Error:
[PASTE_ERROR_LOG_HERE]

Instructions:
1. Analyze the causal chain leading to the error.
2. Check if the error is related to SQLite WAL mode concurrency or DRF decimal parsing (common VentaPOS issues).
3. Apply the minimal necessary diff to fix the bug.
4. Re-run tests to confirm.

[CONSTRAINTS]
- ZERO COLLATERAL DAMAGE: Do not rewrite the entire function. Touch only the lines causing the bug.
- TEST MUTATION BANNED: NEVER modify the test file to make the test pass. The tests are the source of truth.
```

---

## 6. The Diff Review Prompt (Adversarial Quality Gate)
Use this to double-check an agent's work before merging it or marking it done.

```text
Role: Hostile Code Reviewer
Task: Review the following diff and find reasons to REJECT it.

Diff:
[PASTE_DIFF_HERE]

Instructions:
Scrutinize the code against the VentaPOS architecture. Output either "APPROVED" or "REJECTED".
If REJECTED, list the exact line numbers and the rule violated.

[CONSTRAINTS]
- Check against AGENTS.md §2 (Red Lines): E.g., Did they use `.delete()`? Did they add a Customer model?
- Check against Anti-Patterns: Did they write a 6-parameter function? Did they mutate a test?
- Check against UI_UX_RULES.md: Did they use `<select>` instead of `<Autocomplete>`?
- Be pedantic. Be strict.
```
