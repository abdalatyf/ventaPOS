# Handoff Report — Backend Codebase Explorer (`explorer_m1_1`)

## 1. Observation

1. **Django Models (`d:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\models.py`)**:
   - `Receipt` (line 698): Primary key `id` (UUID), `tenant` (FK), `branch` (FK), `salesperson` (FK), `local_id`, `receipt_number`, `client_uuid` (UUID), `receipt_hash` (CharField 255), `customer_name`, `phone_number`, `address`, `area`, `total_amount` (Decimal 12,2), `down_payment` (Decimal 12,2), `installment_system`, `sale_year`, `sale_month`, `is_cash_sale` (Boolean), `products_text`, `is_confirmed`, `is_deleted` (Boolean), `created_at_local`, `created_at`.
   - `SaleItem` (line 797): `tenant` (FK), `receipt` (FK), `inventory_item` (FK), `quantity` (Int), `unit_price` (Decimal 12,2), `is_deleted`.
   - `InstallmentPayment` (line 847): `tenant` (FK), `receipt` (FK), `payment_date` (DateField), `amount` (Decimal 12,2), `is_deleted`.
   - `InventoryItem` (line 242): `tenant` (FK), `branch` (FK), `local_id`, `name`, `initial_quantity`, `initial_purchase_price`, `initial_commission_amount`, `initial_month`, `initial_year`.
   - `Tenant` (line 67): `company_code` (unique), `name`, `is_active`, `is_deleted`.
   - `Customer`: Stored denormalized on `Receipt` records (`customer_name`, `phone_number`, `address`, `area`); queried by autocomplete. Defaults `customer_name="عميل نقدي"` when `is_cash_sale=True` and `customer_name` is blank.

2. **API Routes & Endpoint Resolution (`d:\Projects\VentaPOS\VentaPOS_NextGen\backend\backend\urls.py` and `api/urls.py`)**:
   - Prefix `/api/v1/` mounted in `backend/urls.py`:
     - `/api/v1/product-suggestions/` -> `ProductSuggestionsView` (`api/views.py`: line 1598)
     - `/api/v1/customer-suggestions/` -> `CustomerSuggestionsView` (`api/views.py`: line 1500)
     - `/api/v1/receipts/` -> `ReceiptViewSet` (`api/views.py`: line 666, `api/serializers.py`: line 297)
     - `/api/v1/installment-payments/` -> `InstallmentPaymentViewSet` (`api/views.py`: line 691)
     - `/api/v1/sale-items/` -> `SaleItemViewSet` (`api/views.py`: line 684)

3. **Financial Math & Algorithms**:
   - `25th-of-month Rule`: `InstallmentPaymentSerializer` (`api/serializers.py`: line 269) converts `payment_month` and `payment_year` to `payment_date` formatted as `YYYY-MM-25`.
   - `Retroactive Safe Stock Limit`: `calculate_safe_stock_limit` (`api/views.py`: line 1467) checks stock levels across consecutive months from target sale date to default date and prevents selling more than the minimum available quantity.
   - `HMAC-SHA256 Signatures`:
     - `generate_receipt_signature(...)` (`api/utils/security_utils.py`: line 114) creates `RECEIPT-{receipt_number}-{total_amount}-{sale_month}-{sale_year}-ITEMS[...]` signature.
     - `generate_record_signature(...)` (`api/utils/security_utils.py`: line 97) creates `{expiry_date}-{balance}-{machine_id}-{product_id}-{is_active}` signature for `ClientLicense`.

4. **Multi-Tenant Isolation & Database Setup**:
   - `TenantFromRequestMixin` (`api/views.py`: line 118) resolves `Tenant` from `X-Company-Code` header and filters querysets (`filter(tenant=tenant)`).
   - `SystemDBRouter` (`api/db_router.py`: line 1) routes business operational tables to `'default'` DB (`backend/db/business_data.sqlite3`) and licensing/auth tables to `'system'` DB (`%APPDATA%/VentaPOS/system.sqlite3`).
   - `main.py` (line 53) decrypts `%APPDATA%/VentaPOS/business_data.enc` into `%TEMP%/~sys_runtime_cache_v1.tmp` during PyWebView desktop execution.

---

## 2. Logic Chain

1. **From Observation 1**: The backend stores receipts in `Receipt` and related items/installments in `SaleItem` and `InstallmentPayment`. Customer info is directly on `Receipt` without a separate customer entity, simplifying POS cash transactions.
2. **From Observation 2**: API endpoints are strictly prefixed under `/api/v1/`. Receipt creation accepts nested payloads (`sale_items`/`items` and `installment_payments`/`installments`), handling field aliases like `customer_phone` -> `phone_number`.
3. **From Observation 3**: Financial precision is maintained via `DecimalField(12, 2)`. Installments automatically map to day 25 of the month (`YYYY-MM-25`). Hash signatures (`receipt_hash` and `license_code_hash`) protect data integrity against unauthorized manual modifications.
4. **From Observation 4**: Multi-tenancy is enforced on every request via `X-Company-Code` header and `TenantFromRequestMixin`. Database storage uses SQLite with Django migrations, routed between default business DB and system license DB.

---

## 3. Caveats

- Frontend UI component testing (`http://localhost:5173/pos`) is in the scope of M2 (UI & End-to-End Submission Testing).
- Live desktop Fernet encryption/decryption runtime (`main.py`) applies when running via PyWebView. Running via standard Django dev server (`python manage.py runserver`) uses `backend/db/business_data.sqlite3` directly.

---

## 4. Conclusion

The Django backend for VentaPOS NextGen is fully analyzed and documented. All required models, API endpoints, financial math formulas, 25th-of-month installment rules, HMAC-SHA256 signature algorithms, multi-tenant headers, and dual SQLite database routing structures have been located and verified.

The analysis report has been saved to:  
`d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\explorer_m1_1\analysis.md`

---

## 5. Verification Method

To independently verify this analysis:

1. **Run Django Unit Tests**:
   Execute from `d:\Projects\VentaPOS\VentaPOS_NextGen\backend`:
   ```powershell
   python manage.py test api.tests.test_suggestions_and_parity --databases=default,system
   ```
2. **Inspect Files**:
   - Models: `d:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\models.py`
   - Serializers & Receipt Logic: `d:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\serializers.py`
   - Views & Autocomplete: `d:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\views.py`
   - Security Signatures: `d:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\utils\security_utils.py`
   - Database Routing: `d:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\db_router.py` and `backend/settings.py`
