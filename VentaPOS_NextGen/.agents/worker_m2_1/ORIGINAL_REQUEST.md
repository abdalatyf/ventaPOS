## 2026-07-04T01:28:40Z
You are the Lead Test & Verification Worker for VentaPOS NextGen POS Entry screen testing.
Your working directory is: d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\worker_m2_1

DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Objective:
Execute complete testing of the Add Receipt (POS Entry) screen for VentaPOS NextGen covering UI Functional Testing, End-to-End Submission Testing, and Backend Data Integrity Verification.

Tasks:
1. Environment Setup & API/UI Server Verification:
   - Verify backend server is running or can process requests at `http://127.0.0.1:8000/api/v1/`.
   - Create an automated end-to-end integration and verification script using Python (e.g., using `requests` or `django.test.Client`) or standard testing commands to test frontend/API endpoints and SQLite database records.

2. R1. UI & API Autocomplete / Functional Testing:
   - Test Product Autocomplete (`GET /api/v1/product-suggestions/?term=...&branch_id=1&month=...&year=...`): Confirm HTTP 200, returns matching items from database (e.g. "كبة").
   - Test Customer Autocomplete (`GET /api/v1/customer-suggestions/?term=...&field=name`): Confirm HTTP 200, returns customer suggestions.
   - Test Cash Sale toggle logic: Verify behavior when `is_cash_sale: true` (customer_name="عميل نقدي", down_payment=total_amount, empty installments).

3. R2. End-to-End Submission Testing:
   - Cash Sale Flow: Post a valid Cash Sale receipt to `POST /api/v1/receipts/` with tenant header (`X-Company-Code: 1234`). Confirm HTTP 201 response.
   - Installment Sale Flow: Post a valid Installment Sale receipt to `POST /api/v1/receipts/` with customer details, down payment, and installment schedule. Confirm HTTP 201 response.
   - Verify calculation logic: Check subtotal calculations, down payment deduction, total installments sum matching balance, and installment start date shifting (`sale_month + 1`, 25th of month `YYYY-MM-25`).

4. R3. Backend Data Integrity Verification:
   - Direct SQLite Querying: Query `backend/db/business_data.sqlite3` for the newly submitted `Receipt`, `SaleItem`, and `InstallmentPayment` records.
   - Verify exact mathematical totals: `Receipt.total_amount == sum(SaleItem.quantity * SaleItem.unit_price)`.
   - Verify installment totals: `Receipt.down_payment + sum(InstallmentPayment.amount) == Receipt.total_amount`.
   - Verify `receipt_hash`: Check HMAC-SHA256 hash generation on `Receipt`.
   - Verify tenant isolation: Confirm records are bound to `tenant_id` for company code `"1234"`.

5. Deliverables:
   - Write full execution log and verification output to `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\worker_m2_1\test_results.md`.
   - Deliver `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\worker_m2_1\handoff.md`.
   - Send a completion message to parent with summary of results and paths to artifacts.
