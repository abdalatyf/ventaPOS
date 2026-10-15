## 2026-09-01T02:40:31Z
You are the Spec Miner subagent for the Survey Phase of VentaPOS NextGen Reporting.
Your working directory is: `d:\Projects\VentaPOS\.agents\survey_spec_miner`
Your role: teamwork_preview_spec_miner
Parent conversation ID: `d11e6e43-8b57-4a1e-9692-d7682ea08eff`

## CRITICAL RULES
- READ-ONLY exploration. Do NOT edit source code or test files.
- Write your analysis to `d:\Projects\VentaPOS\.agents\survey_spec_miner\analysis.md` and `d:\Projects\VentaPOS\.agents\survey_spec_miner\handoff.md`.
- Read and follow `d:\Projects\VentaPOS\.agents\AGENTS.md` and `d:\Projects\VentaPOS\.agents\ORIGINAL_REQUEST.md`.

## Task: Full Specification & Requirements Extraction
Read:
1. `d:\Projects\VentaPOS\.agents\ORIGINAL_REQUEST.md`
2. `d:\Projects\VentaPOS\VentaPOS_NextGen\REPORTS_AGREEMENT.md`
3. `d:\Projects\VentaPOS\VentaPOS_NextGen\requirements.md`
4. `d:\Projects\VentaPOS\.agents\AGENTS.md`
5. `d:\Projects\VentaPOS\VentaPOS_NextGen\UI_UX_RULES.md`
6. `d:\Projects\VentaPOS\VentaPOS_NextGen\frontend\TABLE_UX_GUIDELINES.md`

## Required Findings to Produce in `analysis.md` & `handoff.md`:
1. Feature Inventory Table: Complete breakdown of every feature, KPI, column, filter, and utility required for all 7 report pages:
   - Dashboard (/reports/dashboard)
   - Salesperson Performance (/reports/salesperson)
   - Inventory Movement (/reports/inventory)
   - Profit & Loss (/reports/profit-and-loss)
   - Cash Drawer (/reports/cash-drawer)
   - Daily Sales / Invoices Report (/reports/daily-sales or similar)
   - Expenses Report (/reports/expenses or similar)
2. Detailed Specification for R1 (Shared Utilities & Autocomplete):
   - `ReportAutocomplete.jsx` props, styling, debounce, keyboard navigation, clear behavior, RTL styling.
   - `fmtNum` rules (thousand separators, integer-only vs decimal, NaN handling, 0 handling).
   - `toArabic` rules (Arabic-Indic digit conversion ٠-٩, MM/YYYY formatting, date parsing).
3. Detailed Specification for R2 (Backend Fixes):
   - `receipt_from` and `receipt_to` query parameter handling and filtering logic.
   - `إجمالي المقدمات` KPI logic across endpoints.
   - Array extraction expectations (keys returned by backend vs expected by frontend tables).
4. Detailed Specification for R3 (7 Report Pages):
   - Exact Columns (Arabic headers, data keys, formatting per column).
   - Exact Subfilters (inputs, autocompletes, date selectors, clear buttons).
   - Exact KPIs (cards, formulas, drill-down targets).
5. Acceptance Criteria & Verification Checklist.
