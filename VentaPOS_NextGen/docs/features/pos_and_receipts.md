# POS & Receipts Documentation
**Role**: Frontend Architect
**Target System**: VentaPOS NextGen (React Frontend + Django Backend)
**Context Files**: `POS.jsx`, `PosEntry.jsx`, `SearchReceipts.jsx`, `06_ui_design_tokens.md`, `urls.py`, `api_contract.md`.

---

## 1. The Receipt Lifecycle (From Addition to Saving)

The receipt (فاتورة) is the core transactional entity in VentaPOS. Its lifecycle is handled primarily in `PosEntry.jsx` for creation and `SearchReceipts.jsx` for retrieval and management.

### Phase A: Customer & Context Initialization
- The user can toggle between a **Cash Sale** (بيع نقدي بالكامل) or an **Installment Sale** (بيع بالتقسيط).
- For Installment Sales, the user enters customer details (Name, Phone, Area, Address).
- **Smart Suggestions (Customer)**: As the user types, debounced API calls (`GET /api/customer-suggestions/`) fetch existing customer records. These APIs are heavily optimized, returning lightweight payloads instead of full customer objects, which prevents UI freezing and reduces network payload size.
- The transaction date (Month/Year) is initialized to the current date.

### Phase B: Cart Management (البضاعة)
- The user searches for products using an autocomplete field (`GET /api/product-suggestions/`). Like customer suggestions, this is an optimized micro-feature returning only necessary fields (id, name, price) to ensure the dropdown feels instantaneous even with large inventories.
- The UI displays available stock (max). The user enters a quantity and confirms the unit price.
- **Validation**: The system checks if the requested quantity (plus any already in the cart) exceeds the available `max` stock.
- The product is added to the local `cart` state array, and the `totalCart` (إجمالي الفاتورة) is recalculated instantly.

### Phase C: Financials (الماليات)
- For Cash Sales, the entire total is implicitly marked as the down payment.
- For Installment Sales, the user enters the **Down Payment** (مقدم). The remainder is scheduled using the Installment Groups engine (see Section 2).

### Phase D: Submission & Backend Saving
- Upon clicking "حفظ الفاتورة" (Save Receipt), a final client-side validation ensures that the cart is not empty and that the financial totals match: `Total Cart == Down Payment + Total Installments`.
- A massive JSON payload is constructed containing:
  - `is_cash_sale` boolean flag.
  - Customer info and `salesperson`.
  - `total_amount` and `down_payment`.
  - `items`: An array mapping the cart `inventory_item_id`, `quantity`, and `unit_price`.
  - `installments`: An array of calculated schedule objects (`payment_month`, `payment_year`, `amount`).
  - `installment_system`: A string representing the formula (e.g., "500*3 + 200*1").
- The payload is sent via `POST /receipts/`. On success, the user is navigated back to the ledger (`/`).

### Phase E: Retrieval & Ledger View
- In `SearchReceipts.jsx`, the user views the ledger (دفتر المبيعات).
- Receipts are fetched via `GET /receipts/` with advanced query parameters (month, year, salesperson, search filters).
- Infinite scrolling is implemented via a scroll event listener that triggers pagination requests (`nextPageUrl`) as the user nears the bottom of the table.
- Bulk actions (`POST /receipts/bulk_pdf/`, `POST /receipts/bulk_delete/`) allow cashiers to generate PDFs or delete multiple receipts at once.

---

## 2. Installment Payment System Logic

The UI includes a robust engine for modeling the Egyptian retail installment structure (التقسيط), heavily relying on reactive state updates in `PosEntry.jsx`.

### Structure
- The system supports up to **3 Installment Groups**. Each group consists of:
  - `amount` (القسط): The financial value to be paid monthly.
  - `count` (عدد الشهور): How many consecutive months this amount will be paid.

### Dynamic Schedule Generation
- Whenever the `groups` state or the `date` (Sale Date) changes, a `useEffect` hook recalculates the payment schedule.
- **Starting Point**: Payments always start on the month *following* the sale month (`sale_month + 1`).
- The logic loops through active groups (where count > 0 and amount > 0) and pushes sequential `{month, year, amount}` objects into a `schedule` array.
- The system handles year rolrollovers seamlessly (e.g., Month 12 + 1 -> Month 1, Year + 1).

### Financial Validation
- The UI maintains a strict mathematical lock: The sum of the `downPayment` plus the sum of all generated `schedule.amount` entries **must exactly equal** the `totalCart` value.
- If a discrepancy of even `0.01` EGP exists, the totals box highlights the error in red (`text-danger`) and blocks form submission, forcing the cashier to correct the math.

---

## 3. State Management Architecture

The POS and Receipts pages rely entirely on **React Local State (Hooks)**. No global state managers (like Redux, Zustand, or Context API) are utilized for these specific features.

- **`useState` heavy components**: `PosEntry.jsx` utilizes roughly 20 separate `useState` declarations. It heavily relies on primitive values and small objects to control the cart, customer form, financial groups, and UI toggles (e.g., showing/hiding dropdown suggestions).
- **Derived State**: Variables like `totalCart` and `totalInstallments` are not stored in state; they are derived continuously on each render using array `reduce` methods to ensure they are always synchronized with the `cart` and `schedule` states.
- **`useEffect` for Side Effects & Reactivity**: 
  - Used for debouncing search inputs (e.g., delaying API calls for `name`, `phone`, `area` by 300ms).
  - Used as a watcher to rebuild the installment `schedule` whenever the financial `groups` change.
- **Performance Optimizations**:
  - `SearchReceipts.jsx` uses `React.memo` for the `ReceiptRow` component. A custom comparison function ensures that rows only re-render if their specific `isSelected` status or raw data `r` changes, which is critical for performance when rendering hundreds of ledger rows.

---

## 4. Architectural Notes & Areas for Improvement

As a Frontend Architect, reviewing these components reveals several areas that require refactoring and improvement for scalability and maintainability:

### 1. `POS.jsx` is a Stale Placeholder
- The `POS.jsx` file contains static placeholder text (`قائمة البضاعة ستظهر هنا`) and does not actually function. `PosEntry.jsx` contains the real implementation. 
- **Action**: `POS.jsx` should be deleted, and `PosEntry.jsx` should be renamed to `POS.jsx`, updating router links accordingly.

### 2. State Bloat in `PosEntry.jsx`
- Managing 20+ `useState` hooks makes the component highly brittle and difficult to test.
- **Action**: Refactor the state into a `useReducer` hook. Grouping related states (`CustomerState`, `CartState`, `FinancialState`) will clean up the component and make state transitions predictable.

### 3. Missing Client-Side Caching (Network Inefficiency)
- The debounced autocomplete fields (Customers, Products) fire API requests repeatedly for the same search terms.
- **Action**: Integrate **React Query** (or SWR) to cache API responses. Alternatively, implement a simple local map cache to prevent redundant backend hits.

### 4. Hardcoded API Calls inside Components
- API calls (`api.get('/receipts/')`) are written directly inside the UI components.
- **Action**: Implement the **Repository Pattern**. Create service files (e.g., `services/ReceiptService.js`) to abstract Axios calls. This separates business data fetching from UI rendering and makes it easier to mock during testing.

### 5. Type Safety & Validation
- The mathematical validation for installments is done manually inside `handleSubmit`.
- **Action**: Migrate to a schema validation library like **Yup** or **Zod** combined with `react-hook-form` to handle complex cross-field validations (e.g., `down_payment + total_installments == total_amount`).

### 6. Printing Implementation Discrepancy
- The architecture guidelines (`AGENTS.md`) specify that the backend interacts directly with the local OS (e.g., `os.startfile` with SumatraPDF) for an offline-first desktop feel.
- However, the frontend (`handlePrint` in `SearchReceipts.jsx`) relies on `window.open(res.data.pdf_url, '_blank')`, which relies on the browser's built-in PDF viewer. 
- **Confirmed Decision**: The backend `os.startfile()` / SumatraPDF approach is the confirmed standard. The frontend must be updated to call a dedicated `desktop_print` endpoint that triggers silent local printing, completely removing the browser PDF viewer.
