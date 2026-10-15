# POS & Receipts Documentation
**Role**: Frontend Architect
**Target System**: VentaPOS NextGen (React Frontend + Django Backend)
**Context Files**: `POS.jsx`, `SearchReceipts.jsx`, `06_ui_design_tokens.md`, `urls.py`, `api_contract.md`.

---

## 1. The Point of Sale (POS) UI Architecture

The `POS.jsx` page is the heart of the system, designed for maximum speed, accuracy, and ease of use for the cashier. The layout is structured in a two-column grid (`col-lg-7` and `col-lg-5`), reflecting a clear separation of concerns.

### 1.1 Right Column (`col-lg-7`): Receipt Context & Cart
This section focuses on "Who is buying?" and "What are they buying?".

- **Receipt Context**: Contains dropdowns for the Sale Month, Sale Year, and Salesperson selection.
- **Customer Information**: 
  - Visible only for Installment Sales (hidden for Cash Sales).
  - Includes fields for Name, Phone, Area, and Address.
  - Features **Context-Aware Auto-suggestions**: When typing a customer name, the API (`GET /api/customer-suggestions/`) uses the selected Salesperson and Area to prioritize relevant customers, drastically speeding up data entry.
- **Product Cart**:
  - An autocomplete search bar for products (`GET /api/product-suggestions/`).
  - Fields for Quantity and Unit Price.
  - A dynamic Cart Table displaying the selected items, quantities, prices, line totals, and delete actions.
  - A footer summarizing the `Total Sales` (إجمالي الأصناف).

### 1.2 Left Column (`col-lg-5`): Financials & Submission
This section focuses on "How are they paying?".

- **Cash Toggle**: A segmented button to switch between "Cash" (كاش) and "Installments" (تقسيط).
  - *Cash Mode*: Hides customer fields and installment grids, defaulting the down payment to the total cart value.
  - *Installments Mode*: Reveals the Down Payment input and the Installment System grid.
- **Installment Grid**:
  - Supports up to 3 separate installment systems simultaneously (e.g., System 1: 5 months * 200 EGP, System 2: 2 months * 100 EGP).
  - Features **Two-Way Binding (Sync)**: The user can type the formula as text (e.g., `200*5 + 100*2`) and the 3x2 grid of inputs updates automatically, or vice-versa.
- **Dynamic Schedule Generator (`genSchedule`)**:
  - Automatically calculates the payment month and year for every generated installment based on the selected `Sale Month` and `Sale Year`, handling year rollovers seamlessly (e.g., crossing from December to January).
- **Validation & Totals Panel**:
  - Displays the Total Sales, Total Payments (Down payment + Installments), and the Difference (الفرق).
  - Uses conditional styling: **Green** when balanced (Difference = 0), **Red** when unbalanced.
  - The "Save Receipt" button is automatically disabled if the math does not balance.

### 1.3 Native Arabic & Digit Support
A core feature of the UI is native support for Arabic/Hindi numerals (٠١٢٣٤٥٦٧٨٩). 
- Custom utility functions (`toArabic` and `toEnglish`) transparently convert user input. 
- The user sees and types Arabic digits, but the React state and API payloads strictly process standardized English digits to prevent database parsing errors.
- The `fmt` function guarantees that all displayed monetary values are formatted with `ar-EG` locale separators.

---

## 2. The Receipt Lifecycle & Backend Submission

Upon clicking "حفظ الوصل" (Save Receipt), the component fires the `handleSave` function:
1. Validates the cart is not empty and that financials balance.
2. Constructs the payload:
   - `is_cash_sale`: Boolean
   - `customer_name`, `phone_number`, `area`, `address`
   - `sale_month`, `sale_year`, `salesperson`
   - `total_amount`, `down_payment`
   - `sale_items`: Array of `{inventory_item, quantity, sell_price}`
   - `installment_payments`: Flat array of all generated `{amount, month, year}` objects.
3. Sends a `POST` request to `/api/v1/receipts/`.
4. Navigates to `/receipts` (The Ledger) upon success.

---

## 3. Search Receipts & Ledger Management

The `SearchReceipts.jsx` page (دفتر المبيعات) allows cashiers and admins to review historical data.

### Features
- **Advanced Filtering**: Filter by Date Range (Month/Year), Salesperson, Area, and Customer Name.
- **Real-Time Calculation**: Displays total sales dynamically based on the current filtered dataset.
- **Returns & Refunds**: Context menu integration to initiate a `RETURN` receipt, automatically calculating the remaining debt or refund cash amount (handled in `ReturnReceipt.jsx`).
- **Bulk Actions**: Select multiple rows for batch PDF printing or deletion (if permissions allow).
- **Pagination/Infinite Scroll**: Employs infinite scrolling or paginated API calls to gracefully handle ledgers with tens of thousands of records without crashing the browser.

---

## 4. Architectural Notes

- **State Management**: `POS.jsx` utilizes localized React state (`useState`) and derived state for high-performance reactive calculations. No global state (Redux) is needed due to the contained nature of a single transaction.
- **Performance**: Debouncing is strictly enforced on all `triggerSuggestions` inputs (Product, Customer Name, Phone, Area) to prevent API spamming while typing.
- **Printing Architecture**: VentaPOS NextGen enforces an offline-first desktop philosophy. The frontend does not use `window.print()` or browser PDF viewers. Instead, it hits a backend endpoint that triggers `os.startfile()` (via SumatraPDF) for silent, direct thermal printing.
