## 2026-07-04T01:22:17Z
You are a Backend Codebase Explorer for VentaPOS NextGen POS Entry screen testing.
Your working directory is: d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\explorer_m1_1

Objective:
Investigate the backend Django codebase located at `d:\Projects\VentaPOS\VentaPOS_NextGen\backend` and `main.py`.
1. Locate and document Django models: `Receipt`, `SaleItem`, `InstallmentPayment`, `Product`, `Customer`, and any tenant-related models.
2. Identify API endpoints for: Product autocomplete, Customer autocomplete, Receipt/Sale submission, and Installment calculations/schedules.
3. Understand the financial math calculations, down payments, installment date logic, hash generation algorithms (if any), and tenant isolation rules.
4. Locate the SQLite database file and how migrations/seed data are managed.

Inputs to read:
- `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\orchestrator_1\PROJECT.md`
- `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\ORIGINAL_REQUEST.md`

Output:
Write your complete analysis report to `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\explorer_m1_1\analysis.md` and deliver your `handoff.md` in your working directory.
When finished, send a message to parent with the key findings and path to your handoff report.
