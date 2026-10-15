# Product: VentaPOS NextGen

## Vision & Description
VentaPOS NextGen is a modern Point-of-Sale (POS) and inventory management system designed specifically for the Egyptian market. It replaces a legacy VentaPOS system with a robust, modern stack while retaining essential business logic for sales, inventory, and licensing.

## Core Capabilities
- Inventory and Stock Management
- Cash and Installment Sales processing
- Customer and Supplier Ledgers
- Reporting and Dashboard Analytics
- Licensing and Tenant Isolation (ClientLicenses)
- Print/PDF generation for receipts using native OS integrations

## Offline-First Architecture
* **Rule:** The application is an offline-first desktop app. The backend (Django) and frontend (React) will both run locally on the cashier's machine.
* Because of this, it is expected and permitted for the backend to interact directly with the local OS, such as using `os.startfile` to open PDFs or calling local printer binaries (like SumatraPDF).

## Target Users
- Cashiers and Shop Owners operating in environments that require robust offline capabilities.
- Businesses relying heavily on localized terminology and right-to-left UI.

## Legacy System & Business Logic Rules
This NextGen version migrates data and concepts from an older legacy system (Reference: `migrate_legacy_data.py`). 

Through our `/grill-me` alignment, the following core business logic rules have been established as the Single Source of Truth:

1. **Taxes (VAT):** The system **does not** use taxes at all for this market. Tax is inherently included in the product's unit price, and no additional VAT calculations or schema fields should be added.
2. **Installments (التقسيط):** Installment plans are created by the cashier defining up to 3 "groups" or systems (e.g., 6 months × 100 EGP, plus 12 months × 50 EGP). The **Frontend** is responsible for computing the exact `payment_month`, `payment_year`, and `amount` for each individual `InstallmentPayment` row, starting the month *after* the sale. The backend simply receives these pre-computed rows in the payload and saves them.
3. **Licensing & Offline Mode:** The local desktop app enforces licenses locally. It checks `invoices_balance` and `expiry_date`. If the balance reaches 0 or the license expires, the system strictly **blocks the creation of new receipts**, but it gracefully allows the user to log in and view historical data and reports.
4. **Date Formats (التعامل الشهري):** All operations and logic revolve around monthly accounting. To enforce this, dates globally in the UI should be displayed exclusively as month and year `MM/YYYY` (e.g., `07/2026`). Exact days should be hidden from UI components unless explicitly needed.

5. **Profit and Loss Report (??????? ????????):** The report uses a unified table displaying Cash and Installment sales. Sales Commission (?????) and Collection Commission (????? ?????) are separated. The table default sorts by Item Number (\local_id\). Sorting dual-value columns defaults to sorting by the Total value.
6. **Tools Dashboard (الأدوات):** A unified tools dashboard provides Offline Sync (USB/JSON data transfer), Online Sync (Pending Receipts Approval), Smart Import (Excel upload), Backup & Restore (with pre-restore integrity checks), and System Logs. The UI enforces license permissions by disabling online tools for offline-only subscriptions while keeping offline tools functional.
