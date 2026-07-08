# VentaPOS UI Design Tokens (A2UI)

This document serves as the Single Source of Truth for the VentaPOS NextGen visual design and component styling. All frontend agents MUST adhere to these tokens to ensure a consistent, premium, and dynamic user experience.

## Core Principles
1. **RTL First:** The application is entirely Right-to-Left (Arabic).
2. **Tabler UI Foundation:** Built on top of the Tabler Dashboard UI Kit (Bootstrap 5).
3. **Typography:** `Cairo` is the exclusive font family for all text to ensure optimal Arabic legibility.

---

## 1. Color Palette

### Brand Colors
- **Primary / Brand:** `#0f52ba` (Sapphire Blue) - Used for primary actions, active states, and emphasis.
- **Background:** `#f4f6f8` - Default application background.

### Semantic Colors (Tabler Defaults)
- **Success:** `#2fb344` - Paid status, cash payments, positive indicators.
- **Warning:** `#f76707` - Installments, pending actions, alerts.
- **Danger:** `#d63939` - Deletions, unpaid status, critical errors.
- **Info:** `#4299e1` - Tooltips, informational text.
- **Muted/Secondary:** `#656d77` - Secondary text, borders, disabled states.

---

## 2. Typography (Cairo)

Imported via Google Fonts: `family=Cairo:wght@400;500;600;700;800&display=swap`

- **Headings (h1 - h6):** `Cairo`, Font-Weight: `700` (Bold) or `800` (Extra Bold).
- **Body Text:** `Cairo`, Font-Weight: `500` (Medium) or `600` (SemiBold) for standard legibility.
- **Numbers/Currencies:** Always use `fw-bolder` (700/800) and ensure proper formatting (e.g., `toArabic(formatCurrency(value))`).

---

## 3. Spacing & Layout Constraints

- **Containers:** Use `container-xl` or fluid containers for dashboard views.
- **Cards:** 
  - Standard Tabler cards (`card`) with `shadow-sm`.
  - Headers (`card-header`) should have a light background (`bg-light`) and a subtle bottom border.
- **Tables:**
  - Standard structure: `table table-bordered table-vcenter table-hover`.
  - Header: `thead` should generally use `bg-light` or `table-dark` depending on the context.
  - Sticky Headers: Use the custom `.report-table-container` class for tables requiring internal scrolling.

---

## 4. Micro-Animations & Interactions

To ensure a "Dynamic Design" that feels alive:
- **Hover Effects:** Interactive elements (table rows, buttons, dropdowns) must have distinct hover states (e.g., `table-hover` for rows).
- **Buttons:** Use standard Tabler/Bootstrap transitions. Add icons to buttons using `@tabler/icons-react` to make actions visually clear.
- **Modals:** Use `modal-dialog-centered` and `modal-dialog-scrollable` with an overlay backdrop (`bg-dark bg-opacity-50`).

---

## 5. A2UI Declarative Guidelines for Agents
When creating new views, agents must use the following declarative mapping:
- *Icons:* `@tabler/icons-react` (size: 18px to 24px depending on context).
- *Grids:* Bootstrap grid system (`row g-2`, `col-md-6`, etc.).
- *Borders:* Use `border-secondary-subtle` for subtle outlines on cards and tables instead of stark black or dark grey borders.
