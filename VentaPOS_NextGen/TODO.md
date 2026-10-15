# VentaPOS NextGen — Master TODO List

> **Approach:** Backend-first · Quality over speed · No deadline
> **Anchor:** POS.jsx is the only trusted page — everything else needs review
> **Format:** `[ ]` = pending · `[/]` = in progress · `[x]` = done

---

## 0. Cleanup & Preparation
- [x] Delete PosEntry.jsx
- [x] Delete POS.test.jsx (references old POS)
- [x] Delete SearchReceipts.txt (looks like a backup file)
- [x] Review and clean up api.js — remove X-Company-Code header, verify Authorization: Token header
- [x] Review App.jsx routing — default route is SearchReceipts, remove PosEntry references

## 1. Backend: Models Review
- [x] Verify all 17 models match requirements (they look clean already)
- [x] Verify Branch model — consider if collection_commission_rate should be on Branch instead of CompanySetting (currently on CompanySetting as company-wide)
- [x] Review get_stock_at_date() correctness
- [x] Review get_commission_at_date() correctness
- [x] Review get_price_at_date() correctness
- [x] Review get_safe_available_qty() correctness
- [x] Review Receipt.get_next_receipt_number() — ensure branch-scoped
- [x] Review receipt hash generation (is_authentic property)

## 2. Backend: Serializers Review
- [x] Review all serializers in serializers.py (31KB)
- [x] Verify no references to removed models (Tenant, CloudUser, ActionLog)
- [x] Verify receipt serialization handles SALE and RETURN types
- [x] Verify installment serialization
- [x] Verify purchase invoice serialization
- [x] Verify inventory item serialization includes calculated stock

## 3. Backend: Views & API Review
- [x] Review views.py (103KB) — audit all ViewSets and endpoints
- [x] Verify no references to removed models
- [x] Review InventoryItemViewSet — ledger endpoint, stock calculations
- [x] Review ReceiptViewSet — creation, validation, hash generation, license balance deduction
- [x] Review PurchaseInvoiceViewSet — creation, stock impact
- [x] Review ExpenseViewSet
- [x] Review SalespersonViewSet
- [x] Review BranchViewSet
- [x] Review all 6 report views: Dashboard, CashDrawer, Installments, InventoryMovement, ProfitAndLoss, SalespersonPerformance
- [x] Review tools_views.py — sync, backup, restore
- [x] Review DesktopPrintView — installment schedule printing only
- [x] Review license validation endpoints
- [x] Review auth endpoints (login, token)

## 4. Backend: Middleware & Security
- [x] Review middleware.py — verify no tenant resolution, keep license tamper detection
- [x] Review security_utils.py — receipt signature, license row signature, machine ID
- [x] Review license_validator.py — 80-bit crypto, recovery code support

## 5. Backend: URLs & Settings
- [x] Review urls.py — verify all routes, no dead routes
- [x] Review settings.py — SQLite + WAL mode, DRF token auth
- [x] Verify db_router.py doesn't exist (or is not needed)

## 6. Frontend: Login & Auth Flow
- [x] Review/fix Login.jsx — password only → token
- [x] Review/fix BranchSelection.jsx — select active branch (skip if only one branch exists)
- [x] Review api.js — proper token storage and injection
- [x] Verify auth flow: Login → Branch Selection → SearchReceipts

## 7. Frontend: POS (Sales Entry) — ✅ ANCHOR PAGE
- [x] POS.jsx — working end-to-end
- [x] Verify POS.jsx creates receipts correctly with all fields
- [x] Verify installment schedule generation (month/year, 25th is display only)
- [x] Verify cash sale flow
- [x] Verify customer autocomplete from history

## 8. Frontend: Dimensions & Setup Data (Inventory, Salespersons, Suppliers)
- [x] Review/fix Dimensions page (combining Inventory, Salespersons, and Suppliers into one unified tab/view)
- [x] Inventory: show calculated stock, verify add/edit/soft-delete (don't overwrite opening balance)
- [x] Salespersons: verify add/edit/soft-delete
- [x] Suppliers: verify add/edit/soft-delete
- [x] Branches: Add branch management (add/edit branches) directly to the `BranchSelection.jsx` screen
- [x] Verify branch-scoped data isolation across all these entities

## 9. Frontend: Product Ledger
- [ ] Review/fix ProductLedger.jsx — remove mock data fallback
- [ ] Verify time-machine stock display
- [ ] Verify commission history display
- [ ] Verify purchase history display
- [ ] Verify sales history display

## 10. Frontend: Purchases/Procurement
- [x] Review/fix PurchaseEntry.jsx
- [x] Review/fix SearchPurchases.jsx
- [x] Verify creating purchase invoices adds stock
- [x] Verify purchase returns reduce stock

## 11. Frontend: Returns (مرتجع)
- [x] Review/fix ReturnReceipt.jsx
- [x] Verify returns create RETURN receipt with parent_receipt FK
- [x] Verify returns add stock back
- [x] Verify return items match original receipt items

## 12. Frontend: Search Receipts
- [x] Review/fix SearchReceipts.jsx — fix known issues
- [x] Verify filtering by date, customer, salesperson
- [ ] Verify receipt details display

## 13. Frontend: Expenses
- [x] Review/fix Expenses.jsx
- [x] Verify adding/editing/deleting expenses
- [x] Verify monthly filtering



## 14. [Reserved]
- [ ] Reserved for future architectural changes

## 15. Frontend: Reports (8 total)
- [x] Review/fix ReportsLayout.jsx and ReportsIndex.jsx
- [x] Review/fix DashboardReport.jsx — KPIs, sales summary
- [x] Review/fix CashDrawerReport.jsx — cash flow (possibly stub)
- [x] Review/fix ExpensesReport.jsx — branch expenses
- [x] Review/fix InstallmentsReport.jsx — schedule display
- [x] Review/fix InventoryMovementReport.jsx — stock in/out
- [x] Review/fix ProfitAndLossReport.jsx — per-product profitability
- [x] Review/fix ReceiptsReport.jsx — historical receipts
- [x] Review/fix SalespersonPerformanceReport.jsx — مندبة + عمولة تحصيل

## 16. Frontend: Settings
- [x] Review/discover settings page structure
- [x] Verify company settings (name, phones, footer)
- [x] Verify password management
- [x] Verify collection_commission_rate setting

## 17. Frontend: Tools
- [ ] Review/fix ToolsDashboard.jsx
- [ ] Review/fix SyncTab.jsx — offline sync UI
- [ ] Review/fix BackupTab.jsx — MUST WORK (backup & restore)
- [ ] Remove SmartImportTab.jsx or disable it (Smart Import removed from scope)

## 18. Demo Mode
- [x] Implement/review demo mode flow:
  - First launch (no license) → Demo Mode with random sample data
  - Every restart in demo → DB wiped, fresh demo data
  - License entered → Demo data deleted, DB empty, go to Setup
- [x] Review/create DemoBanner.jsx
- [x] Backend: POST /api/auth/demo/ endpoint
- [x] Generate realistic sample data (products, receipts, salespersons, branches)

## 19. System Init & Licensing
- [x] Review/fix Setup.jsx — first-time wizard
- [x] Review/fix ActivationSetup.jsx
- [x] Verify license validation flow
- [x] Implement recovery code as special license type
- [x] Verify machine ID binding

## 20. Desktop Packaging
- [x] Verify launcher.py works (PyWebView)
- [x] Verify React production build (npm run build)
- [x] Verify Django serves built React files
- [x] Test full desktop launch flow

## 21. End-to-End Testing
- [ ] Test complete flow: Launch → Demo → License → Setup → Use
- [ ] Test: Add inventory → Create receipt → Verify stock deduction
- [ ] Test: Create installment sale → Verify schedule
- [ ] Test: Purchase → Verify stock increase
- [ ] Test: Return → Verify stock restore
- [ ] Test: All 8 reports with real data
- [ ] Test: Backup → Restore → Verify data integrity
- [ ] Test: All UI in Arabic RTL
- [ ] Test: Salesperson performance (مندبة + عمولة تحصيل)
- [ ] Run backend test suite: python manage.py test api.tests -v 2
- [ ] Run frontend build: npm run build
