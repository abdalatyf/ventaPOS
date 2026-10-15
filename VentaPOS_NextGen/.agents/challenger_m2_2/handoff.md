# Handoff Report — M2 Challenger 2 (Tenant Isolation & Stock Limits)

## 1. Observation

Empirical testing was executed using `d:\Projects\VentaPOS\VentaPOS_NextGen\venv\Scripts\python.exe .agents/challenger_m2_2/verify_m2_2.py` against the Django backend and SQLite database `backend/db/business_data.sqlite3`.

### Task 1 Observations: Multi-Tenant Isolation
1. **Valid Tenant Code Isolation (`X-Company-Code: 1234`)**:
   - `GET /api/v1/salespersons/` returned HTTP 200 with data filtered to Tenant `"1234"` (ID: `703e4534-ae85-4820-a7ce-4346ef1bd0b6`). `Seller 5678` (belonging to Tenant `"5678"`) was excluded.
2. **Invalid Tenant Code Handling (`X-Company-Code: INVALID_CODE_999`)**:
   - HTTP 400 Bad Request returned:
     ```json
     {"company_code": "رمز الشركة المكتوب غير مسجل في الدفتر، يرجى التحقق من الرقم."}
     ```
3. **Inactive Tenant Handling (`X-Company-Code: 999000`)**:
   - HTTP 400 Bad Request returned:
     ```json
     {"company_code": "الاشتراك السحابي للشركة انتهى أو معطل، يرجى التجديد لتتمكن من الدخول."}
     ```
4. **Missing Header Fallback Vulnerability**:
   - `GET /api/v1/salespersons/` without `X-Company-Code` header returned HTTP 200 containing data from `Tenant.objects.filter(is_deleted=False).first()`.
   - Inspection of `backend/api/views.py` lines 162-164 confirms:
     ```python
     # Fall back to local default tenant since this is a local-first application
     tenant = Tenant.objects.filter(is_deleted=False).first()
     if tenant:
         return tenant
     ```

### Task 2 Observations: DB Tenant Binding & Receipts
1. **Database Binding Inspection (`backend/db/business_data.sqlite3`)**:
   - Created receipt via `POST /api/v1/receipts/` with header `X-Company-Code: 1234`.
   - DB row inspection confirmed:
     - `Receipt` (ID: `9f0dbcf2-ffd4-488a-b512-ac0a73566f4a`): `tenant_id` = `703e4534-ae85-4820-a7ce-4346ef1bd0b6`.
     - `SaleItem` (ID: `47baea0a-c2ca-4508-a5c7-1f36ad88d3eb`): `tenant_id` = `703e4534-ae85-4820-a7ce-4346ef1bd0b6`.
     - `InstallmentPayment` #1 (ID: `79e7eb6b-2846-4483-8fe0-66179cbf4f07`): `tenant_id` = `703e4534-ae85-4820-a7ce-4346ef1bd0b6`.
     - `InstallmentPayment` #2 (ID: `cdc6c720-9c48-4aea-a77a-a8760a071dd9`): `tenant_id` = `703e4534-ae85-4820-a7ce-4346ef1bd0b6`.
   - Querying `GET /api/v1/receipts/` with `X-Company-Code: 5678` returned HTTP 200 with an empty list `[]`. Receipt `9f0dbcf2-...` was isolated.
2. **Receipt Hash Missing Tenant ID Vulnerability**:
   - Inspection of `backend/api/utils/security_utils.py` lines 114-119:
     ```python
     def generate_receipt_signature(receipt_number, total_amount, sale_month, sale_year, items_data=None):
         SECRET_DB_KEY = LicenseValidator._get_key()
         data_to_sign = f"RECEIPT-{receipt_number}-{total_amount}-{sale_month}-{sale_year}"
     ```
   - `tenant_id` is omitted from `data_to_sign`. Since `receipt_hash` has a `UNIQUE` constraint across the entire `receipt` table (`models.CharField(max_length=64, unique=True)`), identical receipt numbers and totals across two different tenants cause a DB `IntegrityError`.
3. **Soft-Delete Receipt Number Recycling**:
   - Inspection of `backend/api/serializers.py` lines 407-417:
     ```python
     last = (
         Receipt.all_objects
         .select_for_update()
         .filter(tenant=tenant, is_deleted=False)
         .order_by("receipt_number")
         .last()
     )
     ```
   - Soft-deleted receipts (`is_deleted=True`) are excluded. The serializer re-uses `receipt_number`, which re-generates an identical `receipt_hash` and fails with `UNIQUE constraint failed: receipt.receipt_hash`.
4. **Misleading Error Handling**:
   - Inspection of `backend/api/views.py` lines 258-261:
     ```python
     except IntegrityError as e:
         if "UNIQUE constraint failed" in str(e):
             raise ValidationError({"name": ["الاسم ده متسجل قبل كده، أو موجود في سلة المهملات."]})
     ```
   - Any `receipt_hash` or `local_id` unique constraint failure is returned to the client as a duplicated item name error.

### Task 3 Observations: Retroactive Stock Limit (`calculate_safe_stock_limit`)
1. **Retroactive Calculation & Enforcement**:
   - Initial stock in 1/2026 = 100. Sales in 3/2026 = 60, Sales in 5/2026 = 30.
   - Calling `calculate_safe_stock_limit(item, default_year=2026, default_month=7, target_year=2026, target_month=2)` evaluated stock in months [2, 3, 4, 5, 6, 7] = [100, 40, 40, 10, 10, 10] -> min stock returned = **10**.
   - POSTing a sale for quantity 15 (> 10) in 2/2026 returned HTTP 400 Bad Request:
     ```json
     {"error": "عفواً، لا يمكن البيع! أقصى كمية يمكن بيعها بأثر رجعي للصنف 'Widget Stock Test' هي (10) لتجنب حدوث رصيد سالب في الشهور اللاحقة."}
     ```
   - POSTing a sale for quantity 8 (<= 10) in 2/2026 returned HTTP 201 Created.
   - Subsequent `calculate_safe_stock_limit()` returned **2**.
2. **Edge Cases**:
   - Target date before item initialization (12/2025 vs initial 1/2026) returned **0**.
   - Future target date (9/2026) evaluated range [7, 8, 9] -> returned **2**.
3. **Flaw: License Start Date vs Item Initial Year**:
   - Inspection of `backend/api/views.py` lines 1440-1442:
     ```python
     active_license = ClientLicense.objects.filter(tenant=tenant, is_active=True, is_deleted=False).order_by('-start_date').first()
     if active_license and active_license.start_date:
         return active_license.start_date.year, active_license.start_date.month
     ```
   - If `active_license.start_date` is `2025-01-01` and an item has `initial_year=2026`, `get_default_date_for_tenant()` returns `(2025, 1)`. `calculate_safe_stock_limit()` evaluates stock starting at 1/2025 where item stock is 0, setting `safe_limit = 0` and blocking ALL sales for that item in 2026.

---

## 2. Logic Chain

1. **Isolation Verification**:
   - Observation 1.1 shows header `X-Company-Code: 1234` scopes API querysets to tenant `"1234"`.
   - Observations 1.2 & 1.3 show invalid/inactive tenant headers trigger validation exceptions.
   - Observation 1.4 proves missing headers silently access `Tenant.objects.first()`. In a multi-tenant environment without JWT auth or missing header, data isolation is compromised.
2. **Database Record Binding**:
   - Observation 2.1 proves `ReceiptSerializer.create()` explicitly assigns `tenant` to `Receipt`, `SaleItem`, and `InstallmentPayment`. All FKs in `business_data.sqlite3` match Tenant "1234".
   - Observations 2.2 & 2.3 prove `generate_receipt_signature()` omits `tenant_id` and `ReceiptSerializer` ignores soft-deleted receipts during number generation. This causes cross-tenant and post-deletion hash collisions on the DB `UNIQUE` constraint.
   - Observation 2.4 shows unique constraint exceptions are misclassified as name duplication errors.
3. **Retroactive Stock Limits**:
   - Observations 3.1 & 3.2 demonstrate `calculate_safe_stock_limit()` correctly finds the minimum stock across consecutive months between `(default_year, default_month)` and `(target_year, target_month)` and blocks sales exceeding that minimum.
   - Observation 3.3 reveals that when `active_license.start_date` precedes item `initial_year`, `get_default_date_for_tenant()` uses the license date, causing `calculate_safe_stock_limit()` to evaluate pre-creation months (where stock is 0), incorrectly locking stock at 0.

---

## 3. Caveats

- **Network Mode**: Tests were performed in `CODE_ONLY` offline environment.
- **Authentication**: JWT token payload resolution (`TenantFromRequestMixin` fallback) was verified via ORM structure; primary device flow tested via `X-Company-Code`.

---

## 4. Conclusion

1. **Multi-tenant Isolation**: **PASSED WITH SECURITY FINDINGS**. `X-Company-Code` header properly isolates tenant data and rejects invalid/inactive tenants. However, missing headers silently fall back to `Tenant.objects.first()`.
2. **Database Record Binding**: **PASSED WITH ARCHITECTURAL FINDINGS**. All created `Receipt`, `SaleItem`, and `InstallmentPayment` records in `backend/db/business_data.sqlite3` are strictly bound to `tenant_id`. However, `generate_receipt_signature()` lacks `tenant_id`, soft-deleted receipts cause hash collisions, and `perform_create()` misreports DB integrity errors.
3. **Retroactive Stock Limits**: **PASSED WITH ALGORITHMIC FINDINGS**. `calculate_safe_stock_limit()` accurately calculates minimum stock and enforces limits across past and future months. However, when `active_license.start_date` is earlier than an item's `initial_year`, stock limit defaults to 0 and blocks legitimate sales.

---

## 5. Verification Method

To re-verify these findings independently:

```bash
# Execute empirical verification test harness
d:\Projects\VentaPOS\VentaPOS_NextGen\venv\Scripts\python.exe .agents/challenger_m2_2/verify_m2_2.py
```

### Files to Inspect:
- `backend/api/views.py` (lines 135-170, 258-262, 1435-1482)
- `backend/api/serializers.py` (lines 375-470)
- `backend/api/utils/security_utils.py` (lines 114-132)
- `backend/db/business_data.sqlite3` (tables `receipt`, `sale_item`, `installment_payment`)
