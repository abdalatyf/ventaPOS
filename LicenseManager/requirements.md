# VentaPOS License Manager — Architecture & Functional Requirements Specification

> **Supreme SSoT**: [`../APP_BIBLE.md`](../APP_BIBLE.md) · **Governance Rules**: [`../.agents/rules/rules.md`](../.agents/rules/rules.md)  
> **Single Source of Truth (SSoT)** for the VentaPOS License Generation & Client Management Subsystem.  
> **Target Version**: 1.0.0 (Synchronized with VentaPOS NextGen Core)  
> **Compatibility**: Fully compatible with `VentaPOS_NextGen.api.utils.license_validator.LicenseValidator`

---

## 1. Application Overview & Purpose

`LicenseManager` is an internal, vendor-facing back-office Django application used exclusively by the software owner / administrator to issue, track, and manage cryptographic activation and password recovery keys for client installations of **VentaPOS NextGen**.

### Core Responsibilities
1. **Client Registry & Fail-Closed Online Marketeer Auth**: Maintains a local SQLite registry (`%APPDATA%\VentaPOS_LicenseManager\db.sqlite3` when frozen) of client stores, customer contact details, assigned hardware machine IDs, and blacklist status. Operator login (`login_view`) enforces **fail-closed online authentication** via Supabase RPC `verify_marketeer_login` against `public.marketeer_users` (`SECURITY DEFINER`, `pgcrypto`); offline login is blocked.
2. **80-Bit Key Synthesis & Mandatory Fail-Closed Cloud Audit**: Generates cryptographically verifiable 80-bit activation codes (`XXXX-XXXX-XXXX-XXXX`) that **client desktops (`VentaPOS_NextGen`) can validate offline**, while **`LicenseManager` itself enforces fail-closed online append-only cloud logging** (`POST /rest/v1/licenses` on Supabase `public.licenses`, protected by RLS + `trg_prevent_license_tamper` blocking `UPDATE`/`DELETE`) before committing any key to local SQLite. Offline key generation is strictly blocked. *(Reconciliation note: Prior specs claimed offline generation on both sides; `LicenseManager` requires active internet and valid `SUPABASE_URL`/`SUPABASE_KEY`.)*
3. **Emergency Password Recovery**: Generates one-time emergency master unlock codes (`product_id = 16`, `is_recovery=True`) allowing clients locked out of their desktop installations to reset the admin password via `/api/v1/auth/recover/`.
4. **WhatsApp Communication Dispatch**: Prepares instant, localized Arabic WhatsApp fulfillment messages containing customer credentials, package details, expiration dates, and activation keys.

---

## 2. Cryptographic 80-Bit Key Specification

VentaPOS NextGen enforces an offline, 80-bit compact binary payload designed for manual transcription by business owners via phone, WhatsApp, or SMS.

### 2.1 Character Set & Encoding (Custom Base32)
- **Alphabet**: 32 human-friendly ASCII characters excluding confusing glyphs (`0`, `O`, `1`, `I`):
  ```python
  CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
  ```
- **Length**: Exactly 16 characters partitioned into 4-character chunks:
  $$\text{Format} = \texttt{XXXX-XXXX-XXXX-XXXX}$$
- **Bit Capacity**: $16 \text{ chars} \times 5 \text{ bits/char} = 80 \text{ bits}$ ($10 \text{ bytes}$).

### 2.2 Shared Secret Key & Obfuscation
Both the `LicenseManager` generator and the desktop `VentaPOS_NextGen` validator share an identical 64-byte cryptographic secret:
- **Raw ASCII Bytes**:
  ```python
  SECRET_KEY = b"JqxQQAKo0BbI76tknaKlhd0rC9hDcam_bqJywXmaXHqAKkVPRZhzgRjHX-zME11enx2oB8o_ivJCn2pXBX-Pow"
  ```
- **Byte Array Obfuscation** (embedded in client runtime to resist naive string searches):
  ```python
  [74, 113, 120, 81, 81, 65, 75, 111, 48, 66, 98, 73, 55, 54, 116, 107, 110, 97, 75, 108, 104, 100, 48, 114, 67, 57, 104, 68, 99, 97, 109, 95, 98, 113, 74, 121, 119, 88, 109, 97, 88, 72, 113, 65, 75, 107, 86, 80, 82, 90, 104, 122, 103, 82, 106, 72, 88, 45, 122, 77, 69, 49, 49, 101, 110, 120, 50, 111, 66, 56, 111, 95, 105, 118, 74, 67, 110, 50, 112, 88, 66, 88, 45, 80, 111, 119]
  ```

### 2.3 Bit Layout & Architecture (80 Bits Total)
The 80-bit integer (`full_code_int`) is structured as two primary components:
$$\text{Bit 79} \dots \text{Bit 44} \quad (36 \text{ bits}) \quad \mid \quad \text{Bit 43} \dots \text{Bit 0} \quad (44 \text{ bits})$$

```
+------------------------------------+---------------------------------------------+
|    36-Bit HMAC Signature Digest    |          44-Bit XOR-Masked Payload          |
|         (Bits 44..79)              |                 (Bits 0..43)                |
+------------------------------------+---------------------------------------------+
                                     | Machine Hash (32b) | Date Code (8b) | Prod (4b)|
                                     |    (Bits 12..43)   |  (Bits 4..11)  | (Bits 0..3)
```

1. **Payload Block (44 bits)**:
   - **`machine_int` (Bits 12..43, 32 bits)**:
     $$\text{machine\_int} = \text{unpack}('>I', \text{SHA256}(\text{machine\_id})[:4])[0]$$
     Extracted from the 32-character SHA-256 hardware machine ID.
   - **`date_int` (Bits 4..11, 8 bits)**:
     $$\text{date\_int} = \min\left(255, \, (\text{year} - 2025) \times 12 + (\text{month} - 1)\right)$$
     Encodes month and year starting from base epoch `2025-01-01` (supports 256 months = 21.3 years, up to late 2046).
   - **`prod_int` (Bits 0..3, 4 bits)**:
     $$\text{prod\_int} = (\text{product\_id} - 1) \ \& \ \texttt{0xF}$$
     Encodes product tier `1` through `16` ($0 \dots 15$).

2. **Signature Block (36 bits)**:
   - Formed by packing payload components into big-endian network bytes:
     $$\text{payload\_bytes} = \text{struct.pack}('>IBB', \text{machine\_int}, \text{prod\_int}, \text{date\_int})$$
   - Hashed using HMAC-SHA256 with `SECRET_KEY`:
     $$\text{sig\_int} = \text{unpack}('>Q', \text{HMAC}(\text{SECRET\_KEY}, \text{payload\_bytes})[:8])[0]$$
     $$\text{final\_sig} = \text{sig\_int} \ \& \ ((1 \ll 36) - 1)$$

3. **Reversible XOR Rotational Mask**:
   To prevent plain data inspection, the 44-bit payload is masked using a pseudo-random bit rotation of the 36-bit signature:
   $$\text{mask} = (\text{final\_sig} \ll 8) \mid (\text{final\_sig} \gg 28)$$
   $$\text{masked\_data} = \text{data\_block} \oplus \text{mask}$$
   $$\text{full\_code\_int} = (\text{final\_sig} \ll 44) \mid \text{masked\_data}$$

---

## 3. Product Packages & Quota Alignment Matrix

### 3.1 Business Quota Constants
- **Standard Sales Volume Rate**: **400 invoices / month**
- **Free Trial Package (`product_id = 1`)**: **800 invoices total (60 Days / 2 Months)**
- **Annual Standard Package (`product_id = 2` & `4`)**: **4,800 invoices / year** (`400/month × 12 months`; reconciled from earlier `5,000` draft estimate)
- **Multi-Year Packages**: `product_id = 5` (3 Years) = **14,400** (`400 × 36`); `product_id = 6` (5 Years) = **24,000** (`400 × 60`)
- **Lifetime Packages (`product_id = 3` & `7`)**: **999,999 invoices** (99 years)

### 3.2 Product ID Mapping Table

| `product_id` | `prod_int` | Arabic Plan Name | Duration | Invoice Quota | Purpose in VentaPOS NextGen |
| :---: | :---: | :--- | :---: | :---: | :--- |
| **`1`** | `0` | تجربة مجانية (Trial 60 Days) | 60 Days (2 Months) | **800** | Initial customer trial before purchasing. |
| **`2`** | `1` | طباعة فقط - سنة واحدة | 1 Year (12 Months) | **4,800** | Print-Only Basic Mode (receipt CRUD & printing only). |
| **`3`** | `2` | طباعة فقط - مدى الحياة | Lifetime (99 Years) | **999,999** | Print-Only Basic Mode lifetime license. |
| **`4`** | `3` | إدارة كاملة - سنة واحدة | 1 Year (12 Months) | **4,800** | **Flagship Standard Production License**. |
| **`5`** | `4` | إدارة كاملة - 3 سنوات | 3 Years (36 Months) | **14,400** | Multi-year full management bundle. |
| **`6`** | `5` | إدارة كاملة - 5 سنوات | 5 Years (60 Months) | **24,000** | Multi-year enterprise full management bundle. |
| **`7`** | `6` | إدارة كاملة - مدى الحياة (VIP) | Lifetime (99 Years) | **999,999** | VIP unlimited full management license. |
| **`8`** | `7` | إضافة الأونلاين - سنة | 1 Year | — | Cloud sync add-on (deprecated; hidden in `LicenseForm`). |
| **`9`** | `8` | إضافة الأونلاين - 5 سنوات | 5 Years | — | Cloud sync add-on (deprecated; hidden in `LicenseForm`). |
| **`10`** | `9` | كود شحن (100 فاتورة) | None (Balance Top-up) | **100** | Top-up invoice refill code (`TOPUP_MAP[10]`). |
| **`11`** | `10` | كود شحن (300 فاتورة) | None (Balance Top-up) | **300** | Top-up invoice refill code (`TOPUP_MAP[11]`). |
| **`12`** | `11` | كود شحن (500 فاتورة) | None (Balance Top-up) | **500** | Top-up invoice refill code (`TOPUP_MAP[12]`). |
| **`13`** | `12` | كود شحن (1,000 فاتورة) | None (Balance Top-up) | **1,000** | Top-up invoice refill code (`TOPUP_MAP[13]`). |
| **`14`** | `13` | كود شحن (3,000 فاتورة) | None (Balance Top-up) | **3,000** | Top-up invoice refill code (`TOPUP_MAP[14]`). |
| **`15`** | `14` | كود شحن (5,000 فاتورة) | None (Balance Top-up) | **5,000** | Top-up invoice refill code (`TOPUP_MAP[15]`, **not** recovery). |
| **`16`** | `15` | كود استعادة كلمة المرور للمدير (طوارئ) | One-Time Use | — | **Emergency Admin Password Reset Code** (`is_recovery=True`). |

> [!NOTE]
> **Reconciliation Note (`product_id` 15 vs 16 & Quotas)**: In `VentaPOS_NextGen/backend/api/views/license_views.py` and `auth_views.py`, **`product_id = 15`** is strictly the `+5,000` invoice top-up package (`TOPUP_MAP[15] = 5000`), while **`product_id = 16`** (`is_recovery=True`) is strictly the one-time Emergency Admin Password Recovery code (rejected by `LicenseActivateView` and handled exclusively by `PasswordRecoveryView`). Earlier draft docs incorrectly wrote `product_id in (15, 16)` for recovery and rounded annual/multi-year quotas to `5,000` / `15,000` / `25,000` / `Unlimited`; actual `LicenseActivateView` grants `800`, `4,800`, `14,400`, `24,000`, and `999,999`.

---

## 4. Hardware Machine ID Binding

- **Format**: 32-character hexadecimal string representing the first 32 characters of the SHA-256 digest of the client machine's hardware GUID:
  ```
  Example: 5410972688ec8bb4e16d99723ecdbf7a
  ```
- **Validation**:
  - `LicenseManager` MUST validate that entered `machine_id` values are valid 32-character hexadecimal strings (allowing clean whitespace stripping and case normalization).
  - Legacy disk IDs (`DISK-5822-S9J1`) are obsolete and replaced by NextGen 32-char hex IDs.

---

## 5. Compatibility Contract with VentaPOS NextGen

1. **Deterministic Bi-directional Verification**:
   Any code generated by `LicenseGenerator.generate(machine_id, product_id, start_date)` MUST pass validation in `VentaPOS_NextGen.api.utils.license_validator.LicenseValidator.validate(code, machine_id)`.
2. **First Activation Data Wipe Guard**:
   When activating a new client license on a Demo machine, NextGen wipes the demo database. Subsequent renewals or top-ups with the same machine ID retain all production data.
3. **Grace Period Consistency**:
   A 1-year license (`product_id=4`) with start date `2026-01-01` allows invoices for months `01-2026` through `12-2026`. NextGen permits invoice creation until `2027-01-25`.
4. **Replay Attack Immunity**:
   Once activated in NextGen, the SHA-256 hash of the 16-character code is stored in `UsedLicense` and permanently rejected on subsequent attempts.

---

## 6. Functional & UI Workflows

1. **Dashboard & Analytics (`/dashboard/`)**:
   - Total clients count, active licenses count, and cumulative revenue.
   - Monthly performance metrics (new clients, monthly license count, and monthly gross revenue).
   - "Expiring Soon" watchlist identifying clients whose subscriptions expire within 30 days.
2. **Client Management (`/clients/`, `/clients/add/`)**:
   - Register client name, contact phone, store/business name, and hardware Machine ID.
   - Blacklist toggle (`is_banned`) to flag compromised or malicious machines.
3. **License Generation (`/licenses/add/`)**:
   - Form fields: Client selection, Product Package dropdown, Price, Start Date (calendar date picker), and Private Notes.
   - Immediate generation of the 16-character key on record save.
4. **Fulfillment Screen (`/licenses/success/<id>/`)**:
   - Displays the generated code formatted with prominent copy-to-clipboard functionality.
   - Pre-generated one-click WhatsApp dispatch link with personalized Arabic customer message.
