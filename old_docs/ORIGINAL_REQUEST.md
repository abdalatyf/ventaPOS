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

## Follow-up — 2026-07-01T02:14:10Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

An automated team of AI agents will analyze the legacy VentaPOS desktop codebase and the new VentaPOS_NextGen codebase to produce a comprehensive feature parity report. The report will identify missing pages, missing features, unhandled edge cases, and actionable steps to implement them in the new architecture.

Working directory: D:\Projects\VentaPOS\VentaPOS_NextGen

## Requirements

### R1. Deep Codebase Comparison
Use Static Code Analysis to thoroughly compare the old desktop system (`D:\Projects\VentaPOS\Desktop\sales`) against the new React/Django system (`D:\Projects\VentaPOS\VentaPOS_NextGen`).

### R2. Exhaustive Gap Analysis Report
Generate a highly detailed, exhaustive Markdown report documenting *every single missing page, feature, logic discrepancy, or UI difference*. **DO NOT Summarize.** You must list the full details about every single page and component that is missing from the new system. 

### R3. Actionable AI Tasks and Prompts
Provide a Master Markdown Checklist artifact containing copy-pasteable AI prompts for each missing page/feature so they can be assigned to other AI agents seamlessly.

## Acceptance Criteria

### Verification
- [ ] The report accurately identifies missing features by statically analyzing and referencing specific files in both codebases.
- [ ] The report does not skip or summarize details—it must be extensive and granular.
- [ ] The report provides actionable, copy-pasteable implementation prompts mapped to the new Django/React architecture.

## Follow-up — 2026-07-01T16:26:58+03:00

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

Rebuild the VentaPOS NextGen POS Entry (Add Receipt) screen and its supporting backend APIs to achieve 100% feature parity with the legacy Django Desktop version, specifically restoring the dynamic Smart Autocomplete engine, Installment schedule shifting, and payload integrity.

Working directory: `D:\Projects\VentaPOS\VentaPOS_NextGen`
Integrity mode: development

## Requirements

### R1. Backend Autocomplete APIs
Implement two endpoints in the Django backend (`api/views.py`):
1. `GET /api/v1/product-suggestions/`: Accepts `term`, `month`, and `year`. Must return `{id, value, max}` where `max` is the safe available quantity calculated for that future date.
2. `GET /api/v1/customer-suggestions/`: Accepts `term`, `field` (name/phone/address/area), `salesperson_id`, `current_area`, and `current_name`. Must return relevance-sorted suggestions matching the legacy logic.

### R2. Frontend Smart Autocomplete
Modify `PosEntry.jsx` to remove the upfront fetching of all inventory items. Replace the standard inputs for Product Search, Customer Name, Phone, Address, and Area with debounced Async Autocomplete dropdowns that query the new APIs from R1. The Customer autocomplete must pass context (e.g., passing `salesperson_id` when searching for a name).

### R3. POS Business Logic Parity
1. **Cash Sale Toggle**: Replicate the "Cash Sale?" checkbox logic. When checked, the UI must hide the Customer and Installment sections, remove their validation requirements, and set `is_cash_sale=true` in the payload.
2. **Installment Shift**: The generated installment schedule must start on `sale_month + 1` (handling year rollover).
3. **Stock Validation**: The product autocomplete must cache the returned `max` value. When clicking "Add to Cart", the UI must strictly block the addition if `requested_qty + cart_qty > max`.
4. **Payload Mapping**: The final POST payload to `/api/v1/receipts/` must use the keys `phone_number`, `address`, and `area` instead of `customer_phone`, etc., to prevent data loss. The Address field must remain a standard `<input type="text">`, not a textarea.

## Acceptance Criteria

### API Integrity
- [ ] `GET /api/v1/product-suggestions/?term=X&month=7&year=2026` returns a valid JSON array of objects with `id`, `value`, and `max`.
- [ ] `GET /api/v1/customer-suggestions/?field=phone&term=010` returns a valid JSON array of `value` strings.

### Frontend Logic
- [ ] Typing in the product search box triggers a network request rather than filtering a static array.
- [ ] Selecting a sale month of "12" and adding a 1-month installment generates a schedule for month "1" of the next year.
- [ ] The submitted POST payload contains `phone_number` and `address` fields, and the backend successfully saves them to the database.

## Follow-up — 2026-07-04T01:20:13Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

Thoroughly test the newly implemented Add Receipt (POS Entry) screen to verify both Cash Sale and Installment flows, payload integrity, and backend database recording.

Working directory: D:\Projects\VentaPOS\VentaPOS_NextGen

## Requirements

### R1. UI Functional Testing
Test the frontend component at `http://localhost:5173/pos`. Verify that the "Cash Sale" toggle correctly hides/shows customer and installment sections, and that the Product and Customer autocomplete fields fetch data correctly from the backend.

### R2. End-to-End Submission Testing
Successfully submit at least one Cash Sale invoice and one Installment Sale invoice. Verify that the frontend correctly calculates subtotals, installment shifts, and down payments.

### R3. Backend Data Integrity Verification
After submission, query the backend database (SQLite/Django) to verify that the `Receipt`, `SaleItem`, and `InstallmentPayment` records were saved exactly as submitted, with correct hashes and tenant isolation.

## Acceptance Criteria

### Testing Deliverables
- [ ] A documented test run of the Cash Sale flow, confirming successful 201 response.
- [ ] A documented test run of the Installment flow, confirming the installment dates start on the correct month.
- [ ] Database queries confirming the records exist and mathematical totals match the expected values.

