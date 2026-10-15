## 2026-08-31T23:53:25Z
You are the E2E Test Writer subagent for the Reporting Subsystem.
Your working directory is: `d:\Projects\VentaPOS\.agents\test_writer_e2e`
Your role: teamwork_preview_test_writer
Parent conversation ID: `d11e6e43-8b57-4a1e-9692-d7682ea08eff`

## CRITICAL INTEGRITY WARNING
DO NOT CHEAT. All test implementations must be genuine. Write authentic assertions testing the actual functionality.

## Context & Inputs to Read:
1. `d:\Projects\VentaPOS\.agents\ORIGINAL_REQUEST.md`
2. `d:\Projects\VentaPOS\PROJECT.md`
3. `d:\Projects\VentaPOS\TEST_INFRA.md`
4. `d:\Projects\VentaPOS\VentaPOS_NextGen\REPORTS_AGREEMENT.md`
5. `d:\Projects\VentaPOS\VentaPOS_NextGen\requirements.md`

## Your Task:
1. Create a comprehensive, multi-tier E2E and integration test suite in `d:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\tests\test_reports_comprehensive_e2e.py`.
2. Cover:
   - **Tier 1 (Feature Coverage)**: Dashboard summary KPIs, Salesperson performance, Inventory movement, P&L totals, P&L averages, Installments ledger, Expenses, Receipt pagination aggregate.
   - **Tier 2 (Boundary & Corner Cases)**: `receipt_from`/`receipt_to` numeric ranges and Arabic digits (`"٢"` to `"١٠"`), 0-value down payments, negative expenses rejection or handling, month/year filtering with rollover.
   - **Tier 3 (Cross-Feature Combinations)**: Sale creation -> Down payment reflection in Cash Drawer & Dashboard -> Salesperson commission & salary calculation -> Inventory stock deduction & movement tracking.
   - **Tier 4 (Real-World Application Workloads)**: Monthly business close scenario verifying financial statement integrity.
3. Verify tests pass by running:
   `D:\Projects\VentaPOS\VentaPOS_NextGen\venv\Scripts\python.exe manage.py test api.tests.test_reports_comprehensive_e2e -v 2` in `d:\Projects\VentaPOS\VentaPOS_NextGen\backend`.
4. When test suite is ready and passing, create `d:\Projects\VentaPOS\TEST_READY.md` summarizing test counts per tier, runner command, and pass status.
5. Save your report to `d:\Projects\VentaPOS\.agents\test_writer_e2e\handoff.md` and message parent.
