# Original User Request

## 2026-06-20T18:14:49Z

Document the entire VentaPOS project (Server, Desktop, Mobile, LicenseManager) and generate comprehensive skill files in `.agents/skills/` to serve as a Single Source of Truth and prevent future AI hallucinations.

Working directory: d:/Projects/VentaPOS
Integrity mode: benchmark

## Requirements

### R1. Team Composition & Role Assignment
The agent team must deploy specialized subagents to cover all aspects of the project: Server Specialist, Mobile Specialist, Desktop Specialist, License/Security Specialist, and a QA/Judge Agent. The team will decide the exact structure of the documentation skills inside `.agents/skills/` based on code complexity.

### R2. Absolute Truth Protocol
All documentation must be 100% grounded in the source code. Agents must read existing architecture documents (like `database_schema.md` and `requirements.md`) before documenting code. Every technical claim, function description, or business rule documented MUST be cross-referenced with exact file paths and line numbers from the source code.

### R3. The Grill-Me Protocol (Anti-Hallucination)
If any agent encounters complex business logic (e.g., installment calculations, DRM logic, hardware integrations) where the true business intent is ambiguous, they are STRICTLY PROHIBITED from guessing. The agent must pause, invoke a human-in-the-loop consultation (ask the user explicitly), and wait for a clear answer before finalizing the documentation.

## Acceptance Criteria

### Verification & Quality
- [ ] Documentation skills have been generated in `.agents/skills/` covering all major subsystems (Server, Mobile, Desktop, LicenseManager).
- [ ] Every technical claim in the documentation contains explicit file path and line number citations.
- [ ] The QA/Judge Agent has independently audited the documentation against the codebase to certify zero hallucinations.
- [ ] The team has successfully paused and asked the user for clarification whenever ambiguous business logic was found.

## Follow-up — 2026-06-20T21:35:13Z

## RESUME — Pick up where the previous team stopped

Working directory: d:/Projects/VentaPOS
Integrity mode: benchmark

## CRITICAL CONTEXT — What was already completed

A previous agent team already completed the **full codebase analysis phase**. Their analysis reports are saved and ready to be consumed. Here is what exists:

### Completed Analysis Reports (DO NOT REDO):
1. `d:/Projects/VentaPOS/.agents/explorer_server/analysis_server.md` (15KB) — Full Server analysis (models, views, routing, sync endpoints, bugs found)
2. `d:/Projects/VentaPOS/.agents/explorer_mobile/analysis_mobile.md` (16KB) — Full Mobile analysis (screens, SQLite tables, API integrations)
3. `d:/Projects/VentaPOS/.agents/explorer_desktop/analysis_desktop.md` (22KB) — Full Desktop analysis (Django project, models, views, licensing validator)
4. `d:/Projects/VentaPOS/.agents/explorer_license/analysis_license.md` (11KB) — Full License analysis (crypto utilities, VALIDATOR.py, licensing flow)

### Existing architecture docs to cross-reference:
- `d:/Projects/VentaPOS/database_schema.md`
- `d:/Projects/VentaPOS/requirements.md`
- `d:/Projects/VentaPOS/.agents/skills/global_architecture.md`
- `d:/Projects/VentaPOS/.agents/skills/api_contract.md`

## YOUR MISSION — Phase 2: Write SKILL.md files

Using the completed analysis reports above as input, generate comprehensive `SKILL.md` documentation files inside `d:/Projects/VentaPOS/.agents/skills/`. The team should decide the best structure based on code complexity.

### Requirements:

**R1. Absolute Truth Protocol:** Every technical claim, function description, or business rule documented MUST be cross-referenced with exact file paths and line numbers from the source code. Read the analysis reports AND verify against actual source files.

**R2. The Grill-Me Protocol (Anti-Hallucination):** If any agent encounters complex business logic (e.g., installment calculations, DRM logic, hardware integrations) where the true business intent is ambiguous, they are STRICTLY PROHIBITED from guessing. The agent must pause, invoke a human-in-the-loop consultation (ask the user explicitly), and wait for a clear answer before finalizing the documentation.

**R3. Checkpoint-Safe Execution:** Each agent must write its output SKILL.md files incrementally — one file at a time, fully saved to disk before starting the next. This way, if the process is interrupted, all completed files are preserved and work can resume from where it stopped. Each agent should update its `progress.md` after completing each SKILL.md file.

## Acceptance Criteria
- [ ] SKILL.md files generated in `.agents/skills/` covering all major subsystems (Server, Mobile, Desktop, LicenseManager)
- [ ] Every technical claim contains explicit file path and line number citations
- [ ] A QA/Judge Agent has independently audited the documentation against the codebase
- [ ] The team paused and asked the user for clarification on any ambiguous business logic
- [ ] Each completed SKILL.md is fully saved to disk before starting the next one (checkpoint-safe)

## 2026-06-24T19:31:33Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Execute the multi-agent teamwork project

Complete the VentaPOS Mobile App overhaul (Flutter/SQLite) to match the Django Desktop application 100% in logic, UI (FlareLine), and features, excluding the local license invoice deduction.

Working directory: D:\Projects\VentaPOS\Mobile\sales_app_offline
Integrity mode: development

## Requirements

### R1. Complete All Remaining Screens
Migrate all remaining mobile screens (`manage_products_screen.dart`, `expenses_screen.dart`, `manage_branches_screen.dart`, `manage_users_screen.dart`, `manage_suppliers_screen.dart`, `manage_purchase_invoices_screen.dart`, `sync_hub_screen.dart`, `product_ledger_screen.dart`, `sales_reports_screen.dart`) to use the FlareLine UIKit components (`CommonCard`, `OutBorderTextFormField`, etc.).

### R2. Replicate Desktop Business Logic (All Screens)
Implement exact Desktop logic for EVERY screen (not just Receipts). This includes inventory constraints, cryptographic hashing, parsing, and advanced filtering across the entire app, excluding only the `invoices_balance` deduction. You must read the corresponding Django views in `D:\Projects\VentaPOS\Desktop\sales\salesapp\views\` to understand the exact logic for each screen.

### R3. Dedicated Agent Per Screen
The teamwork orchestrator must spawn a dedicated subagent for each individual screen. Each agent is responsible for perfectly translating both the FlareLine UI and the underlying Django business logic for their assigned screen.

### R4. Offline Sync Architecture
Ensure the SQLite `database_helper.dart` handles the `receipt_hash` correctly and stages data for the `SyncHub` to push to the Cloud/Desktop.

## Acceptance Criteria

### Automated Verification
- [ ] A Python script (`test_mobile_logic.py`) is written to query the local SQLite DB and verify that `receipt_hash` is generated identically to the Django logic.
- [ ] A Python script verifies that adding a receipt in the mobile app correctly updates stock and respects the `get_safe_available_qty` algorithm.

### Agent-as-Judge Verification
- [ ] All specified screens are fully translated to Flareline UIKit components.
- [ ] No screen uses plain Flutter TextFields or Cards where Flareline components exist.

## Follow-up — 2026-06-28T13:02:13Z

Rebuild the VentaPOS desktop application as a modern web app (React/Django) achieving 100% feature parity with the original system, including exact business logic, UI flows, and comprehensive technical documentation. Includes a safe data migration path for old clients.

Working directory: d:/Projects/VentaPOS/VentaPOS_NextGen
Integrity mode: demo

## Requirements

### R1. 100% Parity Reconstruction
Reconstruct the legacy desktop application's complete logic into the new React/Django stack. You MUST read the old code to understand expected behaviors (like the time-machine inventory logic, invoice hashing, and strict Company Setup Wizard) and replicate them exactly without inventing new constraints or dropping existing ones.

### R2. Data Migration Script
Write a robust Python script that cleanly migrates client data from the old `.sqlite3` database schema to the new Django ORM schema without data loss.

### R3. Continuous Documentation
Generate comprehensive technical documentation (Markdown/OpenAPI) for the system architecture immediately after completing each subsystem.

### R4. Zero Hallucination Policy
If you encounter any ambiguity, missing information in the old codebase, or are unsure about how a specific business rule was implemented, you MUST stop and ask the user for clarification. Do not invent, guess, or assume any logic.

## Acceptance Criteria

### Migration Integrity
- [ ] A test run of the migration script on the user-provided legacy `.sqlite3` database completes without errors.
- [ ] Record counts for core entities (Invoices, Customers, Items, Salespersons) match exactly between the old and new databases.

### Feature Parity
- [ ] A programmatic test script validates that generating an invoice in the new system with identical inputs to the old system produces the exact same cryptographic hash and stock deductions.

### Documentation completeness
- [ ] A verified OpenAPI 3.1 contract exists for all endpoints.
- [ ] Markdown architecture files exist documenting the UI flow mappings from the old desktop views.
