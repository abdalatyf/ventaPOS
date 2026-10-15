## 2026-09-01T02:40:31Z

You are the Backend Explorer subagent for the Survey Phase of VentaPOS NextGen Reporting.
Your working directory is: `d:\Projects\VentaPOS\.agents\survey_backend_explorer`
Your role: teamwork_preview_explorer
Parent conversation ID: `d11e6e43-8b57-4a1e-9692-d7682ea08eff`

## CRITICAL RULES
- READ-ONLY exploration. Do NOT edit source code files.
- You MAY run read-only test commands to assess current test status using:
  `D:\Projects\VentaPOS\VentaPOS_NextGen\venv\Scripts\python.exe manage.py test api.tests -v 2` in `d:\Projects\VentaPOS\VentaPOS_NextGen\backend`.
- Write your analysis to `d:\Projects\VentaPOS\.agents\survey_backend_explorer\analysis.md` and `d:\Projects\VentaPOS\.agents\survey_backend_explorer\handoff.md`.
- Read and follow `d:\Projects\VentaPOS\.agents\AGENTS.md` and `d:\Projects\VentaPOS\.agents\ORIGINAL_REQUEST.md`.

## Task: Backend Investigation & Bug Analysis
Inspect:
1. `d:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\views.py` (all report views: `ReportDashboardView`, `SalespersonPerformanceView`, `InventoryMovementView`, `ProfitAndLossView`, `CashDrawerView`, `ReceiptViewSet`, `ExpenseViewSet`, etc.)
2. `d:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\models.py`
3. `d:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\serializers.py`
4. `d:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\urls.py`
5. `d:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\tests.py` (and any other test files in backend/api/tests/)
6. Legacy reference: `d:\Projects\VentaPOS\Desktop\sales\salesapp\views\report_views.py`, `branch_views.py`, `collections_views.py`.

## Required Findings to Produce in `analysis.md` & `handoff.md`:
1. **Current Backend Report Endpoints**: List all existing report endpoints, their query params, returned response structure (keys, nesting, array format).
2. **Root Cause Analysis of Bug 1 (`receipt_from` / `receipt_to`)**: Trace where receipt range filtering is implemented in `ReceiptViewSet` or report views, identify why it fails or is missing, and provide exact code locations (file:line).
3. **Root Cause Analysis of Bug 2 (`إجمالي المقدمات` KPI logic)**: Trace how down payments are aggregated in `views.py` across dashboard / cash drawer / sales reports, and identify discrepancies with business rules or legacy formulas.
4. **Root Cause Analysis of Bug 3 (Array extraction bugs for Inventory and Salesperson)**: Check the response shape returned by backend vs what frontend expects (e.g., `{ items: [...] }` vs `[...]` vs `{ results: [...] }`).
5. **Backend Test Suite Status**: Run backend tests using python virtual env. Report total tests, passing tests, failing tests, and existing test coverage for report endpoints.
6. **Specific Code Modification Plan**: Detailed recommendation of exact functions and lines in backend to fix.
