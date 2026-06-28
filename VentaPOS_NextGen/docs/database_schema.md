# VentaPOS NextGen - Database Schema
*This document serves as the absolute Single Source of Truth for the Database Schema, enforcing the Dual-DB architecture.*

## 🗄️ Architecture Overview
The system relies on a strictly separated Dual-Database configuration to isolate licensing security from business transactions.

1. **System Database (`system.sqlite3`)**: Stored permanently in `%APPDATA%\VentaPOS\`. Contains Licenses, Users, and Activity Logs.
2. **Business Database (`business_data.enc`)**: Stored in `%APPDATA%\VentaPOS\`. Extracted at runtime to a Temp folder. Contains Receipts, Inventory, and Settings.

---

## 🛡️ 1. System Database (`system`)

### `ClientLicense`
Controls application activation, valid date bounds, and the maximum allowed invoices to be printed.
*   **`id`**: Primary Key
*   **`product_id`**: Integer (e.g., 1=Trial, 2=PrintOnly, 10=ChargeCard)
*   **`start_date`**: Date (When the license was activated)
*   **`expiry_date`**: Date (When the license expires, `null` for lifetime)
*   **`invoices_balance`**: PositiveInteger (Available receipts to print)
*   **`is_active`**: Boolean (Flags if license is valid. Instantly set to `False` if tampered)
*   **`machine_id`**: String (Cryptographic hardware hash bound to this PC)
*   **`license_code_hash`**: String (HMAC signature for anti-tamper checking)

### `UsedLicense`
Prevents a 16-character charge code from being used more than once.
*   **`id`**: Primary Key
*   **`code_hash`**: String (SHA-256 hash of the used code)
*   **`used_at`**: DateTime

### `LicenseHistory`
Archival log of all activations and recharges.
*   **`id`**: Primary Key
*   **`product_name`**: String
*   **`operation_type`**: String
*   **`added_balance`**: Integer
*   **`archived_at`**: DateTime

### `ActionLog`
Audit trail for local operations (Security).
*   **`actor`**: String (User performing action)
*   **`action_type`**: String (CREATE, UPDATE, DELETE, SYNC)
*   **`model_name`**: String
*   **`details`**: Text

---

## 🏢 2. Business Database (`default`)

### `CompanySetting`
Singleton configuration for the company profile.
*   **`name`**: String (Company Name)
*   **`company_code`**: String (Unique 4-digit code assigned upon cloud subscription)
*   **`description`**: String
*   **`phone1` / `phone2`**: String
*   **`footer_text`**: String (Printed at the bottom of receipts)

### `Branch`
Physical store or warehouse locations.
*   **`name`**: String (Unique)
*   **`is_synced`**: Boolean

### `Salesperson`
Employees executing sales.
*   **`name`**: String
*   **`branch`**: ForeignKey (`Branch`)

### `InventoryItem`
Product catalog and base metrics.
*   **`name`**: String
*   **`branch`**: ForeignKey (`Branch`)
*   **`initial_quantity`**: PositiveInteger (Opening stock)
*   **`initial_purchase_price`**: PositiveInteger (Opening cost)
*   **`initial_commission_amount`**: PositiveInteger (Base salesperson commission)
*   **`initial_month` / `initial_year`**: Integer (Time-machine anchoring)

### `CommissionHistory`
Time-based commission rate adjustments.
*   **`item`**: ForeignKey (`InventoryItem`)
*   **`commission_amount`**: PositiveInteger
*   **`activation_month` / `activation_year`**: Integer

### `InventoryAdjustment`
Manual deficit/surplus logging.
*   **`item`**: ForeignKey (`InventoryItem`)
*   **`adjustment_type`**: String (DEFICIT, SURPLUS)
*   **`quantity`**: PositiveInteger
*   **`month` / `year`**: Integer

### `Supplier`
Factories and vendors.
*   **`name`**: String (Unique)

### `PurchaseInvoice`
Restock or Return operations.
*   **`invoice_number`**: PositiveInteger
*   **`supplier`**: ForeignKey (`Supplier`)
*   **`invoice_type`**: String (PURCHASE, RETURN)
*   **`invoice_month` / `invoice_year`**: Integer

### `PurchaseInvoiceItem`
Line items for purchases.
*   **`invoice`**: ForeignKey (`PurchaseInvoice`)
*   **`inventory_item`**: ForeignKey (`InventoryItem`)
*   **`quantity`**: PositiveInteger
*   **`purchase_price`**: PositiveInteger

### `Receipt`
Point of Sale transactions.
*   **`receipt_number`**: PositiveInteger
*   **`branch`**: ForeignKey (`Branch`)
*   **`customer_name`**: String
*   **`total_amount`**: PositiveInteger
*   **`down_payment`**: PositiveInteger
*   **`salesperson`**: ForeignKey (`Salesperson`, null=True)
*   **`sale_month` / `sale_year`**: Integer
*   **`is_cash_sale`**: Boolean
*   **`receipt_hash`**: String (HMAC signature to prevent manual database injection)

### `SaleItem`
Line items for receipts.
*   **`receipt`**: ForeignKey (`Receipt`)
*   **`inventory_item`**: ForeignKey (`InventoryItem`)
*   **`quantity`**: PositiveInteger
*   **`unit_price`**: PositiveInteger

### `InstallmentPayment`
Credit schedule for non-cash sales.
*   **`receipt`**: ForeignKey (`Receipt`)
*   **`payment_month` / `payment_year`**: Integer (e.g., June 2026)
*   **`amount`**: PositiveInteger

### `PendingExternalReceipt`
Staging area for offline USB imports.
*   **`batch_id`**: String
*   **`payload`**: JSONField (Raw receipt dump)
*   **`is_processed`**: Boolean
