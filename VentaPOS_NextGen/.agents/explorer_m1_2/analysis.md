# Frontend Codebase Analysis Report: POS Entry Screen (`/pos`)

**Target Path**: `d:\Projects\VentaPOS\VentaPOS_NextGen\frontend`  
**Explorer**: Explorer M1_2 (Frontend Codebase Explorer)  
**Date**: 2026-07-04  

---

## 1. Component Location & Route Mapping

- **URL Route**: `http://localhost:5173/pos` (or relative route `/pos`)
- **App Router Config**: Defined in `d:\Projects\VentaPOS\VentaPOS_NextGen\frontend\src\App.jsx`
  - Line 8: `import POS from './pages/PosEntry';`
  - Line 76: `<Route path="pos" element={<POS />} />` (wrapped inside protected route `<AppShell />`)
- **Primary Screen Component**: `d:\Projects\VentaPOS\VentaPOS_NextGen\frontend\src\pages\PosEntry.jsx`
- **Secondary / Legacy Component**: `d:\Projects\VentaPOS\VentaPOS_NextGen\frontend\src\pages\POS.jsx` (Note: `App.jsx` specifically mounts `PosEntry.jsx` as the active POS component).

---

## 2. "Cash Sale" Toggle Analysis

### 2.1 State & Default Value
- **State**: `const [isCashSale, setIsCashSale] = useState(false);` (Line 42 in `PosEntry.jsx`)
- **Default Value**: `false` (defaults to Installment Sale mode unless checked).

### 2.2 Toggle UI Control
- Rendered at lines 428-436 as a Tabler / Bootstrap form switch:
  ```jsx
  <input 
    className="form-check-input" 
    type="checkbox" 
    checked={isCashSale} 
    onChange={e => setIsCashSale(e.target.checked)} 
  />
  <span className="form-check-label fw-bold">بيع نقدي بالكامل (كاش بدون أقساط)</span>
  ```

### 2.3 Impact on Customer Selection Section
- **DOM Rendering**: Rendered conditionally on `!isCashSale` (`{!isCashSale && ( ... Customer Card ... )}`).
- **When `isCashSale === true`**:
  - Customer Card (`col-md-6`) is omitted from the DOM.
  - Customer input fields (Name, Phone, Area, Address, Salesperson) are completely hidden.
  - Form validation: `required={!isCashSale}` on Customer Name is disabled.
- **When `isCashSale === false`**:
  - Customer Card is rendered with fields: Customer Name (`required`), Phone, Area, Address, Salesperson select dropdown (`salespersons`).

### 2.4 Impact on Financials & Installments Section
- **DOM Rendering**: Rendered conditionally on `!isCashSale` (`{!isCashSale && ( ... Financials Card ... )}`).
- **When `isCashSale === true`**:
  - Financials card (Down Payment, 3 Installment Groups, and Schedule Preview Table) is omitted from the DOM.
  - Down Payment payload value is automatically overridden to `totalCart` (`down_payment: isCashSale ? totalCart : dpAmount`).
  - Installment Schedule array payload is set to empty list `[]`.
  - Installment System string payload is set to empty string `""`.
  - Customer Name sent in payload defaults to `"عميل نقدي"`.
- **When `isCashSale === false`**:
  - Down Payment input field is interactive.
  - 3 Installment groups (Amount x Count) are interactive.
  - Live calculated notebook schedule preview table (`schedule`) is rendered.

---

## 3. Product & Customer Autocomplete Analysis

All HTTP requests are routed through `src/api.js` (Axios instance configured with `baseURL`, `Authorization: Token ...`, `X-Company-Code`, `X-Machine-ID`, and `X-Branch-ID` headers).

### 3.1 Customer Autocomplete Fields (Name, Phone, Area, Address)

Each customer input field has an independent `useEffect` with debounced execution:
- **Debounce Mechanism**: 300ms delay using `setTimeout` and cleanup via `clearTimeout`.
- **Trigger Threshold**: `term.trim().length >= 1`.
- **API Endpoint**: `GET /api/v1/customer-suggestions/`

| Field | Query Parameters Sent | State Handlers & UI Dropdown |
|-------|----------------------|------------------------------|
| **Name** | `term=customer.name`, `field=name`, `salesperson_id=...`, `current_area=...` | `setNameSuggestions`, dropdown `showNameSuggestions` |
| **Phone** | `term=customer.phone`, `field=phone`, `salesperson_id=...`, `current_area=...`, `current_name=...` | `setPhoneSuggestions`, dropdown `showPhoneSuggestions` |
| **Area** | `term=customer.area`, `field=area`, `salesperson_id=...` | `setAreaSuggestions`, dropdown `showAreaSuggestions` |
| **Address** | `term=customer.address`, `field=address`, `salesperson_id=...`, `current_area=...`, `current_name=...` | `setAddressSuggestions`, dropdown `showAddressSuggestions` |

- **Data Mapping & Selection**:
  - Backend response structure: `[ { "value": "اسم العميل أو المنطقة" }, ... ]`
  - Selecting an item sets the field value in `customer` state object, closes dropdown (`setShow...Suggestions(false)`), and clears suggestions array.

### 3.2 Product Autocomplete Field

- **Debounce Mechanism**: 300ms delay using `setTimeout` with cleanup via `clearTimeout`.
- **Trigger Condition**: `productSearchTerm.trim().length >= 1` AND `productSearchTerm !== selectedProduct?.value`.
- **API Endpoint**: `GET /api/v1/product-suggestions/`
- **Query Parameters**:
  - `term`: `productSearchTerm`
  - `branch_id`: `localStorage.getItem('branchId')` (with fallback logic if missing).
  - `month`: `date.month`
  - `year`: `date.year`
- **Data Mapping & UI**:
  - Backend response format: `[ { "id": "uuid/id", "value": "اسم الصنف", "max": 15 }, ... ]`
  - Dropdown displays: `{p.value} - {p.max} متاح` (Item name - Available stock limit).
- **Selection Handling (`handleSelectProduct`)**:
  - Sets `selectedProductId` to `prod.id`.
  - Sets `selectedProduct` to `prod`.
  - Sets `productSearchTerm` to `prod.value`.
  - Fetches product unit price detail via `GET /api/v1/inventory-items/{prod.id}/`.
  - Populates `selectedPrice` with `res.data.initial_purchase_price`.

---

## 4. Frontend Calculation & Validation Logic

### 4.1 Subtotal & Total Invoice Calculation (`totalCart`)
- **Cart Item Structure**: `{ id, name, quantity, price }`
- **Item Total**: `item.price * item.quantity`
- **Total Invoice Amount**: `totalCart = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0)`
- *Note*: Discounts and Taxes are not explicitly calculated via separate rate inputs on `PosEntry.jsx`; unit price * quantity forms `totalCart`.

### 4.2 Stock Quantity Validation on Cart Addition (`addToCart`)
- When adding an item to cart:
  ```js
  maxStock = selectedProduct.max;
  qtyToAdd = parseInt(selectedQuantity);
  existingQty = cart[existingIdx]?.quantity || 0;
  newTotalQty = existingQty + qtyToAdd;
  ```
- **Constraint**: If `newTotalQty > maxStock`, displays an alert: `الكمية المطلوبة (مع اللي في السلة) أكتر من البضاعة المتاحة في المخزن للفترة دي...` and blocks addition.

### 4.3 Installment Starting Month Logic (`schedule`)
Calculated dynamically in `useEffect` whenever `groups` or `date` changes (lines 216-246):
```js
let currentMonth = parseInt(date.month);
let currentYear = parseInt(date.year);

// Shift to next month
currentMonth++;
if (currentMonth > 12) {
  currentMonth = 1;
  currentYear++;
}
```
- **Key Discovery**: The installment schedule payment months **start on `sale_month + 1`**.
- If sale month is 12 (December), the first payment month rolls over to month 1 (January) and year increments by 1.
- Each installment in active groups (`amount > 0` and `count > 0`) advances `currentMonth` by 1 (with year rollover `if (currentMonth > 12)`).

### 4.4 Financial Matching Validation Before Submit
- For Installment Sales (`isCashSale === false`):
  `expectedTotal = dpAmount + totalInstallments`
  Validation check: `Math.abs(totalCart - expectedTotal) > 0.01`
- If totals do not balance, displays alert and cancels form submission.

---

## 5. Invoice Submission Payload Structures

**Submit Endpoint**: `POST /api/v1/receipts/`

### 5.1 Cash Sale Flow Payload (`is_cash_sale: true`)
```json
{
  "customer_name": "عميل نقدي",
  "phone_number": "",
  "address": "",
  "area": "",
  "salesperson": null,
  "is_cash_sale": true,
  "total_amount": 1500,
  "down_payment": 1500,
  "sale_month": 7,
  "sale_year": 2026,
  "items": [
    {
      "inventory_item_id": "4",
      "quantity": 2,
      "unit_price": 750
    }
  ],
  "installments": [],
  "installment_system": ""
}
```

### 5.2 Installment Sale Flow Payload (`is_cash_sale: false`)
```json
{
  "customer_name": "محمد علي أحمد",
  "phone_number": "01098765432",
  "address": "10 شارع الثورة",
  "area": "مدينة نصر",
  "salesperson": "1",
  "is_cash_sale": false,
  "total_amount": 6000,
  "down_payment": 1000,
  "sale_month": 7,
  "sale_year": 2026,
  "items": [
    {
      "inventory_item_id": "2",
      "quantity": 1,
      "unit_price": 6000
    }
  ],
  "installments": [
    {
      "payment_month": 8,
      "payment_year": 2026,
      "amount": 2500
    },
    {
      "payment_month": 9,
      "payment_year": 2026,
      "amount": 2500
    }
  ],
  "installment_system": "2500*2"
}
```

---

## 6. Summary of Findings & Next Steps

1. `PosEntry.jsx` is fully implemented and correctly handles both Cash Sale and Installment Sale flows.
2. Autocomplete debouncing (300ms) and field filtering work seamlessly with backend `/customer-suggestions/` and `/product-suggestions/`.
3. Financial validation enforces `total_amount === down_payment + total_installments` within 0.01 tolerance for Installment sales.
4. Starting month logic correctly shifts installment schedules to `sale_month + 1`.
5. Frontend explorer findings are ready for E2E testing execution in Milestone 2.
