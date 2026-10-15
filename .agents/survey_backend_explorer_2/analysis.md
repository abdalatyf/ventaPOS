# Backend Investigation & Bug Analysis — VentaPOS NextGen Reporting

**Date**: 2026-09-01  
**Agent**: survey_backend_explorer_2 (teamwork_preview_explorer)  
**Parent**: d11e6e43-8b57-4a1e-9692-d7682ea08eff  
**Working Directory**: `d:\Projects\VentaPOS\.agents\survey_backend_explorer_2`

---

## 1. Executive Summary

This report provides an exhaustive, read-only audit of the VentaPOS NextGen backend reporting architecture, API endpoints, serialization layers, data models, and test suite. We investigated:
1. All 7 report views and ViewSets in `backend/api/views.py` vs frontend requirements in `REPORTS_AGREEMENT.md` and legacy desktop reference (`Desktop/sales/salesapp/views/`).
2. **Bug 1**: `receipt_from` and `receipt_to` filter mechanics in `ReceiptViewSet`.
3. **Bug 2**: Down payment (`إجمالي المقدمات`) KPI aggregation inconsistencies across Dashboard, Salesperson Performance, Cash Drawer, and Receipts reports.
4. **Bug 3**: Array extraction mismatches (`items` vs `salespersons` vs `results`) causing empty tables in Inventory Movement and Salesperson Performance reports.
5. The backend test suite failure breakdown and required fixes.

---

## 2. Current Backend Report Endpoints & Response Schema

| Endpoint | Method | View Class | Query Parameters | Response Structure & Top-Level Keys |
|---|---|---|---|---|
| `/api/v1/reports/dashboard/`<br>`/api/v1/reports/dashboard/summary/` | `GET` | `DashboardReportView` | `branch_id` *(req, int)*<br>`year` *(int)*<br>`month` *(int)* | `{ period: {year, month}, kpis: {safe_balance, total_revenue, total_cogs, total_sales_commissions, total_collection_commissions, estimated_net_profit, current_inventory_value, low_stock_count, avg_basket_size}, cash_drawer_summary: {cash_sales_inflow, down_payment_inflow, collection_inflow, total_cash_inflow, total_purchases, operating_expenses, auto_salaries, net_cash_in_hand}, top_products: [...], top_areas: [...] }` |
| `/api/v1/reports/salespersons/`<br>`/api/v1/reports/salesperson-performance/` | `GET` | `SalespersonPerformanceReportView` | `branch_id` *(req, int)*<br>`year` *(int)*<br>`month` *(int)* | `{ totals: {grand_total_cash, grand_total_credit, grand_total_sales, grand_total_collected, grand_total_comm_sales, grand_total_comm_coll, grand_total_due}, salespersons: [{salesperson_id, id, name, receipts_count, cash_sales, credit_sales, total_sales_val, collected, comm_sales, comm_coll, due_salary}, ...] }` |
| `/api/v1/reports/inventory-movement/` | `GET` | `InventoryMovementReportView` | `branch_id` *(req, int)*<br>`year` *(int)*<br>`month` *(int)*<br>`salesperson_id` *(opt)* | `{ total_inventory_value: float, total_adjustments_count: int, items: [{product_id, id, product_name, opening_stock, purchases, returns, sales, surplus, deficit, final_stock, unit_cost, total_value}, ...] }` |
| `/api/v1/reports/sales-pl/`<br>`/api/v1/reports/profit-and-loss/` | `GET` | `ProfitAndLossReportView` | `branch_id` *(req, int)*<br>`year` *(int)*<br>`month` *(int)*<br>`salesperson_id` *(opt, int)* | `{ summary: {grand_revenue, grand_cost, grand_commission, expenses_total, net_profit_final}, cash_sales_profitability: [{id, name, qty, avg_sell, cost_per_unit, sales_comm_per_unit, total_rev, total_cost, total_sales_comm, coll_comm_per_unit, total_coll_comm, total_profit, avg_profit}, ...], installment_sales_profitability: [...] }` |
| `/api/v1/reports/cash-drawer/`<br>`/api/v1/reports/cash-drawer-details/` | `GET` | `CashDrawerReportView` | `branch_id` *(req, int)*<br>`year` *(int)*<br>`month` *(int)* | `{ cash_sales: [{receipt_id, receipt_number, customer_name, amount, sale_date}, ...], down_payments: [{receipt_id, receipt_number, customer_name, down_payment, total_amount, sale_date}, ...], collections: [{payment_id, receipt_number, customer_name, amount, payment_date}, ...] }` |
| `/api/v1/reports/installments/` | `GET` | `InstallmentsReportView` | `branch_id` *(req, int)*<br>`year` *(int)*<br>`month` *(int)*<br>`salesperson_id` *(int)*<br>`sale_from_year`, `sale_from_month`, `sale_to_year`, `sale_to_month`, `customer_name`, `phone`, `area` | `{ total_installments_amount: float, installments_count: int, installments: [{payment_id, receipt_id, receipt_num, customer_name, phone, area, salesperson_name, amount, date, sale_date, inst_system}, ...] }` |
| `/api/v1/receipts/` | `GET` | `ReceiptViewSet` | `branch_id`, `salesperson_id`/`salesperson`, `year`, `month`, `receipt_from`, `receipt_to`, `customer_name`, `phone`/`phone_number`, `address`, `area`, `is_cash_sale`, `has_down_payment`, `page`, `page_size` | `{ count: int, next: str, previous: str, aggregate: {total_sales: float}, all_ids: [...], results: [...], total_amount_sum: float }` |
| `/api/v1/expenses/` | `GET` | `ExpenseViewSet` | `branch_id`, `year`, `month` | `[{ id, branch, amount, description, expense_year, expense_month, created_at }, ...]` |

---

## 3. Deep Root Cause Analysis

### 3.1 Bug 1: `receipt_from` and `receipt_to` Range Filtering
**Location**: `backend/api/views.py`, lines 1119-1130 (`ReceiptViewSet.get_queryset`)

**Observations**:
```python
# lines 1119-1130:
if receipt_from := params.get("receipt_from"):
    if str(receipt_from).strip():
        clean_rf = to_english_numerals(str(receipt_from).strip())
        qs = qs.filter(receipt_number__gte=clean_rf)

if receipt_to := params.get("receipt_to"):
    if str(receipt_to).strip():
        clean_rt = to_english_numerals(str(receipt_to).strip())
        qs = qs.filter(receipt_number__lte=clean_rt)
```
**Defects Found**:
1. `clean_rf` and `clean_rt` are kept as `str` instead of casting to `int`. While SQLite is type-lenient, comparing strings lexicographically vs integers numerically (`"100" < "20"`) causes incorrect range evaluation when string queries are executed.
2. If non-numeric characters are present, `int(clean_rf)` should be guarded by `try...except ValueError`.
3. In `ReceiptsReport.jsx` (lines 108-109), `receipt_from` and `receipt_to` parameters are appended as query strings, but in `ReceiptPagination` and `ReceiptViewSet`, the totals were not computing subtotal metrics under range filters.

### 3.2 Bug 2: `إجمالي المقدمات` (Down Payments) KPI Logic & Formula Discrepancies
**Locations**:
- `backend/api/views.py`: lines 757-768 (`ReceiptPagination`), lines 1940-2017 (`SalespersonPerformanceReportView`), lines 1752, 1790, 1983, 2284 (Integer division).

**Defects Found**:
1. **Omission in `SalespersonPerformanceReportView`**:
   - `REPORTS_AGREEMENT.md` (§7) explicitly requires:
     - Grouped Column: **المقدمات (Down Payments)** per salesperson.
     - Summary KPI: **إجمالي المقدمات (Total Down Payments)** across all salespersons.
   - `SalespersonPerformanceReportView` calculates `cash_sales` and `credit_sales`, but completely omits `down_payments` per rep and `grand_total_down_payments` in `totals`.
2. **Missing Paginated Aggregates in `ReceiptPagination`**:
   - In `ReceiptPagination.get_paginated_response`, only `total_sales` is calculated over `object_list`:
     `total_sales = self.page.paginator.object_list.aggregate(total=Sum("total_amount"))["total"] or 0`
   - It fails to aggregate `total_cash`, `total_down_payments`, and `total_credit`.
   - Consequently, `ReceiptsReport.jsx` (lines 126-128) fell back to calculating `sumDown` from the 200 items in the active page (`results.reduce(...)`), yielding incorrect numbers on multi-page datasets.
3. **Double Integer Floor Division (`// 10`) Truncation**:
   - In `DashboardReportView` (line 1752): `reserve_deduction = (credit_rev_sum - credit_down_payment_sum) // 10`
   - In `DashboardReportView` (line 1790): `sp_comm_coll = sp_collected // 10`
   - In `SalespersonPerformanceReportView` (line 1983): `comm_coll = collected // 10`
   - In `ProfitAndLossReportView` (line 2284): `item_coll_comm = (item_rev * payment_diff // 10) // receipt.total_amount`
   - Legacy SSoT formula (`Desktop/sales/salesapp/views/report_views.py:51-54`):
     `((F('quantity') * F('unit_price')) * (F('receipt__total_amount') - F('receipt__down_payment')) * 0.10) / F('receipt__total_amount')`
   - Using Python `// 10` truncates cents and intermediate fractions, causing discrepancies with historical ledger math.

### 3.3 Bug 3: Array Extraction Mismatches (Inventory Movement & Salesperson Performance)
**Locations**:
- `frontend/src/pages/reports/InventoryMovementReport.jsx:19, 63` vs `backend/api/views.py:2143-2147`
- `frontend/src/pages/reports/SalespersonPerformanceReport.jsx:20, 45` vs `backend/api/views.py:2006-2017`

**Defects Found**:
1. **Inventory Movement Report**:
   - Backend returns: `{ "total_inventory_value": ..., "total_adjustments_count": ..., "items": items_list }`.
   - Frontend extracted: `const items = Array.isArray(data.results) ? data.results : [];`.
   - Because `data.results` is `undefined`, `items` evaluated to `[]` and rendered an empty table.
2. **Salesperson Performance Report**:
   - Backend returns: `{ "totals": { ... }, "salespersons": list_data }`.
   - Frontend extracted: `const items = Array.isArray(data.results) ? data.results : [];`.
   - Because `data.results` is `undefined`, `items` evaluated to `[]` and rendered an empty table.

---

## 4. Backend Test Suite Status

Command executed:
`D:\Projects\VentaPOS\VentaPOS_NextGen\venv\Scripts\python.exe manage.py test api.tests -v 2` in `d:\Projects\VentaPOS\VentaPOS_NextGen\backend`

### Test Run Output
- Total tests discovered: 10
- Passing: 1
- Failing / Errors: 9

### Breakdown of Test Errors
1. **`api.tests.test_reporting_endpoints`**:
   - `SyntaxError: unmatched ')'` at line 93 (also lines 116, 138).
   - Line 72: `PurchaseInvoiceItem.objects.create(purchase_invoice=...)` instead of `invoice=...`.
2. **`api.tests.test_search_receipts`**:
   - `SyntaxError: unmatched ')'` at line 59 (also lines 76, 93).
3. **`api.tests.test_suggestions_and_parity`**:
   - `SyntaxError: unmatched ')'` at line 47 (also lines 54, 78).
4. **`api.tests.test_price_history`**:
   - 5 tests failed with `TypeError: PurchaseInvoiceItem() got unexpected keyword arguments: 'purchase_invoice'`. Model field is `invoice`.
5. **`api.tests.test_parity`**:
   - References obsolete multi-tenant attributes (`tenant=...`).

---

## 5. Actionable Implementation Recommendations

### Backend Changes (`backend/api/views.py`):
1. **`ReceiptViewSet.get_queryset`**:
   - Parse `receipt_from` and `receipt_to` with `try: int(clean_val)` before applying `receipt_number__gte` and `receipt_number__lte`.
2. **`ReceiptPagination.get_paginated_response`**:
   - Compute full summary dictionary over `self.page.paginator.object_list`:
     `total_sales`, `total_cash`, `total_down_payments`, `total_credit`.
3. **`SalespersonPerformanceReportView`**:
   - Add `down_payments` calculation per rep.
   - Add `grand_total_down_payments` to `totals`.
   - Return both `"salespersons": list_data` and `"results": list_data`.
4. **`InventoryMovementReportView`**:
   - Add `salesperson_id` filtering if passed.
   - Return both `"items": items_list` and `"results": items_list`.
5. **`ProfitAndLossReportView` & `DashboardReportView`**:
   - Fix collection commission and reserve deduction formulas from `// 10` to `* 0.10` / Float arithmetic to match legacy `report_views.py`.
6. **`ExpenseViewSet.get_queryset`**:
   - Add `description__icontains`, `amount__gte`, and `amount__lte` filtering.

### Test Fixes (`backend/api/tests/`):
1. Fix trailing syntax parentheses in `test_reporting_endpoints.py`, `test_search_receipts.py`, `test_suggestions_and_parity.py`.
2. Fix `PurchaseInvoiceItem` kwarg from `purchase_invoice` to `invoice` across `test_price_history.py` and `test_reporting_endpoints.py`.
3. Add unit test assertions for `grand_total_down_payments`, `total_down_payments`, and `receipt_from` / `receipt_to` integer comparisons.
