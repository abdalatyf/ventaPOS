# VentaPOS NextGen — UI & UX Style Guide

This document defines the visual identity, user experience, and interaction rules for the VentaPOS NextGen application.

---

## 1. Language & Tone
- **Strictly RTL & Arabic**: The entire application MUST be in Arabic and Right-to-Left (RTL).
- **Tone (لغة سوق مهنية ومبسطة)**: Professional but easy Egyptian Arabic.
  - Avoid overly strict corporate Arabic.
  - Avoid excessive street slang (like 'يا معلم').
  - Use clear business terms: (العميل, البضاعة, الخزنة, الفاتورة, الدفتر, النقدية, المندبة, المرتجع).

---

## 2. UI Framework & Aesthetics
- **Core Framework**: Bootstrap v5 utilities (via Tabler UI), combined with custom CSS.
- **Tailwind**: Do NOT introduce Tailwind CSS.
- **Glassmorphism**: Use custom "premium" glassmorphism classes (e.g., `.premium-card`) to create depth and modern aesthetics.
- **Typography**: Use the **'Cairo'** font for clean Arabic readability.

---

## 3. Color Palette (Derived from Logo)
- **Primary Brand Color**: Deep Blue (`#123F68`)
- **Secondary / Accent Color**: Emerald Green (`#1DA368`) — used for primary success actions like "Save", "Pay", or "Confirm".
- **Theme**: Light mode only. High-contrast is required for warehouse and office environments.

---

## 4. Layout & Data Density
- **Fluid Layout**: Use **Fluid Containers** (`container-fluid`) across the app to maximize horizontal screen space.
- **Compact Data Density**: Use smaller padding and smaller fonts in data tables. The manager must be able to see maximum rows without scrolling.

---

## 5. Data Entry UX (Keyboard-First)
Speed is critical since the manager copies data from paper notebooks into the system.
- **Auto-Focus**: Inputs must auto-focus on page load where appropriate.
- **Enter Key Navigation**: Pressing "Enter" should move focus to the next logical field, NOT submit the form prematurely.
- **Tab-Indexing**: Enforce logical `tabindex` flows for rapid data entry.

---

## 6. Number, Date, & Input Constraints

### 6.1 Banned Input Types
- **No `<select>` for Dynamic Data**: You are strictly FORBIDDEN from using standard `<select>` dropdowns for data that comes from the database (e.g., Salespersons, Suppliers, Customers, Products).
  - *Alternative*: You MUST use a custom React Autocomplete component with a searchable dropdown list (like the one used for Products in `POS.jsx`).
  - *Exception*: Standard `<select>` is ONLY allowed for hardcoded, fixed enums (e.g., Payment Type: "Cash" vs "Installment", or Receipt Type).

### 6.2 Date Inputs
- **Adding/Editing Dates**: Since the system uses strict `MM/YYYY` business dates, do NOT use native `<input type="date">` or `<input type="month">`. You MUST use **two separate numeric inputs** (one for Month, one for Year) placed side-by-side.
- **Filtering Dates**: For filtering tables by date, use the exact same two numeric inputs. If both inputs are left blank, it means "Select All" (no date filter applied).

### 6.3 Number Formatting
- **Western Digits Only**: All numbers displayed to the user MUST use standard Western digits (0-9) to improve rendering performance and eliminate split-brain data handling. (Arabic-Indic digits ٠١٢٣٤٥٦٧٨٩ are officially banned).
- **Display Format**: Use standard JavaScript formatting (`Intl.NumberFormat('en-US')` or simple `toLocaleString()`). Thousands separator is `,` (comma). Decimal separator is `.` (dot). Show 2 decimal places for currency amounts.

---

## 7. Table UX Rules (Mandatory Patterns)

### 7.1 Column Sorting (Guideline)
- Data tables SHOULD support clickable column headers for ascending/descending sort.
- Use Tabler arrow icons to indicate sort direction.
- Not mandatory for very small tables (e.g., branches list with < 5 rows).

### 7.2 Accordion-Based Add/Edit Forms (Rule)
- All "Add New" and "Edit" forms for dimensions (Inventory, Salespersons, Suppliers, Expenses) MUST use collapsible Bootstrap Accordions, NOT modals or static cards.
- This maximizes vertical table space and creates consistent muscle memory across the app.

### 7.3 Inline Live-Search Filtering (Rule)
- Every primary data table MUST have a search input docked directly above it.
- Search filters the loaded data instantly without refreshing the page (client-side filter).

### 7.4 ID Columns
- Receipts and Purchase Invoices already have branch-scoped sequential numbers (`receipt_number`, `invoice_number`). Display those.
- For all other entities (Inventory, Salespersons, Suppliers, Expenses): use the raw database PK if an ID column is needed, or omit the ID column entirely and let the user search by name.

### 7.5 Sticky Headers & Scroll Architecture
- All data tables MUST follow the Unified Table Scroll Architecture defined in `frontend/TABLE_UX_GUIDELINES.md`.

---

## 8. Frontend Payload Sanitization (Rule)
- **Comma Stripping**: Before sending ANY numeric value to the API, the frontend MUST strip thousands-separator commas (`.replace(/,/g, '')`).
- Django REST Framework throws `400 Bad Request` if it receives `"1,500"` for a `DecimalField`. This rule prevents API crashes from formatted money inputs.
- Apply this sanitization in the API layer (e.g., in `api.js` interceptors or at the form submission level), not in individual input handlers.

---

## 9. CRUD Standard Rules

### 9.1 Create (Add New)
- **Validation**: All forms MUST have client-side validation for required fields before API submission.
- **Feedback**: Success MUST show a Toast/Snackbar (not an intrusive modal alert).
- **Reset**: The form MUST clear its fields and refocus the first input after a successful creation to allow rapid sequential entry.

### 9.2 Search (Read/Filter)
- **Debounce**: Search inputs MUST have a debounce (e.g., 300ms) to prevent spamming the API on every keystroke.
- **Feedback**: Results MUST show a loading spinner while fetching.
- **Empty State**: Empty results MUST display a clear "No results found" (لا توجد نتائج) message.

### 9.3 Edit (Update)
- **Simple Fields**: If the field is a simple text field (e.g., Supplier name), use **Inline Editing** by double-clicking the field directly in the table.
- **Complex Relations**: If the entity is related to other models (like products or installment systems), clicking "Edit" MUST navigate to a dedicated Edit page or populate an Edit Accordion.

### 9.4 Delete
- **Confirmation**: Clicking "Delete" MUST trigger a confirmation dialog (e.g., SweetAlert or a custom Tabler modal) asking "Are you sure?" (هل أنت متأكد؟).
- **Soft Delete**: Deletions are ALWAYS Soft Deletes (updating `is_deleted=True` on the backend). Never use hard deletes.

---

## 10. Reporting System UX Rules

- **Unified <ReportTable> Component**: All reports MUST strictly use the unified <ReportTable> component for rendering data. Do not build custom raw HTML tables for reports.
- **Context-Driven Dates**: Reports MUST consume year, month, and ranchId directly from ReportsContext. Do not create local state for primary date filters (no date pickers).
- **Summary Cards (KPIs)**: All report totals, aggregations, and key metrics MUST be passed to the summaryCards prop of <ReportTable> to be displayed as KPI cards above the table. Do not implement footer rows (<tfoot>) for totals.
- **Sorting**: The <ReportTable> handles client-side multi-column sorting natively via the sortableColumns prop. Do not build custom click-to-sort logic on table headers.
- **Secondary Filters**: Any additional filters specific to a report (e.g., Salesperson dropdown, search by name, sale type) MUST be passed to the enderFilters render prop of <ReportTable>.
