# Server Application - Core Business Logic Memory

This document traces the exact mathematical steps, core algorithms, data transformations, state management workflows, and fundamental business rules of the VentaPOS Server application. 
The primary business logic resides in `D:\Projects\VentaPOS\Server\sync_api\views.py` and centers around the one-way, mass-ingestion synchronization process from local client applications.

## Sync Ingestion Flow (`SyncIngestView.post`)
**Path**: `sync_api/views.py` -> `SyncIngestView`

### 1. Request Parsing & Validation
- Parses incoming request body as JSON.
- Extracts `machine_id` (representing the client hardware footprint).
- Extracts `payload` (a dictionary containing nested arrays of entities).

### 2. Security Check (The Gatekeeper)
- Queries `ServerLicense` for `machine_id=machine_id` where `is_active=True`.
- **Edge Case**: If no license matches or `is_active` is False, immediately returns a `403 Forbidden` JSON response `{'status': 'error', 'message': 'Unauthorized Machine ID'}`.
- If authorized, updates `license.last_sync_at = timezone.now()` and saves it.

### 3. Atomic Data Processing (The Transaction Block)
The entire data ingestion is wrapped in `with transaction.atomic():` to ensure that either all data is saved successfully, or the entire payload is rejected, preventing partial/corrupted sync states.

#### Phase A: Reference Data (Upsert Mode)
The server uses `update_or_create` matching on `(source_machine_id, local_id)` to gracefully handle both first-time creation and subsequent updates.
1. **Company Settings**: Looks for `company_settings` in payload. Defaults to `local_id=1` and upserts `name`, `description`, `phone1`, `phone2`, `footer_text`.
2. **Branches**: Upserts using `b['id']` and `b['name']`.
3. **Salespeople**: Upserts using `sp['id']`, mapped to `local_branch_id`.
4. **Inventory**: Upserts using `item['id']`. Updates `quantity`, `purchase_price`, `salesperson_commission_amount`, and links to `local_branch_id`.

#### Phase B: Financial & Transactional Data (Hard Reset Mode for Children)
5. **Receipts (Invoices)**: 
   - Uses `update_or_create` on `ServerReceipt` matching on `(source_machine_id, local_id)`.
   - Populates core invoice metadata (`total_amount`, `down_payment`, `sale_year`, `sale_month`, `is_cash_sale`).
   - Links to `local_branch_id` and optionally `local_salesperson_id`.
   - **Child Entity Overwrite Strategy**: For every receipt processed:
     - Calls `receipt_obj.items.all().delete()` and recreates all `ServerSaleItem` rows from `r['items']`.
     - Calls `receipt_obj.payments.all().delete()` and recreates all `ServerInstallmentPayment` rows from `r['payments']`.
   - Increments a `processed_count` tracker.

6. **Expenses**:
   - Upserts `ServerExpense` using `exp['id']`.
   - Records `amount`, `description`, `expense_year`, `expense_month`.

7. **Stock Transactions**:
   - Upserts `ServerStockTransaction` using `st['id']`.
   - Records `transaction_type`, `quantity`, and `product_name_snapshot`.

### 4. Response Dispatch
- **Success**: Returns `200 OK` JSON with `{'status': 'success', 'message': 'Data synced successfully. Receipts processed: X'}`.
- **Exception Handling**: Catches all generic exceptions during the atomic block, triggering an implicit database rollback. Returns `500 Internal Server Error` JSON with `{'status': 'error', 'message': str(e)}`.

## Key Architectural Rules
1. **Source of Truth Delegation**: The server treats the client app as the absolute source of truth for POS data. It blindly accepts the state of `receipts` and `inventory quantities` instead of re-calculating them locally. 
2. **Composite Key Identifier**: Almost all models use `(source_machine_id, local_id)` as a composite unique identifier to support multi-tenant synchronization cleanly.
3. **Immutable History for Names**: The server persists `product_name_snapshot` on transaction lines instead of relying on ForeignKeys to the Inventory item, protecting historical invoices if the product name changes in the future.
