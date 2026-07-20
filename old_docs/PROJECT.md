# VentaPOS NextGen Rebuild - Project Scope & Milestones

## Architecture
The VentaPOS NextGen Rebuild transition replaces the legacy Waitress/Python-Webview/SQLite desktop container with a modern, multi-tenant web application.
- **Backend:** Django (Python 3.11+) with Django REST Framework (DRF), utilizing a unified PostgreSQL database (replacing the dual-database SQLite architecture).
- **Frontend:** React (RTL-first, Tailwind CSS/Bootstrap) delivering a responsive web interface.
- **Database:** Standard PostgreSQL database for centralized tenant storage with clean logical separation, soft delete protection, and sync transaction control.
- **Synchronization:** Standardized JSON endpoints for synchronization between the central backend server and local mobile/viewer clients.

---

## Milestones

| # | Name | Scope | Dependencies | Status | Conv ID |
|---|------|-------|--------------|--------|---------|
| 1 | Database Schema & Migration Foundation | DDL schema design mapping SQLite tables; creation of python migration script (`migrate_legacy_data.py`) with zero data loss. | None | Pending | TBD |
| 2 | Backend REST APIs & Licensing Engine | Django REST APIs, 80-bit license validator, database row signature tamper checks, and sync normalization endpoints. | Milestone 1 | Pending | TBD |
| 3 | E2E Testing Suite (Dual Track) | Categories, BVA, and pairwise combinations test harness mapping Tiers 1-4. Compiles `TEST_READY.md`. | Milestone 2 | Pending | TBD |
| 4 | React UI Overhaul (Arabic RTL) | RTL-first React components, Login, Wizard, Dashboard, Receipts with 25th billing rule, Suppliers, Expenses, and License activation. | Milestone 2, Milestone 3 | Pending | TBD |
| 5 | Integration, Hardening & Forensic Audit | Final E2E test runs, white-box adversarial testing, and Forensic Auditor verification. | Milestone 4 | Pending | TBD |

---

## Code Layout

Below is the code mapping of files and folders under `d:\Projects\VentaPOS\VentaPOS_NextGen\`:

```
d:\Projects\VentaPOS\VentaPOS_NextGen/
├── backend/                              # Django Backend Application
│   ├── api/                              # REST API Application
│   │   ├── migrations/                   # Database migrations
│   │   ├── utils/                        # Security & validator utility modules
│   │   │   ├── __init__.py
│   │   │   ├── license_validator.py      # 80-bit Cryptographic key validation
│   │   │   └── security_utils.py         # Row-level HMAC-SHA256 signature checks
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── db_router.py                  # Database routing policies
│   │   ├── middleware.py                 # Tampering protection & subscription middleware
│   │   ├── models.py                     # Centralized PostgreSQL Django models
│   │   ├── serializers.py                # DRF Serializers with key normalization
│   │   ├── tests.py                      # Backend API unit tests
│   │   ├── urls.py                       # REST API routing
│   │   └── views.py                      # REST Views (Sync Ingestion, Auth, etc.)
│   ├── backend/                          # Django Settings & Core
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py                   # Django settings
│   │   ├── urls.py                       # Root URL routing
│   │   └── wsgi.py
│   └── manage.py                         # Django management CLI
└── frontend/                             # React Frontend Application
    ├── public/                           # Static assets
    ├── src/                              # Source code
    │   ├── assets/                       # Images, icons, and theme assets
    │   ├── components/                   # Reusable React components (Arabic RTL)
    │   │   ├── ActivationModal.jsx       # License activation dialog
    │   │   └── CommissionModal.jsx       # Salesperson commission update dialog
    │   ├── pages/                        # Screen layouts
    │   │   ├── Dashboard.jsx             # KPI view & pending sync queue
    │   │   ├── Inventory.jsx             # Catalog view & adjustment dialogs
    │   │   ├── Login.jsx                 # User login interface
    │   │   ├── POS.jsx                   # Sales screen layout
    │   │   ├── PosEntry.jsx              # Checkout and invoice entry
    │   │   ├── ProductLedger.jsx         # Time-machine inventory ledger view
    │   │   ├── Purchases.jsx             # Supplier purchase & returns invoicing
    │   │   └── Settings.jsx              # Setup and preferences configuration
    │   ├── App.css
    │   ├── App.jsx                       # Main React App routing & structure
    │   ├── api.js                        # Axios API client setup
    │   ├── index.css
    │   └── main.jsx                      # App entry point
    ├── index.html                        # Root HTML document
    ├── package.json                      # NPM dependencies & scripts
    └── vite.config.js                    # Vite build configuration
```

---

## Interface Contracts

### 1. Synchronization Endpoint (`/api/v1/sync/push/`)
Accepts synchronization payloads from viewer and mobile clients. To resolve legacy serialization key mismatches and prevent data loss, the payload format is strictly normalized.

#### Protocol Standards:
- **Key Names**: Serializations must use the key `"installments"` (not `"payments"` or `"installment_payments"`) for installment payment schedules.
- **Due Date Key**: Each payment schedule item in the `"installments"` array must use `"payment_date"` (not `"date"` or `"due_date"`).
- **Collision Prevention**: The unique identifier for receipts across the swarm is the cryptographic `receipt_hash` (not the local sequence combination `(source_machine_id, local_id)`).

#### Request Example (`POST /api/v1/sync/push/`):
```json
{
  "receipt_hash": "a4f89d09c6238b1f2095f87b8d009211c47dfd6e3c3b03698a96d13a6df91278",
  "customer_name": "العميل التجريبي",
  "total_amount": 3000,
  "down_payment": 1000,
  "installment_system": "1000 * 2",
  "is_cash_sale": false,
  "installments": [
    {
      "payment_date": "2026-07-25",
      "amount": 1000
    },
    {
      "payment_date": "2026-08-25",
      "amount": 1000
    }
  ]
}
```

#### Response Example (`201 Created`):
```json
{
  "status": "success",
  "receipt_hash": "a4f89d09c6238b1f2095f87b8d009211c47dfd6e3c3b03698a96d13a6df91278",
  "synced_at": "2026-06-28T13:16:29Z"
}
```

### 2. Mobile Sync Field Translation Layer
The synchronization system translates differences between the backend Django model schema and the local offline SQLite database schemas. 

#### Product Schema Mappings:
| Django Backend Field | Local SQLite Field | Description |
|---|---|---|
| `local_id` | `id` | Product unique identifier locally |
| `quantity` | `initial_quantity` | Initial opening stock balance |
| `purchase_price` | `initial_purchase_price` | Retroactive purchase unit cost |
| `salesperson_commission_amount` | `initial_commission_amount` | Retroactive base commission |

#### Receipt Schema Mappings:
| Django Backend Field | Local SQLite Field | Description |
|---|---|---|
| `local_id` | `id` | Sequential receipt number locally |
| `local_branch_id` | `branch_id` | Branch key |
| `local_salesperson_id` | `salesperson_id` | Associated salesperson key |
| `created_at_local` | `created_at` | Client-side creation timestamp |

---

## Retrospective Algorithms & Rules

### 1. Retrospective Stock Formula (`get_stock_at_date(month, year)`)
Calculates the quantity of stock for an item at any arbitrary month and year:
$$\text{final\_stock} = (\text{initial\_quantity} + \text{total\_purchased} + \text{total\_surplus}) - (\text{total\_sold} + \text{total\_returned} + \text{total\_deficit})$$

### 2. Credit Installment Due Date Rule (25th Billing Rule)
For credit installment sales, payment schedules are generated automatically on the **25th of each month** starting with the month following the sale.
$$\text{due\_date} = \text{date}(\text{sale\_year}, \text{sale\_month}, 25) + \text{relativedelta}(\text{months} = i + 1)$$
Manual alteration of payment dates is prohibited by UI constraints and API validation.
