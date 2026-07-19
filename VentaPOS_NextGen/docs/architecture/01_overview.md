# Chapter 1: Architecture Overview

# VentaPOS NextGen — Project Scope & Architecture

> **Status:** Living document · Last updated: 2026-07-19

---

## 1. Project Scope

VentaPOS NextGen is an **offline-first desktop POS application** purpose-built for the **Egyptian retail and wholesale market**. The entire stack — Django backend, React frontend, and SQLite database — runs locally on the cashier's machine, wrapped inside a PyWebView desktop window.

### Design Principles

| Principle | Implementation |
|---|---|
| Offline-first | No internet required; all data is local SQLite |
| Single-tenant | One company per installation; no tenant isolation needed |
| Single-admin | One admin password; no multi-user roles |
| Arabic RTL | All UI uses professional Egyptian market Arabic (لغة سوق مهنية ومبسطة) |
| Local printing | `os.startfile()` / SumatraPDF for silent print (no browser print dialogs) |
| Soft delete | `is_deleted` flag on all models with `ActiveManager` filtering |

---

## 2. Architecture Stack

```
┌─────────────────────────────────────┐
│           PyWebView Window          │  ← Desktop wrapper (Windows)
│  ┌───────────────────────────────┐  │
│  │     React Frontend (Vite)     │  │  ← RTL Bootstrap / Axios
│  │     http://localhost:5173     │  │
│  └──────────────┬────────────────┘  │
│                 │ REST API          │
│  ┌──────────────▼────────────────┐  │
│  │    Django Backend (DRF)       │  │  ← Token auth, business logic
│  │    http://localhost:8000      │  │
│  └──────────────┬────────────────┘  │
│                 │                   │
│  ┌──────────────▼────────────────┐  │
│  │   SQLite + WAL mode           │  │  ← Single file, local disk
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

---

## 3. Confirmed Architecture Decisions

These decisions were finalized during the requirements interview and are **non-negotiable** across all agents and milestones.

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Database | SQLite + WAL mode | Offline-first, single-user, no server needed |
| 2 | Primary Keys | `AutoField` / `BigAutoField` | Simple integers, no UUID overhead |
| 3 | Multi-tenancy | Single-tenant (no tenant FK) | One installation = one company |
| 4 | Authentication | Single admin password + DRF `TokenAuthentication` | No multi-user roles needed |
| 5 | Desktop wrapper | PyWebView | Lightweight, no Electron bloat |
| 6 | Quantities | Integer only | No fractional units in this market |
| 7 | Customers | Implicit (text fields on receipts) | No `Customer` model; name/phone/address on receipt |
| 8 | Selling price | Cashier enters per sale | No fixed price on product model |
| 9 | Products | Branch-scoped | Same product name can exist in different branches |
| 10 | Date system | Monthly-based (`month`/`year` fields) | Not daily; matches Egyptian accounting cycles |
| 11 | Printing | `os.startfile()` / SumatraPDF | Silent local print, no browser dialogs |
| 12 | Soft delete | `is_deleted` on all models + `ActiveManager` | Safe deletion, audit trail |
| 13 | Sales commission (مندبة) | Fixed value per product | Stored in `InventoryItem.salesperson_commission_amount` |
| 14 | Collection commission (عمولة تحصيل) | Percentage per branch | Stored in `Branch.collection_commission_percentage` |
| 15 | Salesperson salary | Commission-only | No base salary field |
| 16 | Installments | Schedule only (25th rule) | No collection tracking |
| 17 | Product identity | Name only | No barcode/SKU |
| 18 | Recovery code | License code from `client_license` table | Special license type for password recovery |

---

## 4. Code Layout

```
VentaPOS_NextGen/
├── backend/                              # Django Backend Application
│   ├── api/                              # REST API Application
│   │   ├── migrations/                   # Database migrations
│   │   ├── utils/                        # Security & validator utilities
│   │   │   ├── license_validator.py      # 80-bit license key validation
│   │   │   └── security_utils.py         # Row-level HMAC-SHA256 checks
│   │   ├── management/                   # Custom manage.py commands
│   │   ├── templates/                    # PDF/receipt templates
│   │   ├── tests/                        # Backend test suite
│   │   ├── models.py                     # SQLite Django models (all entities)
│   │   ├── serializers.py                # DRF Serializers
│   │   ├── views.py                      # REST Views (Auth, CRUD, Reports)
│   │   ├── tools_views.py                # Backup, sync, smart import views
│   │   ├── urls.py                       # REST API routing
│   │   ├── middleware.py                 # License enforcement middleware
│   │   ├── print_utils.py                # SumatraPDF silent print helpers
│   │   └── db_router.py                  # Database routing policies
│   ├── backend/                          # Django Settings & Core
│   │   ├── settings.py                   # Django settings (SQLite config)
│   │   ├── urls.py                       # Root URL routing
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── db/                               # SQLite database files
│   └── manage.py                         # Django management CLI
├── frontend/                             # React Frontend Application
│   ├── public/                           # Static assets
│   ├── src/                              # Source code
│   │   ├── assets/                       # Images, icons, theme assets
│   │   ├── components/                   # Reusable React components
│   │   │   ├── ActivationModal.jsx       # License activation dialog
│   │   │   ├── CommissionModal.jsx       # Salesperson commission update
│   │   │   ├── Navbar.jsx                # Main navigation bar
│   │   │   ├── DemoBanner.jsx            # Demo mode indicator
│   │   │   ├── BranchesTab.jsx           # Branch management tab
│   │   │   ├── SalespersonsTab.jsx       # Salesperson management tab
│   │   │   ├── SuppliersTab.jsx          # Supplier management tab
│   │   │   └── InventoryTab.jsx          # Inventory management tab
│   │   ├── pages/                        # Screen layouts
│   │   │   ├── Login.jsx                 # Admin password login
│   │   │   ├── SystemInit.jsx            # First-run setup wizard
│   │   │   ├── Dashboard.jsx             # KPI summary view
│   │   │   ├── BranchSelection.jsx       # Branch picker
│   │   │   ├── Inventory.jsx             # Catalog & adjustments
│   │   │   ├── POS.jsx                   # Sales screen layout
│   │   │   ├── PosEntry.jsx              # Checkout & invoice entry
│   │   │   ├── ProductLedger.jsx         # Time-machine inventory ledger
│   │   │   ├── Expenses.jsx              # Operating expenses tracker
│   │   │   ├── PurchaseEntry.jsx         # Supplier purchase invoicing
│   │   │   ├── SearchReceipts.jsx        # Sales receipt search/filter
│   │   │   ├── SearchPurchases.jsx       # Purchase invoice search
│   │   │   ├── Setup.jsx                 # System preferences
│   │   │   ├── reports/                  # Report sub-pages
│   │   │   ├── settings/                 # Settings sub-pages
│   │   │   └── tools/                    # Backup/sync/import tools
│   │   ├── hooks/                        # Custom React hooks
│   │   ├── utils/                        # Frontend utility functions
│   │   ├── App.jsx                       # Main React App routing
│   │   ├── api.js                        # Axios API client setup
│   │   └── main.jsx                      # App entry point
│   ├── index.html                        # Root HTML document
│   ├── package.json                      # NPM dependencies & scripts
│   └── vite.config.js                    # Vite build configuration
├── docs/                                 # Project documentation
├── e2e/                                  # End-to-end test scripts
└── main.py                              # PyWebView desktop launcher
```

---

## 5. Milestones

| Phase | Name | Scope | Status |
|-------|------|-------|--------|
| 0 | Documentation & Context | Architecture docs, data models doc, API contract, design tokens — establish the single source of truth | ✅ In Progress |
| 1 | Models & Schema | Finalize Django models, run migrations, verify SQLite schema matches docs | Pending |
| 2 | Backend Fixes | Fix all backend bugs: serializer mismatches, view logic errors, report calculations, license validation | Pending |
| 3 | Frontend Fixes | Fix all React bugs: broken pages, wrong API calls, missing error handling, RTL issues | Pending |
| 4 | Missing Pages | Build pages not yet implemented: remaining reports, tools pages, settings sub-pages | Pending |
| 5 | Demo & Init | Demo mode seeding, first-run wizard polish, sample data population | Pending |
| 6 | PyWebView Integration | Package as desktop app: `main.py` launcher, auto-start Django, window management | Pending |
| 7 | E2E Test Suite | Playwright + pytest end-to-end tests covering all critical business flows | Pending |

---

## 6. Key Algorithms

### 6.1 Retrospective Stock Formula

**Function:** `get_stock_at_date(product, month, year)`

Calculates the quantity of stock for a product at any arbitrary month/year point in time:

$$\text{final\_stock} = (\text{initial\_quantity} + \text{total\_purchased} + \text{total\_surplus}) - (\text{total\_sold} + \text{total\_returned} + \text{total\_deficit})$$

Where:
- `initial_quantity` = opening stock balance when product was first added
- `total_purchased` = sum of purchase invoice items up to (month, year)
- `total_surplus` = sum of positive inventory adjustments up to (month, year)
- `total_sold` = sum of sale items from receipts up to (month, year)
- `total_returned` = sum of purchase returns up to (month, year)
- `total_deficit` = sum of negative inventory adjustments up to (month, year)

All aggregations filter by `(item_month <= month AND item_year <= year)` using the monthly date system.

### 6.2 Credit Installment Due Date Rule (25th Billing Rule)

For credit installment sales, payment schedules are generated automatically on the **25th of each month**, starting with the month following the sale:

$$\text{due\_date} = \text{date}(\text{sale\_year}, \text{sale\_month}, 25) + \text{relativedelta}(\text{months} = i + 1)$$

Where `i` is the zero-based installment index.

**Constraints:**
- Manual alteration of payment dates is **prohibited** by both UI constraints and API validation
- The key name in payloads must be `"installments"` (not `"payments"` or `"installment_payments"`)
- Each installment uses the field `"payment_date"` (not `"date"` or `"due_date"`)

---

## 7. Sync Interface Contracts

> [!IMPORTANT]
> These contracts are **ready for future mobile integration** (Flutter app — currently deferred). They define the protocol for syncing data between a central server and local offline clients. The desktop app does not currently use cloud sync, but the contracts are preserved here for forward compatibility.

### 7.1 Sync Push Endpoint (`POST /api/sync/push/`)

Accepts synchronization payloads from viewer and mobile clients. The payload format is strictly normalized.

#### Protocol Standards

| Rule | Specification |
|------|---------------|
| Installment key | Must use `"installments"` (not `"payments"`) |
| Due date key | Must use `"payment_date"` (not `"date"` or `"due_date"`) |
| Collision prevention | Unique identifier = `receipt_hash` (not `source_machine_id + local_id`) |

#### Request Example

```json
{
  "receipt_hash": "a4f89d09c6238b1f20...91278",
  "customer_name": "العميل التجريبي",
  "total_amount": 3000,
  "down_payment": 1000,
  "installment_system": "1000 * 2",
  "is_cash_sale": false,
  "installments": [
    { "payment_date": "2026-07-25", "amount": 1000 },
    { "payment_date": "2026-08-25", "amount": 1000 }
  ]
}
```

#### Response Example (`201 Created`)

```json
{
  "status": "success",
  "receipt_hash": "a4f89d09c6238b1f20...91278",
  "synced_at": "2026-06-28T13:16:29Z"
}
```

### 7.2 Field Translation Layer (Future Mobile Sync)

When syncing between the Django backend and local offline SQLite databases, the system translates field names automatically.

#### Product Schema Mappings

| Django Backend Field | Local SQLite Field | Description |
|---|---|---|
| `id` | `id` | Auto-increment primary key |
| `quantity` | `initial_quantity` | Initial opening stock balance |
| `purchase_price` | `initial_purchase_price` | Purchase unit cost |
| `salesperson_commission_amount` | `initial_commission_amount` | Base commission amount |

#### Receipt Schema Mappings

| Django Backend Field | Local SQLite Field | Description |
|---|---|---|
| `id` | `id` | Auto-increment primary key |
| `branch_id` | `branch_id` | Branch foreign key |
| `salesperson_id` | `salesperson_id` | Salesperson foreign key |
| `customer_phone` | `phone_number` | Customer phone number |
| `customer_address` | `address` | Customer address |
| `customer_area` | `area` | Customer area/district |
