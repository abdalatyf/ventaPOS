## 2026-07-04T01:22:17Z
You are a Frontend Codebase Explorer for VentaPOS NextGen POS Entry screen testing.
Your working directory is: d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\explorer_m1_2

Objective:
Investigate the frontend codebase located at `d:\Projects\VentaPOS\VentaPOS_NextGen\frontend`.
1. Locate the POS Entry screen component rendered at route `/pos` (or `http://localhost:5173/pos`).
2. Analyze the "Cash Sale" toggle implementation and how it controls visibility/interactivity of Customer selection and Installment schedule inputs.
3. Analyze Product and Customer autocomplete components: API calls made, query parameters, debouncing, data mapping.
4. Analyze calculation logic on the frontend: subtotals, discounts, taxes, down payments, total amount, and installment date shifting (starting month logic).
5. Identify payload structure sent to backend upon invoice submission for both Cash Sale and Installment Sale flows.

Inputs to read:
- `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\orchestrator_1\PROJECT.md`
- `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\ORIGINAL_REQUEST.md`

Output:
Write your complete analysis report to `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\explorer_m1_2\analysis.md` and deliver your `handoff.md` in your working directory.
When finished, send a message to parent with the key findings and path to your handoff report.
