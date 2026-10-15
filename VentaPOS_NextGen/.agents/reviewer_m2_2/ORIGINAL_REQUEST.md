## 2026-07-04T04:37:09+03:00
You are Reviewer 2 (UI Logic & Payload Compliance) for VentaPOS NextGen POS Entry screen testing.
Your working directory is: d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\reviewer_m2_2

Objective:
Review the Lead Worker's work product (`worker_m2_1`) for frontend UI logic alignment, Cash Sale toggle behavior, and payload structure compliance.

Artifacts to inspect:
- `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\worker_m2_1\test_results.md`
- `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\worker_m2_1\run_m2_verification.py`
- `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\explorer_m1_2\analysis.md`

Tasks:
1. Verify Cash Sale toggle state logic: `is_cash_sale: true` defaults `customer_name` to `"عميل نقدي"`, `down_payment` to `total_amount`, and clears installments.
2. Verify Product and Customer debounced autocomplete payload and query parameters.
3. Verify financial balance validation (`Math.abs(total_amount - (down_payment + total_installments)) <= 0.01`).
4. Run independent verification commands if needed.

Deliverable:
Write review report and handoff to `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\reviewer_m2_2\handoff.md`. Send message to parent with verdict.
