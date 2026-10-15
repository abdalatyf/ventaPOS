# Handoff Report — Frontend POS Entry Screen (`/pos`) Investigation

**Agent**: Explorer M1_2 (Frontend Codebase Explorer)  
**Working Directory**: `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\explorer_m1_2`  
**Date**: 2026-07-04  

---

## 1. Observation

- **App Routing & Entry Component**:
  - `d:\Projects\VentaPOS\VentaPOS_NextGen\frontend\src\App.jsx`:
    - Line 8: `import POS from './pages/PosEntry';`
    - Line 76: `<Route path="pos" element={<POS />} />`
  - Rendered component file: `d:\Projects\VentaPOS\VentaPOS_NextGen\frontend\src\pages\PosEntry.jsx` (783 lines).

- **Cash Sale Toggle**:
  - Line 42: `const [isCashSale, setIsCashSale] = useState(false);`
  - Lines 428-436: Checkbox input binding `isCashSale`.
  - Line 441: `{!isCashSale && ( ... Customer Info Card ... )}` hides Customer inputs when `isCashSale === true`.
  - Line 673: `{!isCashSale && ( ... Financials Card ... )}` hides Down Payment & Installment Groups inputs when `isCashSale === true`.

- **Autocomplete Endpoints & Query Parameters**:
  - `GET /customer-suggestions/` with params `term`, `field` (`name`, `phone`, `area`, `address`), `salesperson_id`, `current_area`, `current_name` (lines 80-173).
  - `GET /product-suggestions/` with params `term`, `branch_id`, `month`, `year` (lines 185-213).
  - Debounce timer: 300ms `setTimeout` (lines 94, 120, 144, 170, 210).

- **Installment Starting Month Logic**:
  - Lines 216-246:
    ```js
    let currentMonth = parseInt(date.month);
    let currentYear = parseInt(date.year);
    currentMonth++;
    if (currentMonth > 12) { currentMonth = 1; currentYear++; }
    ```
    This shifts the payment schedule start date to `sale_month + 1`.

- **Invoice Submission Payload**:
  - Lines 363-385: `POST /receipts/` payload:
    - Cash Sale: `is_cash_sale: true`, `customer_name: "عميل نقدي"`, `down_payment: totalCart`, `installments: []`, `installment_system: ""`.
    - Installment Sale: `is_cash_sale: false`, `customer_name: customer.name`, `down_payment: dpAmount`, `installments: schedule`, `installment_system: installmentSystemStr`.

- **Financial Validation**:
  - Lines 349-357: `Math.abs(totalCart - (dpAmount + totalInstallments)) > 0.01` displays an alert and blocks invoice submission if math does not match.

---

## 2. Logic Chain

1. **Route Mapping**: Inspecting `App.jsx` confirms route `/pos` maps to `POS`, which imports `pages/PosEntry.jsx`. Therefore, `PosEntry.jsx` is the component active when users visit `http://localhost:5173/pos`.
2. **Toggle Mechanics**: `isCashSale` state defaults to `false`. Toggling it to `true` conditionally unmounts both the Customer Information card and the Financials/Installments card, enforcing a cash sale flow with `customer_name: "عميل نقدي"` and `down_payment: totalCart`.
3. **Data Fetching & Debouncing**: Autocomplete effects for Customer (Name, Phone, Area, Address) and Products monitor input state, waiting 300ms before sending GET requests to `/customer-suggestions/` and `/product-suggestions/`. Product selection triggers a secondary detail fetch (`/inventory-items/{id}/`) to populate default unit prices.
4. **Calculations & Date Shifting**:
   - Total cart amount is calculated as `sum(price * quantity)`.
   - Installment schedule generation advances the initial payment month by `+1` relative to `date.month` (handling year increment when month > 12).
   - Validation ensures `down_payment + total_installments === total_amount` before API post.
5. **Backend Alignment**: The constructed `POST /receipts/` payload structure matches the Django API contract (expecting `customer_name`, `is_cash_sale`, `total_amount`, `down_payment`, `sale_month`, `sale_year`, `items`, `installments`, `installment_system`).

---

## 3. Caveats

- **Legacy File**: `pages/POS.jsx` exists in the codebase but is NOT imported by `App.jsx`. All findings in this report pertain to `pages/PosEntry.jsx` which is actively mounted at `/pos`.
- **Taxes / Discounts**: `PosEntry.jsx` does not include standalone discount or tax percentage UI fields; unit prices * quantity directly sum to `total_amount`.
- **Read-Only Verification**: Code analysis was conducted via static inspection. E2E live HTTP submission testing will be executed during Milestone 2.

---

## 4. Conclusion

The frontend POS Entry screen (`pages/PosEntry.jsx`) is fully structured, features robust debounced autocomplete search for both products and customers, correctly hides/shows fields via the Cash Sale switch, implements accurate `sale_month + 1` installment date shifting, enforces strict balance validation, and prepares valid JSON payloads for backend receipt creation.

---

## 5. Verification Method

To independently verify this investigation:
1. **File Inspection**: View `d:\Projects\VentaPOS\VentaPOS_NextGen\frontend\src\App.jsx` line 8 & line 76.
2. **Component Code**: Inspect `d:\Projects\VentaPOS\VentaPOS_NextGen\frontend\src\pages\PosEntry.jsx`:
   - Toggle: lines 42, 428-436, 441, 673.
   - Autocomplete: lines 74-214.
   - Installment Month Shift: lines 216-246.
   - Validation & Payload: lines 342-385.
3. **Analysis Artifact**: Read full analysis report at `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\explorer_m1_2\analysis.md`.
