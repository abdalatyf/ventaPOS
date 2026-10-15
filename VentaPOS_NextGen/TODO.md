# VentaPOS NextGen — Master Task & Bug Tracking List

> **Approach**: Backend-First · Correctness Over Speed · Zero Hallucination  
> **Anchors**: `GEMINI.md` (Rules), `requirements.md` (Domain Specs), `UI_UX_RULES.md` (Frontend Bible)  
> **Status Notation**: `[ ]` = Pending · `[/]` = In Progress · `[x]` = Verified & Done  

---

## Priority 0: Critical Backend Bug Fixes

- [x] **Fix `InventoryItem.get_stock_at_date()` in `models.py`**:
  - Filter `receipt__receipt_type='SALE'` for `total_sold`.
  - Add `total_sales_returns` (where `receipt__receipt_type='RETURN'`) to the additive side of stock calculation.
  - Formula: $\text{Stock} = \max(0, \text{initial\_qty} + \text{purchases} + \text{surplus} + \text{sales\_returns} - \text{sales} - \text{purchase\_returns} - \text{deficit})$.
- [x] **Fix `InventoryAdjustmentSerializer` in `serializers.py`**:
  - Fix field names in `Meta.fields` and `validate()` to use `month`, `year`, and `item` (matching `models.py`), replacing outdated names `adjustment_month`, `adjustment_year`, and `inventory_item`.
- [x] **Fix `get_safe_available_qty()` Signature Mismatch**:
  - Update `InventoryItem.get_safe_available_qty()` in `models.py` to accept `return_bottleneck=False` and optionally return `(min_stock, bottleneck_month, bottleneck_year)`, resolving the `TypeError` currently triggered by `views.py` `safe_available_qty`.
- [x] **Replace Hardcoded `0.10` Collection Commission in `views.py`**:
  - Replace static `0.10` multiplier in `DashboardReportView` (L1811, L1849), `SalespersonPerformanceReportView` (L2044), `ProfitAndLossReportView` (L2360), and `ledger` with dynamic `CompanySetting.collection_commission_rate`.
- [x] **Enforce Universal Western Digits in `CustomerSuggestionsView`**:
  - Remove `to_arabic_numerals()` formatting on line 1630 of `views.py`, adhering to the project-wide ASCII `0-9` rule.
- [x] **Align Recovery Code `product_id` across Licensing Handlers**:
  - Verify and synchronize Recovery Code product ID (value `15` vs `16`) across `LicenseValidator.validate()`, `PasswordRecoveryView`, and `LicenseActivateView`.

---

## 1. Backend Core & Dimensions

- [x] Verify 17 SQLite models match requirements specification (`models.py`)
- [x] Soft delete manager (`ActiveManager`) and `is_deleted` flags
- [x] Branch-scoped sequential receipt numbering (`Receipt.get_next_receipt_number()`)
- [x] Receipt HMAC cryptographic tamper detection (`receipt_hash`)
- [x] Serializers handling nested writes, computed stock, and receipt types (`serializers.py`)
- [x] Salesperson commission tracking (`CommissionHistory`)
- [x] Branch-scoped supplier procurement (`PurchaseInvoice`, `PurchaseInvoiceItem`)
- [x] Expense recording without categories (`Expense`)

---

## 2. Desktop Packaging & Runtime

- [x] PyInstaller packaging script (`build_exe.py`) bundling built frontend and backend
- [x] Spec file hidden imports configuration (`VentaPOS.spec`)
- [x] Desktop launcher with dynamic Waitress port allocation (`launcher.py`)
- [x] Native window rendering via `pywebview`
- [x] DummyWriter stream stubbing for `--windowed` mode
- [x] Production WhiteNoise static file serving

---

## 3. Frontend Core & POS Anchor

- [x] Single admin token authentication flow (`Login.jsx`)
- [x] Branch selector with multi-branch management (`BranchSelection.jsx`)
- [x] Anchor Page: Point of Sale transaction entry (`POS.jsx`)
- [x] Keyboard-first data entry (Autofocus, Enter key navigation)
- [x] Searchable dropdown autocomplete components (`ReportAutocomplete.jsx`, `Autocomplete.jsx`)
- [x] Dual numeric date inputs (`month`, `year`) in `YYYY/MM` format
- [x] Comma-stripping payload sanitization before DRF API submission
- [x] Dimensions management tabs (Inventory, Salespersons, Suppliers)

---

## 4. Frontend: Product Ledger (In Progress)

- [ ] Review/fix `ProductLedger.jsx` — eliminate mock data fallback
- [ ] Connect live time-machine stock ledger endpoint (`/api/v1/inventory-items/{id}/ledger/`)
- [ ] Verify chronological timeline rendering (initial stock, purchases, sales, returns, adjustments)
- [ ] Verify commission history display per product

---

## 5. Procurement, Returns & Invoices

- [x] Purchase invoice entry (`PurchaseEntry.jsx`)
- [x] Historical purchase search and filtering (`SearchPurchases.jsx`)
- [x] Customer sales return processing (`ReturnReceipt.jsx`)
- [x] Linking return receipt to original sale via `parent_receipt` FK
- [x] Historical receipts search and status filtering (`SearchReceipts.jsx`)
- [ ] Verify full receipt detail modal inspection in `SearchReceipts.jsx`

---

## 6. Reports & Analytical Suite (8 Reports)

- [x] Unified report shell and period context (`ReportsLayout.jsx`, `ReportsIndex.jsx`)
- [x] Dashboard Report: P&L and Cash Drawer cards (`DashboardReport.jsx`)
- [x] Installments Report: 7 columns, 3 KPIs, phone directory (`InstallmentsReport.jsx`)
- [x] Expenses Report: 4 columns, 2 KPIs, search (`ExpensesReport.jsx`)
- [x] Profit and Loss Report: 7 columns, 6 KPIs, autocompletes (`ProfitAndLossReport.jsx`)
- [x] Averages Report: 7 per-unit columns, 0 KPIs (`AveragesReport.jsx`)
- [x] Inventory Movement Report: 10 columns, 8 KPIs (`InventoryMovementReport.jsx`)
- [x] Salesperson Performance Report: Grouped headers, 7 KPIs (`SalespersonPerformanceReport.jsx`)
- [x] Sales Invoices Report: 7 columns, 5 KPIs, infinite scroll (`ReceiptsReport.jsx`)

---

## 7. Data Safety, Tools & Settings

- [x] System settings and company information tabs (`CompanyTab.jsx`, `SecurityTab.jsx`)
- [x] Dynamic collection commission percentage configuration
- [x] Admin password management
- [ ] Complete and verify `ToolsDashboard.jsx`
- [ ] Offline USB database sync UI (`SyncTab.jsx`)
- [ ] Database backup creation and restore functionality (`BackupTab.jsx`)
- [ ] Remove deprecated `SmartImportTab.jsx` from tools

---

## 8. Licensing & Demo Mode

- [x] Demo mode random sample generation on initial launch
- [x] Demo database wipe and fresh state on restart
- [x] Cryptographic 80-bit license code validation
- [x] Machine ID hardware binding
- [x] License activation flow wiping demo data and directing to Setup (`ActivationSetup.jsx`)
- [x] Password recovery via special recovery code

---

## 9. End-to-End Verification & Integrity

- [ ] Full lifecycle test: Demo launch $\rightarrow$ License activation $\rightarrow$ Setup $\rightarrow$ Production
- [ ] Time-machine stock verification across multiple historical months
- [ ] Return receipt stock restoration test
- [ ] Installment schedule calculation and silent SumatraPDF printing test
- [ ] Full backup generation and restoration verification
- [ ] Complete automated test suite: `python manage.py test api.tests -v 2`
- [ ] Complete frontend production build: `npm run build`
