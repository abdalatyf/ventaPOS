## 2026-06-20T19:47:04Z

Role: Technical Writer & Code Auditor
Task:
You are tasked with generating the comprehensive, audited `SKILL.md` file for the VentaPOS Desktop subsystem.
1. Read the codebase analysis report:
   - `d:\Projects\VentaPOS\.agents\explorer_desktop\analysis_desktop.md`
2. Integrate the official architectural resolutions from the Product Manager:
   - **License Expiry Logic Inconsistency**: The 1-month early renewal block (`expiry_date - 1 month`) in `receipt_views.py` is intentional. The views are correct. Document that the unit tests in `test_license.py` must be updated to align with this policy.
   - **System Database Location & Security (OS Temp)**: Storing the runtime license database (`~sys_lic_runtime.tmp`) unencrypted in the OS Temp directory is a known limitation. Document this as "Technical Debt" and a "Known Limitation."
   - **Background Sync Trigger in Production**: Continuous 1-minute background sync is disabled in production Waitress server. Document this as the official production behavior: "Continuous 1-minute background sync is disabled in production. Syncing is explicitly triggered via the Safe Exit routine or UI actions" (Known Limitation).
3. Write a single, unified, hyper-detailed `d:\Projects\VentaPOS\.agents\skills\Desktop\SKILL.md` containing:
   - YAML frontmatter:
     ```yaml
     ---
     name: ventapos-desktop
     description: Complete technical documentation of the VentaPOS Desktop subsystem, including database schema, configuration, views, local license validation, migration logic, automation scripts, and known limitations, fully verified against the source code.
     ---
     ```
   - Complete technical documentation covering:
     - **Project Structure & Database Configurations**: Main settings, default database (`~sys_runtime_cache_v1.tmp`), system database (`~sys_lic_runtime.tmp`), database router.
     - **Models**: All system/auth and business models with fields, types, and constraints, with exact file path and line number citations. Document the duplicate `Receipt.save()` method.
     - **Views & Routing**: Auth views, branch views, duplicate dead views in settings_views, inventory views, purchase views, receipt views (including add, edit, delete, search), print views, subscription views, sync views, utility views. Include file paths and line number citations.
     - **Local Licensing Validator**: Custom base32 decoding, unmasking, HMAC validation, licensing middleware checks, with citations.
     - **Migration Logic & Automation Scripts**: Migration steps on startup, run_app, run_browser, release engineering scripts (build_release, module_builder, etc.).
     - **Quality Audit & Architectural Resolutions**: A detailed section outlining the security and sync issues, their impacts, and resolutions. Specifically highlight the Technical Debt / Known Limitations (unencrypted temp database, disabled continuous sync in production).
4. Save the file fully at `d:\Projects\VentaPOS\.agents\skills\Desktop\SKILL.md`.
Send a message back to the orchestrator once complete with the path of the file.
Your working directory is `d:\Projects\VentaPOS\.agents\teamwork_preview_worker_desktop`.

## 2026-06-20T20:06:29Z

**Context**: Instructions update for VentaPOS Desktop Subsystem SKILL.md.
**Content**: Please integrate two new directives from the Product Manager:
1. **Grill-Me Protocol Update**: Do not pause execution or block for any ambiguous logic. Instead, document any questions/uncertainties directly in the `SKILL.md` (or a separate `unresolved_questions.md` file in the skills directory) using a prominent warning block.
2. **Exclude `run_browser.py`**: Entirely skip analyzing or documenting the file `run_browser.py`. It is excluded from the documentation scope.

**Action**: Implement these changes in the final `SKILL.md` output.
