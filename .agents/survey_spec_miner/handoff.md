# Handoff Report: VentaPOS NextGen Reporting Subsystem Survey & Spec Mining

**Subagent Archetype:** `teamwork_preview_spec_miner`  
**Parent Conversation ID:** `d11e6e43-8b57-4a1e-9692-d7682ea08eff`  
**Report Type:** Hard Handoff (Complete Specification Survey)  
**Date:** 2026-09-01  

---

## 1. Observation

### 1.1 Single Source of Truth (SSoT) Documents Examined
1. `d:\Projects\VentaPOS\.agents\ORIGINAL_REQUEST.md`: Lines 404–438 define the current goal:
   - R1: Shared Utilities & Autocomplete (`ReportAutocomplete`, `fmtNum`, `toArabic`).
   - R2: Backend Fixes (`receipt_from`/`receipt_to`, `إجمالي المقدمات` KPI logic, array extraction bugs for Inventory and Salesperson reports).
   - R3: Refactor 7 Report Pages per `REPORTS_AGREEMENT.md`.
2. `d:\Projects\VentaPOS\VentaPOS_NextGen\REPORTS_AGREEMENT.md`: Defines exact Columns, Subfilters, and KPIs for:
   - `InstallmentsReport`: Columns (Receipt Number, Area, Customer Name, Phone, Amount, Salesperson, Sale Date), Subfilters (Sale From MM/YYYY, Sale To MM/YYYY, Salesperson, Area, Customer, Phone), KPIs (Total Installments Count, Total Amount to Collect).
   - `ExpensesReport`: Columns (ID, Description, Amount, MM/YYYY), Subfilters (Description search, Amount from/to), KPIs (Count of Expenses, Total Expenses).
   - `ProfitAndLossReport`: Columns (Product Name, Quantity, Total Revenue, Total Cost, Total Sales Comm, Total Coll Comm, Total Profit), Subfilters (Product, Salesperson, Sale Type), KPIs (Revenue, Cost, Sales Comm, Coll Comm, Expenses, Net Profit).
   - `AveragesReport`: Columns (Product Name, Quantity, Avg Sale Price, Avg Cost, Avg Sales Comm, Avg Coll Comm, Avg Profit), Subfilters (Product, Salesperson, Sale Type), KPIs (None).
   - `InventoryMovementReport`: Columns (Product Name, Opening Stock, Purchases, Sales Returns, Sales, Purchase Returns, Deficit, Final Stock, Unit Cost, Total Value), Subfilters (Product, Salesperson), KPIs (Opening, Purchases, Sales Returns, Sales, Purchase Returns, Deficit, Final Stock, Total Value).
   - `SalespersonPerformanceReport`: Grouped Columns (Salesperson, Receipts Count, Sales Performance [Cash, Credit, Total Sales], Collections, Salary Details [Sales Comm, Coll Comm, Due Salary]), Subfilters (Salesperson Autocomplete), KPIs (7 summary cards).
3. `d:\Projects\VentaPOS\VentaPOS_NextGen\requirements.md`: Section 4 & 5 define the monthly business date system (`MM/YYYY`), soft-delete rule, Arabic-Indic numbers, commission rules (fixed value sales comm + company-wide 10% collection comm), and time-machine inventory pricing.
4. `d:\Projects\VentaPOS\.agents\AGENTS.md` & `UI_UX_RULES.md`: Red lines: no `<select>` for dynamic entities (Salespersons, Items), use Cairo font, Tabler/Bootstrap 5, fluid layout, no `<tfoot>` for totals, and table UX rules.
5. `d:\Projects\VentaPOS\VentaPOS_NextGen\frontend\TABLE_UX_GUIDELINES.md`: Native window scroll and hybrid scroll architecture with `.sticky-toolbar`, `.table-sticky-header`, and `scrollbarGutter: 'stable'`.

### 1.2 Existing Codebase Discrepancies & Direct Observations
1. **Array Extraction Discrepancies**:
   - `SalespersonPerformanceReport.jsx:45`: `const items = Array.isArray(data.results) ? data.results : [];` — fails because `SalespersonPerformanceReportView` in `views.py:2016` returns `{"totals": {...}, "salespersons": list_data}` (key is `salespersons`, not `results`).
   - `InventoryMovementReport.jsx:63`: `const items = Array.isArray(data.results) ? data.results : [];` — fails because `InventoryMovementReportView` in `views.py:2146` returns `{"total_inventory_value": ..., "total_adjustments_count": ..., "items": items_list}` (key is `items`, not `results`).
2. **Backend `receipt_from` & `receipt_to` Filtering Bug**:
   - `views.py:1120-1129`:
     ```python
     if receipt_from := params.get("receipt_from"):
         clean_rf = to_english_numerals(str(receipt_from).strip())
         qs = qs.filter(receipt_number__gte=clean_rf)
     if receipt_to := params.get("receipt_to"):
         clean_rt = to_english_numerals(str(receipt_to).strip())
         qs = qs.filter(receipt_number__lte=clean_rt)
     ```
     `clean_rf` and `clean_rt` are strings. `receipt_number` is an `IntegerField`. String comparison against integers in SQLite results in lexicographical order (where `"10" < "2"`).
3. **Backend `ReceiptViewSet.list` Missing Pagination Aggregates**:
   - `views.py:1165-1177` calculates `total_amount_sum`, but does not calculate or return `total_cash` or `total_down_payments` in an `aggregate` object. `ReceiptsReport.jsx:126-128` tries to read `res.data.aggregate?.total_down_payments`, which is currently `undefined`.
4. **Autocomplete Component Disconnect**:
   - `components/Autocomplete.jsx` expects `fetchSuggestions` function only, while `InstallmentsReport.jsx:157` and `ReceiptsReport.jsx:244` pass `items={salespersonsList}` with `displayKey="name"`. This causes `handleInputChange` to fail when searching static lists.
5. **Local Duplicate Formatting Functions**:
   - Every report page (`SalespersonPerformanceReport.jsx`, `InventoryMovementReport.jsx`, `ProfitAndLossReport.jsx`, `AveragesReport.jsx`, `InstallmentsReport.jsx`, `ReceiptsReport.jsx`, `ExpensesReport.jsx`) duplicates its own `fmtNum` and `toArabic` inline implementations instead of importing a single, robust utility from `utils/formatUtils.js`.

---

## 2. Logic Chain

1. **Premise 1**: `REPORTS_AGREEMENT.md` and `requirements.md` define the exact business contracts for the 7 report views.
2. **Premise 2**: When frontend components attempt to read `data.results` from API endpoints returning custom keys (`salespersons` and `items`), the rendered table receives an empty array `[]`, causing the UI to show an empty state despite the backend returning valid data.
3. **Premise 3**: In SQLite, evaluating `receipt_number >= "10"` compares column values against string collation rules rather than integer arithmetic. Casting the sanitized string to `int(clean_rf)` guarantees correct integer range filtering in `ReceiptViewSet`.
4. **Premise 4**: For paginated endpoints like `/api/v1/receipts/`, calculating aggregate sums in the SQL query before slicing allows the frontend summary cards to display accurate dataset totals (`total_sales`, `total_cash`, `total_down_payments`) rather than just the first page sum.
5. **Premise 5**: Centralizing `fmtNum`, `toArabic`, and building a standalone `ReportAutocomplete.jsx` eliminates duplicate inline code, fixes client-side dropdown searching, and guarantees compliance with the strict UI/UX rules (Cairo font, Arabic-Indic numerals, integer rounding, no native `<select>` for dynamic data).

---

## 3. Caveats

- **Legacy Desktop Reference**: The legacy application in `Desktop/sales/salesapp/views/` served as the mathematical authority for time-machine valuation, proportional collection commission distribution (`(item_rev * (total_amount - down_payment) * 0.10) / total_amount`), and salesperson salary composition.
- **Printing**: Installment schedule batch and single voucher printing are preserved as defined in `InstallmentsReport.jsx` and legacy `collections_views.py`.
- **Database Schema**: No schema changes or new models are required; all 17 models in `backend/api/models.py` already support these queries.

---

## 4. Conclusion

The specification mining and survey phase is complete. The requirements, edge cases, contracts, and bugs are fully discovered and documented:
1. **R1**: Implement `ReportAutocomplete.jsx` and standardize `fmtNum` and `toArabic` in `formatUtils.js`.
2. **R2**: Fix integer casting for `receipt_from`/`receipt_to`, add `aggregate` totals to `ReceiptViewSet.list`, and align response keys (`salespersons`, `items`).
3. **R3**: Refactor all 7 report pages (`DashboardReport`, `SalespersonPerformanceReport`, `InventoryMovementReport`, `ProfitAndLossReport`, `AveragesReport`, `InstallmentsReport`, `ExpensesReport`) to consume standardized utilities and match exact columns, subfilters, and KPI cards.

Detailed reference tables and specifications have been written to `d:\Projects\VentaPOS\.agents\survey_spec_miner\analysis.md`.

---

## 5. Verification Method

### 5.1 Programmatic Backend Tests
Run the Django test suite using the project virtual environment:
```powershell
cd D:\Projects\VentaPOS\VentaPOS_NextGen\backend
D:\Projects\VentaPOS\VentaPOS_NextGen\venv\Scripts\python.exe manage.py test api.tests -v 2
```
Expected: All tests pass with exit code 0.

### 5.2 Frontend Build & Lint Verification
Run the frontend build from the frontend root:
```powershell
cd D:\Projects\VentaPOS\VentaPOS_NextGen\frontend
npm run build
```
Expected: Vite build succeeds with 0 syntax or bundling errors.

### 5.3 Invalidation Conditions
- Any report page using a standard `<select>` for salespersons or products violates `UI_UX_RULES.md` §6.1.
- Any numeric table cell displaying unformatted English decimals (e.g. `1500.00` instead of `١،٥٠٠`) violates `UI_UX_RULES.md` §6.3.
- Any report table using `<tfoot>` for totals instead of `<ReportTable summaryCards={...} />` violates `UI_UX_RULES.md` §10.
