# VentaPOS NextGen — Rejected Approaches (Negative Knowledge Base)

This document serves as the project's **Anti-Hallucination Guardrail**. It catalogs all design decisions, features, and architectural approaches that have been explicitly considered and **REJECTED**.

If any agent suggests, plans, or implements anything on this list, it is a critical failure. Reject the code immediately.

---

## 1. Architectural & Database Rejections

| Rejected Approach | Rationale (Why it was rejected) | Corresponding Rule |
|---|---|---|
| **Multi-Tenancy / SaaS Model** | The app is strictly for a single manager on a single machine. Multi-tenant `Tenant` tables bloat queries and add unneeded complexity. | `AGENTS.md §2.1` |
| **Cloud Synchronization** | Strictly an Offline-First Desktop App. Relying on cloud sync introduces edge cases for offline states that are out of scope. | `AGENTS.md §2.1` |
| **UUIDs for Primary Keys** | Django's default auto-incrementing integers (`BigAutoField`) are perfectly sufficient for a single-machine SQLite DB. UUIDs waste space and make debugging harder. | `AGENTS.md §2.3` |
| **Hard Deletes (`.delete()`)** | Business accounting requires auditability. If an entity is deleted, it must be hidden via `is_deleted=True` using soft deletes and an `ActiveManager`. | `AGENTS.md §2.2` |
| **Action / System Logs Table** | Since there is only one user (the manager), tracking "who did what" via an `ActionLog` model is useless overhead. | `AGENTS.md §2.9` |

## 2. Business Logic Rejections

| Rejected Approach | Rationale (Why it was rejected) | Corresponding Rule |
|---|---|---|
| **Explicit Customer Model** | No CRM features needed. Customers are just text strings on receipts (`customer_name`, `phone`). The UI provides autocomplete based on historical receipts. | `AGENTS.md §2.6` |
| **Selling Price on Product Model** | Prices constantly fluctuate. Storing a fixed `selling_price` on `InventoryItem` is useless. The manager types the agreed price per unit directly into the receipt at the time of sale. | `AGENTS.md §2.7` |
| **Base Salary for Salespeople** | Salespeople (مناديب) work strictly on commission. Their payout is calculated dynamically: `(مندبة × units sold) + (collection_rate × monthly collections)`. | `requirements.md §4.7` |
| **Payment Tracking (Installments)** | The system only generates and prints the schedule (the planned dates). It does **not** track whether the customer actually paid the installment. | `requirements.md §4.3` |
| **Inter-Branch Transfers** | Each branch/warehouse operates with independent, isolated inventory. Stock does not move between branches within this system. | `AGENTS.md §0` |
| **Daily Dates (`DateFields`)** | Accounting operates entirely on a monthly basis. The system relies on `month` and `year` integer fields, bypassing complex timezone and day-of-month logic. | `AGENTS.md §3` |

## 3. Scope & Feature Rejections

| Rejected Approach | Rationale (Why it was rejected) | Corresponding Rule |
|---|---|---|
| **Smart Import (Excel)** | Too fragile and high-maintenance. Users must enter opening balances manually. | `AGENTS.md §2.8` |
| **Barcode / SKU Support** | The business relies strictly on localized text-based names for products (e.g., "طقم كاسات مدهب"). Search is text-only. | `AGENTS.md §0` |
| **Card / Visa Payments** | Customers pay entirely in Cash (نقدي) or via physical Installments (تقسيط). | `AGENTS.md §3` |
| **Split Payments** | A receipt cannot be paid half-cash, half-installment. One receipt = one payment type. | `AGENTS.md §3` |
| **Expense Categories (Enums)** | Adding expense category models creates unnecessary setup. Expenses just use a free-text `description` field. | `AGENTS.md §2.10` |

## 4. UI/UX Rejections

| Rejected Approach | Rationale (Why it was rejected) | Corresponding Rule |
|---|---|---|
| **Tailwind CSS** | The codebase is heavily invested in Tabler and Bootstrap v5 utilities. Mixing in Tailwind creates styling conflicts and fragmented UI paradigms. | `UI_UX_RULES.md §2` |
| **Standard `<select>` Dropdowns** | Standard `<select>` elements cannot handle thousands of options cleanly. Must use the unified React `<Autocomplete>` / `<ReportAutocomplete>` component with debounce. | `UI_UX_RULES.md §6.1` |
| **Native `<input type="date">`** | Because the app uses a strict Month/Year integer system, native date pickers confuse the user. Use two side-by-side inputs for `MM` and `YYYY`. | `UI_UX_RULES.md §6.2` |
| **Leading Zeros in Dates** | The display format for dates (e.g. `8/2026`) must omit leading zeros. Do not pad the month to `08`. | `UI_UX_RULES.md §6.2` |

---

> **Note for AI Orchestrators:** When reviewing PRs or diffs, search the proposed plan against these keywords (`Tenant`, `UUID`, `delete()`, `Customer`, `selling_price`, `Tailwind`). If any exist, you must **Challenge** the action (`AGENTS.md §13`).
