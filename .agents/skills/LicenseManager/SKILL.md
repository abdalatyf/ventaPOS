---
name: ventapos-licensemanager
description: Complete technical documentation of the VentaPOS LicenseManager subsystem, including database schema, license code generation, client validation mechanisms, and quality audit findings, fully verified against the source code.
---

# VentaPOS LicenseManager Technical Manual & Code Audit

This document provides the definitive technical specification, architectural layout, and security audit of the VentaPOS Licensing Subsystem. It covers the database models, cryptographic code generation protocol, client-side validation logic, runtime enforcement gates, and known architectural/security vulnerabilities.

---

## 1. Licensing Model Overview

VentaPOS maps client permissions to specific package identifiers (`product_id` 1 to 16). The packages are split into four main categories: Trial, Time-based plans, Cloud sync add-ons, and Balance recharge packages.

### Product ID Mapping Table
The complete suite of licensing choices is defined identically on the server (`LicenseManager/licenses/models.py`, lines 21–38) and the client (`Desktop/sales/salesapp/models.py`, lines 483–500):

| ID | Package Name (Source Label) | Category | Expiry Behavior / Duration | Client-side Tier & Permissions |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `تجربة مجانية (Trial 60 Days)` | Trial | 60 Days (calculated dynamically on client, warning on Admin discrepancy) | Pro Tier (for evaluation purposes) |
| **2** | `طباعة فقط - سنة واحدة` | Time-based Basic | 365 Days | Basic (Printing capabilities only) |
| **3** | `طباعة فقط - مدى الحياة` | Lifetime Basic | 99 Years (36,135 days) | Basic (Printing capabilities only) |
| **4** | `إدارة كاملة - سنة واحدة` | Time-based Pro | 365 Days | Pro (Full ERP & management features) |
| **5** | `إدارة كاملة - 3 سنوات` | Time-based Pro | 1095 Days | Pro (Full ERP & management features) |
| **6** | `إدارة كاملة - 5 سنوات` | Time-based Pro | 1825 Days | Pro (Full ERP & management features) |
| **7** | `إدارة كاملة - مدى الحياة (VIP)` | Lifetime Pro | 99 Years (36,135 days) | Pro (Full ERP & management features) |
| **8** | `إضافة الأونلاين - سنة` | Cloud Add-on | 365 Days | Basic / Pro (Enables cloud sync client/viewer features) |
| **9** | `إضافة الأونلاين - 5 سنوات` | Cloud Add-on | 1825 Days | Basic / Pro (Enables cloud sync client/viewer features) |
| **10** | `كود شحن (100 فاتورة)` | Balance Recharge | Infinite (Increments invoice balance by 100) | - (Replenishes active transaction balance) |
| **11** | `كود شحن (300 فاتورة)` | Balance Recharge | Infinite (Increments invoice balance by 300) | - (Replenishes active transaction balance) |
| **12** | `كود شحن (500 فاتورة)` | Balance Recharge | Infinite (Increments invoice balance by 500) | - (Replenishes active transaction balance) |
| **13** | `كود شحن (1000 فاتورة)` | Balance Recharge | Infinite (Increments invoice balance by 1000) | - (Replenishes active transaction balance) |
| **14** | `كود شحن (3000 فاتورة)` | Balance Recharge | Infinite (Increments invoice balance by 3000) | - (Replenishes active transaction balance) |
| **15** | `كود شحن (5000 فاتورة)` | Balance Recharge | Infinite (Increments invoice balance by 5000) | - (Replenishes active transaction balance) |
| **16** | `كود الطوارئ (استعادة وضبط - لمرة واحدة)` | System Unlock | Single-use Reset | Bypass authorization/Emergency settings modification |

### Client-Side Behavior
Upon validation, the client-side UI parses the package characteristics to determine access control. Active base plans (IDs 1–7) are merged to identify the "best" tier. Balance recharge cards (IDs 10–15) accumulate in a single balance pool. If a client is classified as a Cloud Viewer (`is_cloud_viewer=True`), it requires an active online sync license (ID 8 or 9) to operate.

---

## 2. Database Schema

The subsystem maintains separate databases for the licensing server (`LicenseManager`) and the desktop client (`Desktop/sales/salesapp`).

### A. Server-Side Models
Located at `LicenseManager/licenses/models.py` (lines 6–115).

#### `Client` Model (lines 6–18)
Stores client identifying information and hardware registration:
* **`name`** (`CharField`, max_length=100): Client's name.
* **`phone`** (`CharField`, max_length=20): Client's phone number.
* **`machine_id`** (`CharField`, max_length=100, unique=True): Hardware fingerprint.
* **`store_name`** (`CharField`, max_length=100, blank=True, null=True): Name of the retail shop.
* **`is_banned`** (`BooleanField`, default=False): Admin blacklist flag.
* **`created_at`** (`DateTimeField`, auto_now_add=True): Timestamp of registration.

#### `License` Model (lines 20–115)
Tracks individual licenses issued by the administration:
* **`client`** (`ForeignKey` to `Client`, `on_delete=models.CASCADE`): Link to the registered client.
* **`product_id`** (`IntegerField`, choices=PRODUCT_CHOICES): The product type (1-16).
* **`price`** (`IntegerField`, default=0): Amount paid in EGP.
* **`notes`** (`TextField`, blank=True, null=True): Admin secret notes.
* **`start_date`** (`DateField`, default=timezone.now): Subscription start date.
* **`generated_code`** (`CharField`, max_length=20, editable=False): Output activation key (`XXXX-XXXX-XXXX-XXXX`).
* **`is_active`** (`BooleanField`, default=True): Subscription status flag.
* **`created_at`** (`DateTimeField`, auto_now_add=True): Date code was generated.

**Model Properties & Helpers**:
* `is_lifetime` (lines 66-67): Checks if `product_id` is 3 or 7.
* `is_base_plan` (lines 69-71): Checks if `product_id` is between 1 and 7.
* `is_online_product` (lines 73-75): Checks if `product_id` is 8 or 9.
* `is_invoice_based` (lines 77-79): Checks if `product_id` is between 10 and 15.
* `is_emergency_code` (lines 81-83): Checks if `product_id` is 16.
* `get_duration_days()` (lines 85-91): Returns duration days based on `product_id` (Trial=60, Basic=365, VIP=36135).
* `get_expiry_date()` (lines 93-99): Computes final date by adding duration to `start_date` (returns `None` for recharge cards/emergency/lifetime).

### B. Client-Side Models
Located at `Desktop/sales/salesapp/models.py` (lines 474–618).

#### `UsedLicense` Model (lines 474–480)
Acts as a replay-prevention log by caching processed activation key hashes:
* **`code_hash`** (`CharField`, max_length=64, unique=True): SHA-256 hash of the used activation key.
* **`used_at`** (`DateTimeField`, auto_now_add=True): Date and time used.

#### `ClientLicense` Model (lines 482–605)
Caches activated licensing records locally:
* **`product_id`** (`IntegerField`, choices=PRODUCT_CHOICES, default=1): The package ID.
* **`start_date`** (`DateField`): Subscription activation date.
* **`expiry_date`** (`DateField`): Expiration date (or `None` for recharge/lifetime).
* **`invoices_balance`** (`PositiveIntegerField`, default=0): Remaining invoice quota.
* **`is_active`** (`BooleanField`, default=True): Activation status.
* **`machine_id`** (`CharField`, max_length=255): Bound hardware fingerprint.
* **`company_code`** (`CharField`, max_length=10): Online tenant code.
* **`license_code_hash`** (`CharField`, max_length=64): Local cryptographic row signature (prevents DB tampering).
* **`is_online_active`** (`BooleanField`, default=False): Enables online/cloud synchronization features.
* **`online_start_date`** / **`online_expiry_date`** (`DateField`): Boundaries for online sync features.

**Model Properties & Helpers**:
* `is_expired` (lines 516-524): Compares local system date with `expiry_date` (excludes lifetime/recharges).
* `get_active_license()` (lines 526-587): Merges all active licenses in the database into a single composite license object (`merged_license`). It aggregates remaining invoice balances and calculates active subscription boundaries.
* `save()` (lines 592-605): Automatically computes `license_code_hash` by running the record signature algorithm prior to saving.

---

## 3. Cryptographic Code Layout & Generation Protocol

The licensing code generation protocol constructs a dense 80-bit integer block encapsulating the machine fingerprint, start date, and product type, signed via HMAC-SHA256, masked via bitwise XOR operations, and formatted into custom Base32.

```
       80-Bit Integrated Bitwise Layout
 ┌──────────────────────────┬──────────────────────────┐
 │   HMAC-SHA256 Signature  │        Masked Data       │
 │        (36 Bits)         │         (44 Bits)        │
 └─────────────┬────────────┴─────────────┬────────────┘
               │                          │
               └─► Mask Generation ───────┼─► XOR Masking
                   (final_sig Shift/OR)   │
                                          ▼
                                ┌───────────────────┐
                                │ Machine ID Hash   │ (32 Bits)
                                ├───────────────────┤
                                │ Date Code Offset  │ (8 Bits)
                                ├───────────────────┤
                                │ Product ID        │ (4 Bits)
                                └───────────────────┘
```

### A. Cryptographic Key Definitions
The system leverages a shared cryptographic secret to compute row signatures and license codes:
* **Plaintext Secret Key**: `b"JqxQQAKo0BbI76tknaKlhd0rC9hDcam_bqJywXmaXHqAKkVPRZhzgRjHX-zME11enx2oB8o_ivJCn2pXBX-Pow"`
  * Citations: Server-side `LicenseManager/licenses/utils/crypto.py` (line 9).
* **Obfuscated Key Representation**: Loaded at runtime as a list of integer ASCII values:
  * `encrypted_bytes = [74, 113, 120, 81, 81, 65, ...]`
  * Citations: Server-side `LicenseManager/VALIDATOR.py` (lines 20–22), Client-side `Desktop/sales/salesapp/license_validator.py` (lines 20–22).

### B. Bitwise Structural Layout
The custom license code decodes to an **80-bit block** structured as follows:
1. **Signature (`final_sig`)**: Upper 36 bits (bits 44 to 79).
2. **Masked Data (`masked_data`)**: Lower 44 bits (bits 0 to 43).
   * Within the unmasked `data_block` (44 bits):
     * **Machine Hash (`machine_hash`)**: 32 bits (bits 12 to 43).
     * **Date Code (`date_code`)**: 8 bits (bits 4 to 11).
     * **Product ID (`prod_int`)**: 4 bits (bits 0 to 3) representing `product_id - 1`.

### C. Bitwise Masking (XOR Obfuscation)
To hide plain parameters in transit, the lower 44 bits are XOR-masked with a mask generated dynamically from the signature itself:
$$\text{mask} = (\text{final\_sig} \ll 8) \mid (\text{final\_sig} \gg 28)$$
$$\text{masked\_data} = \text{data\_block} \oplus \text{mask}$$

This XOR operation is completely symmetric. On the client, the plaintext data block is restored:
$$\text{data\_block} = \text{masked\_data} \oplus \text{mask}$$

### D. Code Generation Protocol
Implemented in `LicenseManager/licenses/utils/crypto.py` (lines 117–135):
1. **Machine Fingerprinting**: Takes the SHA-256 hash of the `machine_id` string and unpacks the first 4 bytes as a big-endian 32-bit unsigned integer (`machine_int`).
2. **Product ID Encoding**: Maps `product_id` to a 0-indexed value (`product_id - 1`) and applies a `0xF` bitwise mask to isolate 4 bits (`prod_int`).
3. **Date Code Encoding**: Calculates the number of months elapsed since January 2025:
   $$\text{months\_code} = ((\text{year} - 2025) \times 12) + (\text{month} - 1)$$
   The result is capped at 255 (8-bit block).
4. **HMAC Calculation**: Packs the integers into a 6-byte buffer:
   `struct.pack('>IBB', machine_int, prod_int, date_int)`
   Computes the HMAC-SHA256 hash of this buffer using the secret key. Takes the first 8 bytes of the digest and masks it to get the lower 36 bits (`final_sig`).
5. **Assembly**: Shifts the signature and ORs it with the XOR-masked data:
   `full_code_int = (final_sig << 44) | masked_data`
6. **Base32 Formatting**: Encodes the 80-bit integer to a custom Base32 alphabet:
   `CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"`
   *(Excludes confusing characters `I`, `O`, `0`, `1`)*
   Pads the output to 16 characters and formats it as `XXXX-XXXX-XXXX-XXXX`.

---

## 4. Client-Side License Verification & Protection Flows

The client POS application employs local validation checks and a runtime middleware layer to enforce license boundaries and detect database tampering.

### A. Validation Flow (Activation Key Processing)
When the user submits an activation key on the UI (`Desktop/sales/salesapp/views/subscription_views.py`, lines 73–145):
1. **Replay Check**: The key's SHA-256 hash is checked against `UsedLicense` records (lines 80–84). If present, the activation is rejected.
2. **Bitwise Extraction**: The key is sent to `LicenseValidator.validate()`. It converts the string back to the 80-bit integer, extracts the signature, recalculates the XOR mask, unmasks the data block, and parses `machine_hash`, `date_code`, and `product_id`.
3. **HMAC Verification**: The client fetches the obfuscated key bytes, rebuilds the payload, recalculates the HMAC signature, and matches the lower 36 bits against `final_sig` (lines 62–74).
4. **Hardware Binding**: The extracted `machine_hash` is matched against the local system's hardware fingerprint (lines 75–79).
5. **License Persistence**: If all checks pass, the client calculates expiration boundaries and creates a local `ClientLicense` record, saving the raw activation key into `%LOCALAPPDATA%/VentaPOS/license.key` as a hidden/system file.

### B. Runtime Enforcement Middleware
Located at `Desktop/sales/salesapp/middleware.py` (lines 7–106), the middleware runs on every incoming HTTP request:

```
                  Middleware Execution Flow
                    ┌───────────────────┐
                    │  Incoming Request │
                    └─────────┬─────────┘
                              │
                    [Path Static/Admin?]
                     ├─── Yes ───► (Pass Request)
                     └─── No ────► [Session Cache Valid & No Save?]
                                    ├─── Yes ───► (Pass Request)
                                    └─── No ────► [Perform Forensic Check]
                                                   For each active license:
                                                   Recalculate Row HMAC.
                                                   Mismatch? ──► Disable Row
                                                                      │
                                                 ┌────────────────────┘
                                                 ▼
                                           [Time Gate Check]
                                            ├─── Expired ────► Redirect (Activate)
                                            └─── Valid ──────► [Balance Gate Check]
                                                                ├─── Save & Bal <= 0 ──► Block & Redirect
                                                                └─── Pass ─────────────► [Cloud Gate Check]
                                                                                          ├─── Cloud Viewer & Sync Exp ──► Block
                                                                                          └─── Pass ─────────────────────► Pass Request
```

* **Exemptions**: Skip validation for static assets, media files, admin URLs, activation forms, and the subscription dashboard (lines 12–22).
* **Performance Cache**: Employs a 5-minute session cache (`is_licensed` and `last_license_check` session keys). The middleware bypasses database queries if the cache is active, unless the user is saving a receipt.
* **Forensic Verification Check**:
  1. Queries all active license records (`is_active=True`).
  2. For each record, it recalculates the local DB row signature using `generate_record_signature`:
     `expected_sig = generate_record_signature(lic.expiry_date, lic.invoices_balance, machine_id, lic.product_id, lic.is_active)`
  3. If `lic.license_code_hash != expected_sig`, database tampering is detected! The middleware immediately disables the record in the database using `.update(is_active=False)` (lines 58–63) to prevent the `save()` method from automatically rewriting the signature.
* **Security Gates**:
  1. **Time Gate**: Ensures at least one active license is present and not expired (lines 78–80). If missing, redirects to `activate_app`.
  2. **Balance Gate**: If the request is saving a receipt (`/receipts/add/`) and the aggregated invoice balance is `<= 0`, it blocks the transaction and redirects to the subscription dashboard (lines 82–86).
  3. **Cloud Gate**: If the client is configured as a secondary terminal (`is_cloud_viewer=True`), it verifies that the merged license has `is_online_active` set to `True` (lines 88–94). If expired or disabled, it redirects the user to `shutdown_app`.

---

## 5. Quality Audit & Critical Flaws

This section documents the known limitations, security gaps, and backdoor keys identified during the codebase audit.

### A. Trial Period Duration Discrepancy (14 vs. 60 Days)
> [!WARNING]
> There is a conflicting definition of the Trial period duration between the licensing server models and the administration panel configuration:
> * **60-Day Model Specification**: The server-side model (`LicenseManager/licenses/models.py`, line 22/87) defines the label as `"Trial 60 Days"` and its duration in the model's `duration_map` as `60` days. The desktop client mapping (`Desktop/sales/salesapp/views/subscription_views.py`, line 28) also uses a `MONTHS_MAP` value of `2` months (60 days) to configure Trial expiration.
> * **14-Day Admin Panel Mapping**: The Django administration dashboard (`LicenseManager/licenses/admin.py`, line 87) hardcodes the Trial duration as 14 days inside its `duration_map`:
>   ```python
>   duration_map = {
>       1: 14,       # تجربة
>       ...
>   }
>   ```
> * **Impact**: The Django admin panel shows a Trial license as "expired" after 14 days, whereas the desktop client allows it to run for 60 days.

### B. Silent Bypass of Receipt Balance Decrement
* **Location**: `Desktop/sales/salesapp/models.py` (lines 372–396).
* **Vulnerability Description**: The decrement logic resides in the `save()` method of the client-side `Receipt` model. When saving a new receipt, the application queries active licenses with a positive balance. If none are found, the save operation proceeds anyway without raising an error:
  ```python
  if base_license:
      base_license.invoices_balance -= 1
      base_license.save()
  else:
      recharge_code = ClientLicense.objects.filter(...).first()
      if recharge_code:
          recharge_code.invoices_balance -= 1
          recharge_code.save()
      # Loops to the end and saves receipt without decrementing if balance is 0
  ```
* **Impact**: While HTTP views are blocked by the middleware, receipts saved outside typical HTTP controllers (e.g. background sync daemons, direct API calls, shell operations, or test suites) bypass the billing checks completely.

### C. Server-Side Lack of Receipt Hash Validation
* **Location**: `Server/sync_api/views.py` (lines 103–108, 233–247).
* **Vulnerability Description**: During synchronization, the central licensing server reads the `receipt_hash` from the client's payload. The server uses this hash solely for deduplication (`update_or_create`). It does **not** recalculate and verify the hash against the receipt contents using the HMAC secret key.
* **Impact**: Compromised desktop databases can push modified or falsified receipt totals to the cloud server without triggering detection.

### D. Hardcoded Master Developer Key ("Dev2025#Sales")
* **Location**: Defined in `Desktop/sales/salesapp/views/decorators.py` (line 10); referenced in `auth_views.py` (lines 113, 201).
* **Vulnerability Description**: The string `"Dev2025#Sales"` is hardcoded as `DEV_MASTER_KEY`. It allows users to bypass authorization checks on company-protected settings page and reset administrator credentials on the emergency reset page:
  ```python
  if key == DEV_MASTER_KEY:
      admin_user = User.objects.filter(is_superuser=True).first()
      if admin_user:
          admin_user.username = new_username
          admin_user.set_password(new_pass)
          admin_user.save()
  ```
* **Impact**: Significant security backdoor if left in production environments, granting administrative access to anyone knowing the key.

---

## 6. Absolute Source Verification Index

| Target Element | File Path | Line Range | Verbatim Reference / Context |
| :--- | :--- | :--- | :--- |
| **Obfuscated Secret Key (Server)** | `LicenseManager/VALIDATOR.py` | 20–22 | `encrypted_bytes = [74, 113, 120, 81, 81, 65, 75, 111, 48, ...]` |
| **Obfuscated Secret Key (Client)** | `Desktop/sales/salesapp/license_validator.py` | 20–22 | `encrypted_bytes = [74, 113, 120, 81, 81, 65, 75, 111, 48, ...]` |
| **Plaintext Secret Key** | `LicenseManager/licenses/utils/crypto.py` | 9 | `SECRET_KEY = b"JqxQQAKo0BbI76tknaKlhd0rC9hDcam_bqJywXmaXHqAKkVPRZhzgRjHX-zME11enx2oB8o_ivJCn2pXBX-Pow"` |
| **Validation Bitwise Math** | `LicenseManager/licenses/utils/crypto.py` | 64–70 | `final_sig = full_int >> 44`<br>`masked_data = full_int & ((1 << 44) - 1)`<br>`mask = (final_sig << 8) | (final_sig >> 28)`<br>`data_block = masked_data ^ mask` |
| **Row Tamper Check** | `Desktop/sales/salesapp/middleware.py` | 58–63 | `expected_sig = generate_record_signature(...)`<br>`if lic.license_code_hash != expected_sig:`<br>&nbsp;&nbsp;&nbsp;&nbsp;`ClientLicense.objects.filter(pk=lic.pk).update(is_active=False)` |
| **Receipt Decrement Logic** | `Desktop/sales/salesapp/models.py` | 375–396 | Checks for `product_id__lt=10` first, then `product_id__gte=10`, decrements `invoices_balance -= 1` and calls `save()`. |
| **Admin Panel 14-day Discrepancy** | `LicenseManager/licenses/admin.py` | 87 | `1: 14, # تجربة` |
| **Model 60-day Duration** | `LicenseManager/licenses/models.py` | 87 | `1: 60, 2: 365, ...` |
| **Hardcoded Backdoor Key** | `Desktop/sales/salesapp/views/decorators.py` | 10 | `DEV_MASTER_KEY = "Dev2025#Sales"` |
