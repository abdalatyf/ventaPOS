# VentaPOS NextGen — Parity Test Strategy Documentation

**File:** `backend/api/tests/test_parity.py`
**Total Test Cases:** 47 across 7 test classes
**Methodology:** Every test was derived by reading the actual legacy source code, not from documentation alone.

---

## 1. Scope & Philosophy

This test suite verifies **feature parity** between the legacy VentaPOS Desktop (Django/SQLite, `d:/Projects/VentaPOS/Desktop/`) and the new VentaPOS NextGen (Django REST Framework, `d:/Projects/VentaPOS/VentaPOS_NextGen/backend/`).

A parity test is only meaningful if it is grounded in the **actual legacy behavior**. All expected values in this suite were derived from reading:

- `Desktop/sales/salesapp/models.py` — `InventoryItem.get_stock_at_date()` (lines 152–189), `Receipt.save()` (lines 379–415)
- `Desktop/sales/salesapp/security_utils.py` — `generate_receipt_signature()` (lines 114–122), `generate_record_signature()` (lines 97–108)
- `Desktop/sales/salesapp/views/receipt_views.py` — installment schedule generation (lines 316–322)
- `requirements.md` — authoritative business rules (§4, §5, §6, §8)

---

## 2. Test Classes Overview

| # | Class | Source File(s) | Cases | Domain |
|---|-------|----------------|-------|--------|
| 1 | `TimeMachineStockTests` | `models.py:152–189` | 10 | Inventory |
| 2 | `InvoiceHashTests` | `security_utils.py:114–122` | 9 | Cryptography |
| 3 | `InstallmentScheduleTests` | `receipt_views.py:316–322` | 8 | Finance |
| 4 | `LicenseBalanceTests` | `models.py:379–415`, `serializers.py:99–144` | 7 | Licensing |
| 5 | `RecordSignatureTests` | `security_utils.py:97–108` | 6 | Security |
| 6 | `LicenseValidatorTests` | `license_validator.py` | 7 | Licensing |
| 7 | `CommissionHistoryTests` | `models.py:205–215` | 3 | Finance |

---

## 3. Class-by-Class Details

### 3.1 TimeMachineStockTests

**Business Rule (requirements.md §4.1):**
```
final_stock = (initial_quantity + total_purchased + total_surplus)
            − (total_sold + total_returned + total_deficit)
return max(0, final_stock)
```

Date filtering uses **logical month/year fields** (`sale_year`, `sale_month`, `invoice_year`, `invoice_month`) — NOT `created_at`. This is the "Time-Machine" property.

| ID | Test | Edge Case Covered |
|----|------|-------------------|
| TC-STOCK-01 | Opening month = initial_quantity | Baseline |
| TC-STOCK-02 | Before opening date → 0 | Guard clause |
| TC-STOCK-03 | Purchase in month X visible from month X, invisible before | Date boundary |
| TC-STOCK-04 | Sale in month X reduces from month X onward | Core formula |
| TC-STOCK-05 | **Backdated invoice** retro-reduces historical stock | Critical edge case |
| TC-STOCK-06 | Stock never goes below 0 (`max(0, ...)`) | **BUG FLAG** (see below) |
| TC-STOCK-07 | SURPLUS/DEFICIT adjustments | Adjustment types |
| TC-STOCK-08 | Factory RETURN reduces stock | Invoice type RETURN |
| TC-STOCK-09 | Combined multi-movement scenario | Integration |
| TC-STOCK-10 | Cross-year boundary (Nov→Dec→Jan) | Year rollover |

> **⚠️ BUG DOCUMENTED — TC-STOCK-06:**
> The legacy `InventoryItem.get_stock_at_date()` in `Desktop/salesapp/models.py:189` applies `return max(0, final_stock)`.
> The NextGen implementation in `VentaPOS_NextGen/backend/api/models.py:92` returns the raw result **without the max(0, ...) clamp**. This means the NextGen can return negative stock values, which is incorrect behavior.
> **TC-STOCK-06 will fail until this is fixed.** The fix is a one-line change on line 92 of `api/models.py`:
> ```python
> # Current (WRONG):
> return stock + purchases + adj_plus - sales - returns - adj_minus
> # Correct (matches legacy):
> return max(0, stock + purchases + adj_plus - sales - returns - adj_minus)
> ```

---

### 3.2 InvoiceHashTests

**Business Rule (requirements.md §5 & `security_utils.py:114–122`):**
```python
data_to_sign = f"RECEIPT-{receipt_number}-{total_amount}-{sale_month}-{sale_year}"
return hmac.new(SECRET_DB_KEY, data_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
```

| ID | Test | Property |
|----|------|----------|
| TC-HASH-01 | No-items hash matches legacy formula exactly | Backward compat |
| TC-HASH-02 | Empty list is falsy → also matches legacy | Edge case |
| TC-HASH-03 | Same inputs → same hash (determinism) | Basic HMAC property |
| TC-HASH-04 | Different `receipt_number` → different hash | Tamper detection |
| TC-HASH-05 | Different `total_amount` → different hash | Tamper detection |
| TC-HASH-06 | Different `sale_month` → different hash | Tamper detection |
| TC-HASH-07 | Different `sale_year` → different hash | Tamper detection |
| TC-HASH-08 | Output is 64-char hex string | Format assertion |
| TC-HASH-09 | **Items data diverges from legacy** | Discrepancy documented |

> **⚠️ BEHAVIORAL DISCREPANCY — TC-HASH-09:**
> The NextGen `generate_receipt_signature()` in `api/utils/security_utils.py:114–132` has an optional `items_data` parameter that extends the hash message with an `ITEMS[...]` suffix.
> When called from `ReceiptSerializer.create()` (line 123–129), `items_data` IS passed, making the hash **different from the legacy** for the same receipt.
>
> **Impact:** Receipts created via the NextGen API will have a different `receipt_hash` than if created via the legacy desktop for the same data.
>
> **Migration Requirement:** The migration script MUST call `generate_receipt_signature(..., items_data=None)` when importing historical legacy receipts, to preserve their original hashes (as required by `requirements.md §3.2`).

---

### 3.3 InstallmentScheduleTests

**Business Rule (requirements.md §8.5 & `receipt_views.py:316–322`):**
```python
start_date = date(sale_year, sale_month, 25)
for i, amt in enumerate(installment_amounts):
    due_date = start_date + relativedelta(months=i + 1)
    # Creates InstallmentPayment with this due_date
```

Key properties tested:
- **Day is always 25** (not the sale day, not the end of month)
- **First installment is the month AFTER the sale month** (`months=i+1` where `i=0`)
- **Month wrapping** is handled by `dateutil.relativedelta` (no manual rollover)
- **3-group system** (up to 3 `sys{n}_count × sys{n}_amount` inputs) expands to individual amounts

> **⚠️ MODEL FIELD DISCREPANCY:**
> The legacy `InstallmentPayment` model uses a single `payment_date` (DateField).
> The NextGen model (`api/models.py:162–166`) uses integer `payment_month` + `payment_year` fields instead.
>
> The schedule-generation logic must be adapted when creating NextGen `InstallmentPayment` records to extract `.month` and `.year` from the computed `due_date` datetime object.

---

### 3.4 LicenseBalanceTests

**Business Rule (legacy `models.py:379–415`, NextGen `serializers.py:99–144`):**

1. Creating a new `Receipt` deducts exactly **1** from `invoices_balance`
2. If no active license has `invoices_balance > 0` → raises `ValidationError`
3. Deleting a receipt does **NOT** restore the balance (neither system implements this)

> **⚠️ PRIORITY DIFFERENCE — Base vs. Recharge License:**
> The legacy `Receipt.save()` uses a two-tier priority: first looks for `product_id < 10` (base licenses), then falls back to `product_id >= 10` (recharge codes).
> The NextGen `ReceiptSerializer.create()` at line 105 uses `select_for_update().filter(is_active=True, invoices_balance__gt=0).first()` — **no product_id filter**.
>
> This means the NextGen may consume a recharge code BEFORE exhausting base license balance, which **differs from the legacy behavior**. TC-LIC-01 through TC-LIC-07 test the NextGen behavior as implemented. A separate test should be added if/when the priority logic is aligned.

---

### 3.5 RecordSignatureTests

**Business Rule (requirements.md §6 & `security_utils.py:97–108`):**
```python
data = f"{expiry_date}-{balance}-{machine_id}-{product_id}-{is_active}"
return hmac.new(SECRET_DB_KEY, data.encode('utf-8'), hashlib.sha256).hexdigest()
```

This signature protects `ClientLicense` rows from direct SQL tampering. The middleware recalculates and compares it on every non-static request.

Tests verify that changing ANY field (balance, expiry, is_active) invalidates the signature, ensuring tamper-detection sensitivity.

---

### 3.6 LicenseValidatorTests

Tests the `LicenseValidator.validate()` method which implements the full 80-bit cryptographic key protocol:
1. Custom Base32 → 80-bit integer
2. Bitwise extraction of signature (36 bits) + masked data (44 bits)
3. XOR unmasking with the shifted signature
4. HMAC-SHA256 verification using the 86-byte secret key
5. Machine binding check

Since generating valid license keys requires the proprietary key-generation tool, these tests focus on failure paths and internal utilities.

---

### 3.7 CommissionHistoryTests

**Business Rule (legacy `models.py:205–215`, NextGen `api/models.py:94–102`):**
Returns the most recent `CommissionHistory` record at or before the queried month/year, falling back to `initial_commission_amount` if no history exists.

---

## 4. How to Run

```bash
# From d:/Projects/VentaPOS/VentaPOS_NextGen/backend/

# Run all parity tests
python manage.py test api.tests.test_parity --verbosity=2

# Run a specific class
python manage.py test api.tests.test_parity.TimeMachineStockTests --verbosity=2

# Run a single test case
python manage.py test api.tests.test_parity.TimeMachineStockTests.test_stock_never_goes_below_zero --verbosity=2
```

---

## 5. Known Failures (Pre-Fix)

The following tests are **expected to fail** on the current NextGen codebase and represent known bugs that must be fixed before the NextGen system can be considered feature-complete:

| Test | File to Fix | Line | Fix Required |
|------|-------------|------|--------------|
| `TC-STOCK-06` `test_stock_never_goes_below_zero` | `api/models.py` | 92 | Wrap result with `max(0, ...)` |

---

## 6. Discrepancies That Are Accepted by Design

| Discrepancy | Decision |
|-------------|----------|
| `generate_receipt_signature` with `items_data` produces a different hash than legacy | **Accepted** — New receipts created in NextGen use the extended hash. Migration MUST use `items_data=None`. |
| `ReceiptSerializer` does not filter licenses by `product_id < 10` first | **Documented** — Behavior differs from legacy priority order. Acceptable for NextGen if a single license type is used. |
| `InstallmentPayment` uses `payment_month/payment_year` (int) instead of `payment_date` (DateField) | **Documented** — NextGen model change; schedule generation logic must be adapted accordingly. |
