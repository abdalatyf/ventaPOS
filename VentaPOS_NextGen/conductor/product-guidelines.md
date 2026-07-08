# Product Guidelines: VentaPOS NextGen

## 1. Terminology & Tone
- **Language:** The entire application MUST be in Arabic and Right-to-Left (RTL).
- **Tone:** "لغة سوق مهنية ومبسطة" (Professional but easy Egyptian Arabic).
- **Style Rules:** 
  - Avoid overly strict corporate Arabic.
  - DO NOT use excessive street slang (like 'يا معلم').
  - Use clear terms like (العميل, البضاعة, الخزنة, الفاتورة, الدفتر, النقدية).

## 2. A2UI Design Tokens

### Core Principles
1. **RTL First:** The application is entirely Right-to-Left (Arabic).
2. **Tabler UI Foundation:** Built on top of the Tabler Dashboard UI Kit (Bootstrap 5).
3. **Typography:** `Cairo` is the exclusive font family for all text to ensure optimal Arabic legibility.

### Color Palette
- **Primary / Brand:** `#0f52ba` (Sapphire Blue) - Used for primary actions, active states, and emphasis.
- **Background:** `#f4f6f8` - Default application background.
- **Success:** `#2fb344` - Paid status, cash payments, positive indicators.
- **Warning:** `#f76707` - Installments, pending actions, alerts.
- **Danger:** `#d63939` - Deletions, unpaid status, critical errors.
- **Info:** `#4299e1` - Tooltips, informational text.
- **Muted/Secondary:** `#656d77` - Secondary text, borders, disabled states.

### Typography (Cairo)
- **Headings (h1 - h6):** `Cairo`, Font-Weight: `700` (Bold) or `800` (Extra Bold).
- **Body Text:** `Cairo`, Font-Weight: `500` (Medium) or `600` (SemiBold) for standard legibility.
- **Numbers/Currencies:** Always use `fw-bolder` (700/800) and ensure proper formatting (e.g., `toArabic(formatCurrency(value))`).

### Spacing & Layout Constraints
- **Containers:** Use `container-xl` or fluid containers for dashboard views.
- **Cards:** Standard Tabler cards (`card`) with `shadow-sm`. Headers (`card-header`) should have a light background (`bg-light`) and a subtle bottom border.
- **Tables:** Standard structure: `table table-bordered table-vcenter table-hover`.

### Micro-Animations & Interactions
- **Hover Effects:** Interactive elements (table rows, buttons, dropdowns) must have distinct hover states.
- **Buttons:** Use standard Tabler/Bootstrap transitions. Add icons to buttons using `@tabler/icons-react`.
- **Borders:** Use `border-secondary-subtle` for subtle outlines on cards and tables.
