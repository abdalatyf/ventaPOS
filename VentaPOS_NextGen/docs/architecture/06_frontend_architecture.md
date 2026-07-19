# VentaPOS NextGen - Frontend Architecture & Developer Guide

## Introduction
This document serves as the comprehensive reference guide for building and maintaining frontend components in the VentaPOS NextGen ecosystem. It unifies our visual design tokens, the strict Egyptian Market language guidelines, and our advanced native-scroll table architecture. 

By following this guide step-by-step, developers can ensure that any new page integrates seamlessly into the VentaPOS `AppShell`, maintains a highly performant and accessible UI, and perfectly aligns with the required aesthetic and business logic.

---

## 1. Core Architecture: AppShell & Navbar

Every page in VentaPOS NextGen is automatically wrapped by the global `<AppShell />` component. 

### The Global Layout
- **RTL Enforcement:** The outermost `.page` wrapper sets `dir="rtl"`. All layouts naturally flow from right to left.
- **The Navbar:** The `<Navbar />` component is injected globally. It uses Bootstrap's `sticky-top` class with a `z-index` of 1030, meaning it remains fixed at the absolute top of the browser viewport during scrolling.
- **The Content Area:** Below the Navbar, `AppShell` uses a flexbox layout (`.page-wrapper`, `.page-body`, and `.container-fluid`) that expands naturally (`flex-grow-1`). 
- **Important Constraint Rule:** The `AppShell` specifically avoids using `overflow: hidden` or fixed viewport heights (e.g., `h-100`). This ensures the page expands natively and uses the browser's main window scrollbar.

---

## 2. Design Tokens & Localization

VentaPOS is tailored for the Egyptian retail and distribution market. You must adhere strictly to these visual and linguistic rules defined in `06_ui_design_tokens.md`.

### Typography
- **Primary Text:** `'Cairo', sans-serif` (Used for all labels, headings, and descriptions).
- **Monospace:** `'Courier New', monospace` (Used exclusively for barcodes and system logs).
- **Numerals:** Always use standard Western Arabic numerals (`1, 2, 3...`) for all quantities and financial figures, avoiding Eastern Arabic numerals (`١, ٢, ٣...`). Monetary values should be rounded to the nearest whole integer (EGP).

### Color Palette
- **`brand-primary` (`#0f52ba`):** (أزرق الدفتر) Primary actions, brand consistency.
- **`brand-secondary` (`#20c997`):** (أخضر المبيعات) Secondary additions, active interactions.
- **`state-success` (`#28a745`):** (النقدية المتاحة) Positive states, synced items, safe increases.
- **`state-warning` (`#ffc107`):** (مراجعة وتنبيه) Pending actions, warnings.
- **`state-danger` (`#dc3545`):** (العجز والإنذار) Errors, canceled invoices, backlogs.

### Egyptian Market Glossary
You must use the following professional yet accessible Egyptian business terms (لغة سوق مهنية ومبسطة) across the entire UI. Do not use formal corporate Arabic or extreme street slang.

| Standard Term | VentaPOS UI Term | Context |
| :--- | :--- | :--- |
| Customer / Client | **العميل** | Dropdowns, balance sheets, ledgers. |
| Product / Item | **البضاعة** | Product lists, stock panels. |
| Cash Drawer / Safe | **الخزنة** | Cash balances, safe setups. |
| Receipt / Invoice | **الفاتورة** | Transactions, POS checkouts. |
| Ledger / Database | **الدفتر** | General accounts, client accounts. |
| Cash | **النقدية** | Transactions, down payments. |
| Salesperson / Cashier | **المندوب** | Employee assignments, logins. |
| Down Payment | **مقدم الفاتورة** | Initial deposits for credit sales. |

---

## 3. The Unified Table Scroll Architecture

VentaPOS uses a **Native Window Scroll** approach for all data tables. We do not use internal nested scrollbars (e.g. `overflow-y: auto` inside a fixed height `.card`). This creates a mobile-friendly, native-feeling scrolling experience where sticky elements stack underneath each other.

### Sticky Hierarchy
When a user scrolls down the page:
1. The **Navbar** (`z-index: 1030`) stays at `top: 0`.
2. The **Toolbar** (`.sticky-toolbar`, `z-index: 1020`) sticks immediately beneath the Navbar.
3. The **Table Header** (`.table-sticky-header th`, `z-index: 1010`) sticks immediately beneath the Toolbar.

---

## 4. Step-by-Step Guide: Building a New Page

Follow these exact steps when creating a new screen (e.g., a new "Inventory List" or "Sales Report" page).

### Step 1: The Page Wrapper
Ensure the root element of your component supports native window scrolling. Remove any `h-100`, `overflow-hidden`, or `flex-grow-1` classes that might trap the scroll inside a div.

```jsx
import React, from 'react';

export default function InventoryPage() {
  return (
    // 'native-page-scroll' ensures the div expands and doesn't clip content
    <div className="native-page-scroll">
      {/* Content goes here */}
    </div>
  );
}
```

### Step 2: Add the Sticky Toolbar
If your page has a filter bar, search input, or action buttons above the data table, apply the `.sticky-toolbar` class to its container (e.g., a `.card-header`).

```jsx
<div className="card">
  <div className="card-header sticky-toolbar">
    <h3 className="card-title">البضاعة المتاحة</h3>
    <div className="card-actions">
      <button className="btn btn-primary">إضافة بضاعة</button>
    </div>
  </div>
  {/* Table goes here */}
</div>
```

### Step 3: Add the Data Table
For a standard table, add the `.table-sticky-header` class directly to the `<table>` element. 
> [!WARNING]
> Do NOT wrap `.table-sticky-header` inside a `.table-responsive` div. The default `overflow-x: auto` on Bootstrap's responsive wrapper breaks window-level `position: sticky`.

```jsx
<table className="table table-sticky-header">
  <thead>
    <tr>
      <th>م</th>
      <th>البضاعة</th>
      <th>الكمية</th>
      <th>السعر</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td>شاشة سامسونج</td>
      <td>10</td>
      <td>5000</td>
    </tr>
    {/* Map data here */}
  </tbody>
</table>
```

### Step 4: Infinite Scrolling (Intersection Observer)
Since the window handles the scrolling, you cannot attach an `onScroll` event to a local `div`. Instead, use the `IntersectionObserver` API. Attach a `ref` to the **very last `<tr>`** in your list. When that row becomes visible on the screen, trigger your `loadMore()` API call.

```jsx
{data.map((item, index) => {
  if (data.length === index + 1) {
    // Attach observer to the last row
    return (
      <tr ref={lastRowElementRef} key={item.id}>
        <td>{item.id}</td>
        <td>{item.name}</td>
      </tr>
    );
  }
  return (
    <tr key={item.id}>
      <td>{item.id}</td>
      <td>{item.name}</td>
    </tr>
  );
})}
```

### Step 5: Advanced Hybrid Scroll (For Wide Tables Only)
If your table has many columns and absolutely requires horizontal scrolling, use the **Hybrid Scroll Merging Architecture**:
1. Wrap the table in a container with a dynamic `maxHeight` (e.g. `calc(100vh - 110px)`).
2. Set `overflow-x: auto` and `overflow-y: auto`.
3. Add the `.hide-vertical-scroll` CSS class to make the internal vertical scrollbar invisible (tricking the user into seeing only the window scrollbar).
4. Implement the `useCallback` mouse wheel interceptor to ensure downward wheel scrolls bubble up to the `window` while the sticky thresholds apply. (See `TABLE_UX_GUIDELINES.md` for the exact Javascript snippet).
