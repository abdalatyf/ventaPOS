# Licensing & Security Architecture

This document is the authoritative specification for VentaPOS NextGen's cryptographic licensing system, row-level tamper protection, and password recovery mechanism.

---

## 1. The Obfuscated Secret Key

The HMAC signing key is stored as an array of ASCII codes to prevent plain-text scanning in source control or decompiled binaries.

### ASCII Code Representation

```python
SECRET_KEY_BYTES = [
    74, 113, 120, 81, 81, 65, 75, 111, 48, 66, 98, 73, 55, 54, 116, 107,
    110, 97, 75, 108, 104, 100, 48, 114, 67, 57, 104, 68, 99, 97, 109, 95,
    98, 113, 74, 121, 119, 88, 109, 97, 88, 72, 113, 65, 75, 107, 86, 80,
    82, 90, 104, 122, 103, 82, 106, 72, 88, 45, 122, 77, 69, 49, 49, 101,
    110, 120, 50, 111, 66, 56, 111, 95, 105, 118, 74, 67, 110, 50, 112, 88,
    66, 88, 45, 80, 111, 119
]
```

### Plaintext Equivalent

```python
SECRET_KEY = b"JqxQQAKo0BbI76tknaKlhd0rC9hDcam_bqJywXmaXHqAKkVPRZhzgRjHX-zME11enx2oB8o_ivJCn2pXBX-Pow"
```

---

## 2. Key Alphabet & Bitwise Layout

### Character Set (Custom Base32)

```python
CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
```

- 32 characters (5 bits each)
- Excludes ambiguous characters: `0`, `1`, `I`, `O`
- Keys are presented to users as: `XXXX-XXXX-XXXX-XXXX` (16 data characters = 80 bits)

### 80-Bit Integrated Bitwise Layout

```
      ┌──────────────────────────────┬──────────────────────────────┐
      │   HMAC-SHA256 Signature      │        Masked Data           │
      │        (36 Bits)             │         (44 Bits)            │
      └─────────────┬────────────────┴─────────────┬────────────────┘
                    │                              │
                    └─► Mask Generation ───────────┼─► XOR Masking
                        (final_sig Shift/OR)       │
                                                   ▼
                                         ┌───────────────────┐
                                         │ Machine ID Hash   │ (32 Bits)
                                         ├───────────────────┤
                                         │ Date Code Offset  │ (8 Bits)
                                         ├───────────────────┤
                                         │ Product ID        │ (4 Bits)
                                         └───────────────────┘
```

| Field             | Bit Width | Bit Range   | Description                                    |
|:------------------|:----------|:------------|:-----------------------------------------------|
| HMAC Signature    | 36 bits   | `[79:44]`   | Lower 36 bits of HMAC-SHA256 digest            |
| Machine ID Hash   | 32 bits   | `[43:12]`   | SHA-256 of hardware UUID, truncated to 4 bytes |
| Date Code Offset  | 8 bits    | `[11:4]`    | Months since January 2025                      |
| Product ID        | 4 bits    | `[3:0]`     | License tier index (`prod_int + 1`)            |

---

## 3. Decrypting & Validation Pipeline

The validation logic is implemented in `license_validator.py` and executes the following 6-step pipeline:

### Step 1: Custom Base32 → Integer

Convert the 16-character key string (after stripping dashes) back to an 80-bit integer:

```python
def _custom_base32_to_int(key_str):
    result = 0
    for ch in key_str:
        result = result * 32 + CHARSET.index(ch)
    return result  # → full_int (80 bits)
```

### Step 2: Bitwise Separation

```python
final_sig   = full_int >> 44                   # Top 36 bits (HMAC signature)
masked_data = full_int & ((1 << 44) - 1)       # Bottom 44 bits (encrypted payload)
```

### Step 3: XOR Mask Resolution

The mask is derived symmetrically from the signature bits:

$$\text{mask} = \left(\text{final\_sig} \ll 8\right) \;\big|\; \left(\text{final\_sig} \gg 28\right) \pmod{2^{44}}$$

```python
mask = ((final_sig << 8) | (final_sig >> 28)) & ((1 << 44) - 1)
```

### Step 4: Payload Extraction

Restore the cleartext data block and extract individual fields:

```python
data_block = masked_data ^ mask

prod_int     = data_block & 0xF                    # 4 bits  → product_id = prod_int + 1
date_code    = (data_block >> 4) & 0xFF            # 8 bits  → months since Jan 2025
machine_hash = (data_block >> 12) & 0xFFFFFFFF     # 32 bits → hardware binding
```

### Step 5: Signature Verification (HMAC-SHA256)

Pack the extracted fields in big-endian format and compute the HMAC:

```python
import struct, hmac, hashlib

payload = struct.pack('>IBB', machine_hash, prod_int, date_code)  # 6 bytes
computed_hmac = hmac.new(SECRET_KEY, payload, hashlib.sha256).digest()
computed_sig  = int.from_bytes(computed_hmac[:5], 'big') & ((1 << 36) - 1)

assert computed_sig == final_sig  # Mismatch → INVALID key
```

### Step 6: Hardware & Expiry Checks

**Machine Binding:**

```python
machine_hash_expected = struct.unpack('>I', hashlib.sha256(machine_id.encode()).digest()[:4])[0]
assert machine_hash == machine_hash_expected  # Mismatch → wrong machine
```

**Date Decoding:**

$$\text{start\_year} = 2025 + \lfloor\text{date\_code} / 12\rfloor$$
$$\text{start\_month} = 1 + (\text{date\_code} \bmod 12)$$

**Expiry Check:** Look up the product duration and verify the current date is within range.

---

## 4. Product IDs & Durations

| Product ID | Plan Name   | Duration     | Notes                            |
|:-----------|:------------|:-------------|:---------------------------------|
| 1          | Trial       | 60 days      | Limited evaluation period        |
| 2          | Basic       | 365 days     | Standard annual subscription     |
| 3+         | Lifetime    | 36,135 days  | ~99 years; effectively permanent |
| 10+        | Recharge    | —            | Invoice balance top-up cards     |
| 16         | Emergency   | —            | Recovery / emergency code        |

> [!NOTE]
> `product_id` values < 10 are base subscription licenses. Values ≥ 10 are recharge/utility codes. The Receipt `save()` override decrements the base license balance first, then falls back to recharge codes.

---

## 5. Row-Level Tamper Protection

### 5.1 Record Signature Algorithm

For each row in `ClientLicense`, the system calculates a cryptographic integrity hash:

$$\text{license\_code\_hash} = \text{HMAC-SHA256}\left(\text{expiry\_date},\; \text{invoices\_balance},\; \text{machine\_id},\; \text{product\_id},\; \text{is\_active}\right)$$

- Computed using the system's obfuscated secret key.
- The `ClientLicense.save()` override automatically recalculates this hash on every write via `generate_record_signature()`.

### 5.2 Middleware Verification

The `LicenseEnforcementMiddleware` performs forensic verification on every non-static HTTP request:

1. **Query** all active licenses (`is_active=True`).
2. **Recalculate** the record signature for each row.
3. **Compare** the stored `license_code_hash` against the freshly computed value.
4. **If mismatch (tampering detected)**:
   ```python
   # Bypass save() to prevent hash auto-recalculation during emergency deactivation
   ClientLicense.objects.filter(pk=lic.pk).update(is_active=False)
   ```

> [!CAUTION]
> The middleware deliberately uses `.update()` instead of `.save()` to prevent the `save()` override from silently recalculating the hash during emergency deactivation.

### 5.3 Performance Optimization

To avoid heavy database checks on every request, the middleware caches the license validation result in the Django session:

```python
request.session['is_licensed'] = True
# Re-checked only if > 5 minutes have elapsed since last check
# Receipt-save requests always bypass the cache
```

---

## 6. Recovery Code

### 6.1 Overview

The Recovery Code provides a mechanism for the admin to reset their password if they forget it. It is generated once during system initialization and displayed to the admin for safekeeping.

> [!IMPORTANT]
> **Current Implementation Note**: In the current codebase, the recovery code is generated as a random string (`VNTA-XXXX-XXXX`) and stored as a hashed value in the admin user's `last_name` field to avoid database migrations. The architectural target is to store it as a **special license type** in the `client_license` table (product_id = 16, the Emergency Code tier). See Section 6.3 for the target architecture.

### 6.2 Current Implementation

During `SystemInitializationView.post()`:

```python
recovery_code = f"VNTA-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"

# Stored as bcrypt hash in user.last_name
user.last_name = make_password(recovery_code)
user.save()
```

**Password Recovery Flow** (`POST /api/v1/auth/recover/`):

1. Admin submits `recovery_code` + `new_password`.
2. Backend retrieves the superuser and calls `check_password(recovery_code, admin_user.last_name)`.
3. If valid → `admin_user.set_password(new_password)`.

### 6.3 Target Architecture (License-Based Recovery)

The planned architecture stores the recovery code as a special license entry:

1. **During System Init**: A `ClientLicense` row is created with `product_id = 16` (Emergency Code). The license code field stores the recovery code value.
2. **During Password Recovery**: The user enters their recovery code. The `LicenseValidator` confirms it as a valid product_id = 16 license bound to the current machine.
3. **Advantages**: Eliminates the `last_name` field hijack, integrates recovery into the existing licensing infrastructure, and benefits from row-level tamper protection (HMAC signature).

---

## 7. Machine ID Binding

### 7.1 Hardware UUID

The machine identity is derived from the hardware's unique identifier:

```python
# api/utils/security_utils.py
def get_machine_id():
    """Returns the unique hardware UUID for the local machine."""
    import subprocess
    output = subprocess.check_output(
        'wmic csproduct get uuid', shell=True
    ).decode()
    return output.strip().split('\n')[-1].strip()
```

### 7.2 Machine Hash Derivation

The 32-bit machine hash embedded in license keys is computed as:

```python
import struct, hashlib

raw_hash = hashlib.sha256(machine_id.encode()).digest()[:4]  # First 4 bytes
machine_hash = struct.unpack('>I', raw_hash)[0]              # Big-endian uint32
```

This hash is:
- **Encoded into every generated license key** (32 bits in the data block).
- **Verified at activation time** against the local machine's computed hash.
- **Prevents license portability** — a key generated for Machine A will fail validation on Machine B.

---

## Related Documents

- [Settings & Security](../features/settings_and_security.md) — Password management and admin security
- [Data Models](04_data_models.md) — `ClientLicense`, `UsedLicense`, `LicenseHistory` table schemas
