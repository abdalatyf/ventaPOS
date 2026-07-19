# VentaPOS NextGen — Master Documentation Hub

Welcome to the VentaPOS NextGen documentation. This index is the single entry point for all project documentation.

> [!IMPORTANT]
> VentaPOS NextGen is an **offline-first, single-tenant desktop POS** application.
> Database: **SQLite + WAL mode** · Auth: **Single admin + DRF TokenAuthentication** · Desktop: **PyWebView**

---

## Directory Map

```
docs/
├── index.md                          ← This file (master hub)
├── business/
│   ├── product.md                    ← Product vision & target audience
│   ├── product-guidelines.md         ← Arabic RTL & UI tone rules
│   ├── tech-stack.md                 ← Tech stack (SQLite, Django, React, PyWebView)
│   └── workflow.md                   ← Dev workflow & CDD rules
├── architecture/
│   ├── 01_overview.md                ← Project overview & confirmed decisions
│   ├── 02_data_models.md             ← SSoT: all Django models & schema
│   ├── 03_api_contract.md            ← Unified API reference
│   ├── 04_ui_design_tokens.md        ← UI design system (colors, tokens, components)
│   ├── 05_licensing.md               ← 80-bit crypto licensing spec
│   └── 06_frontend_architecture.md   ← React component structure & routing
├── features/
│   ├── inventory_management.md       ← Inventory ledger & time-machine mechanics
│   ├── pos_and_receipts.md           ← POS screen flow, receipt generation & printing
│   ├── procurement.md                ← Purchase entry & supplier ledger
│   ├── reports.md                    ← All 8 system reports
│   ├── tools.md                      ← Sync, backup & smart import tools
│   ├── expenses_and_branches.md      ← Expense tracking & branch context
│   ├── settings_and_security.md      ← Security, password, & system settings
│   └── system_init.md                ← First-time setup wizard
├── technical/
│   └── parity_tests_doc.md           ← E2E parity testing strategy
└── _archive/                         ← Preserved out-of-scope & superseded docs
    ├── 00_master_index.md            ← (Superseded by this index)
    ├── 01_executive_summary.md       ← (Superseded by product.md)
    ├── 02_architecture_overview.md   ← (Multi-agent design — superseded)
    ├── 03_core_components.md         ← (Requirements spec — superseded)
    ├── 04_data_models.md             ← (Old schema — see 02_data_models.md when created)
    ├── 05_integration_points_and_apis.md ← (Old API spec — see 03_api_contract.md when created)
    ├── 07_mobile_architecture.md     ← (Mobile — DEFERRED)
    ├── 08_mobile_screens_plan.md     ← (Mobile — DEFERRED)
    ├── api_contract.md               ← (Old API contract draft)
    ├── backend_micro_features.md     ← (Merged into feature docs)
    ├── backend_models_doc.md         ← (Old models doc — see 02_data_models.md when created)
    ├── database_schema.md            ← (Old DDL — superseded)
    └── tracks.md                     ← (Old tracking — superseded)
```

---

## 1. Business & Product Rules (`/business`)

*Core rules about how the POS should function and look.*

| Document | Description |
| :--- | :--- |
| [product.md](./business/product.md) | Product vision, target audience, and business context |
| [product-guidelines.md](./business/product-guidelines.md) | Arabic UI layout, RTL design, and Egyptian-market localization rules |
| [tech-stack.md](./business/tech-stack.md) | Tech stack choices: SQLite, Django 5.x, React 19, PyWebView |
| [workflow.md](./business/workflow.md) | CDD workflow rules, GitHub sync, and code quality gates |

---

## 2. Architecture (`/architecture`)

*Active technical blueprints and design systems.*

| Document | Description |
| :--- | :--- |
| [04_ui_design_tokens.md](./architecture/04_ui_design_tokens.md) | UI design tokens, color palettes, glassmorphism, and declarative components |
| [06_frontend_architecture.md](./architecture/06_frontend_architecture.md) | React component structure, routing, and frontend developer guide |

> [!NOTE]
> Architecture docs `01_overview.md`, `02_data_models.md`, `03_api_contract.md`, and `05_licensing.md` are **planned but not yet created**. The old versions are preserved in `_archive/` for reference.

---

## 3. Feature Documentation (`/features`)

*Detailed documentation for each functional area of the system.*

| Document | Description |
| :--- | :--- |
| [inventory_management.md](./features/inventory_management.md) | Inventory management logic and time-machine ledger mechanics |
| [pos_and_receipts.md](./features/pos_and_receipts.md) | POS screen flow, receipt generation, and silent print via SumatraPDF |
| [procurement.md](./features/procurement.md) | Purchase entry, supplier ledger, and procurement flow |
| [reports.md](./features/reports.md) | All 8 system reports: Dashboard, Cash Drawer, Expenses, Installments, Inventory Movement, P&L, Receipts, Salesperson Performance |
| [tools.md](./features/tools.md) | Sync tool (offline USB + future online), Backup (download/restore), Smart Import |
| [expenses_and_branches.md](./features/expenses_and_branches.md) | Expense tracking and branch-specific POS context |
| [settings_and_security.md](./features/settings_and_security.md) | Single-admin authentication, password management, and system settings |
| [system_init.md](./features/system_init.md) | First-time setup wizard: license validation, admin creation, branch provisioning |

---

## 4. Technical Specs (`/technical`)

| Document | Description |
| :--- | :--- |
| [parity_tests_doc.md](./technical/parity_tests_doc.md) | Strategy and details for system parity testing |

---

## 5. Deferred / Out of Scope

The following items are **not current features** and their docs are preserved in `_archive/`:

| Item | Status | Archive Location |
| :--- | :--- | :--- |
| Mobile App (Flutter) | **Deferred** | `_archive/07_mobile_architecture.md`, `_archive/08_mobile_screens_plan.md` |
| Cloud Sync Server | **Deferred** | — |
| Multi-user Roles | **Not planned** — single admin only | — |
| Legacy Data Migration | **Not needed** | — |
| ActionLog model | **Removed** from system | — |
| Tenant model | **Removed** — single-tenant | — |
| CloudUser model | **Removed** | — |

---

## 6. Missing Documentation (TODO)

*The following features exist in the codebase but do not yet have dedicated documentation.*

### Architecture Docs (Planned)

- [ ] `architecture/01_overview.md` — Project overview & confirmed architectural decisions
- [ ] `architecture/02_data_models.md` — SSoT: all Django models & schema (SQLite, AutoField PKs, soft-delete)
- [ ] `architecture/03_api_contract.md` — Unified OpenAPI 3.1 API reference
- [ ] `architecture/05_licensing.md` — 80-bit crypto licensing specification

### Frontend Components & Pages

- **CashDrawerReport** (`pages/reports/CashDrawerReport.jsx`) — Cash drawer transactions and daily summaries
- **DashboardReport** (`pages/reports/DashboardReport.jsx`) — KPI and sales summary dashboard
- **DemoBanner** (`components/DemoBanner.jsx`) — Demo mode visual indicator
- **ExpensesReport** (`pages/reports/ExpensesReport.jsx`) — Branch expenses by type
- **InstallmentsReport** (`pages/reports/InstallmentsReport.jsx`) — Installment payment tracking
- **InventoryMovementReport** (`pages/reports/InventoryMovementReport.jsx`) — Stock movements ledger
- **ProfitAndLossReport** (`pages/reports/ProfitAndLossReport.jsx`) — Financial P&L report
- **ReceiptsReport** (`pages/reports/ReceiptsReport.jsx`) — Historical receipt list and analytics
- **ReportsIndex** (`pages/reports/ReportsIndex.jsx`) — Reports navigation index
- **ReportsLayout** (`pages/reports/ReportsLayout.jsx`) — Reports layout shell
- **SalespersonPerformanceReport** (`pages/reports/SalespersonPerformanceReport.jsx`) — Commission and performance tracking
- **SettingsIndex** (`pages/settings/SettingsIndex.jsx`) — Settings navigation index
- **ToolsDashboard** (`pages/tools/ToolsDashboard.jsx`) — Tools navigation dashboard

### Frontend Routes

- `/login` — Authentication route
- `/select-branch` — Branch selection for cashier terminal
- `product-ledger/:id` — Time-machine ledger for a specific product
- `purchases/edit/:id` — Purchase invoice editing
- `purchases/new` — New purchase entry
- `search-purchases` — Procurement search and filter
- `tools/*` — Tools dashboard subroutes

### Backend Endpoints & Custom Actions

- `tools/sync/approve-pending/<int:pk>/` → `ApprovePendingReceiptView`
- `/api/v1/inventory-items/get_safe_available_qty/` → `get_safe_available_qty`
- `/api/v1/inventory-items/pos_search/` → `pos_search`
- `/api/v1/receipts/printers/` → `printers`
