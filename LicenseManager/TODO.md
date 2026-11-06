# VentaPOS License Manager — Master Task & Roadmap Tracker

> **Anchors**: `requirements.md` (Domain Specifications & Cryptographic Contract)  
> **Status Notation**: `[ ]` = Pending · `[/]` = In Progress · `[x]` = Verified & Done  

---

## Priority 0 — Critical Compatibility & Cryptographic Sync Fixes

- [x] **P0.1 — Machine ID 32-Character Hex Validation (`ClientForm`)**:
  - `licenses/forms.py` (`ClientForm`):
    - Clean and validate `machine_id` to ensure it is a valid 32-character hexadecimal string (`^[a-fA-F0-9]{32}$`).
    - Auto-strip leading/trailing whitespace and convert to lowercase.
    - Reject obsolete legacy hardware formats (e.g., `DISK-5822-S9J1`) to eliminate customer rejection upon entry.

- [x] **P0.2 — Emergency Password Recovery Product ID Alignment (`LIC-05` / `SEC-01`)**:
  - `licenses/models.py`:
    - Confirm `product_id=16` ('كود استعادة كلمة المرور للمدير (طوارئ)') as the standard Emergency Password Recovery package.
    - Ensure `VentaPOS_NextGen` validator recognizes both `15` and `16` for backwards compatibility while `LicenseManager` explicitly labels `16` as "كود استعادة كلمة المرور للمدير (طوارئ)".

- [x] **P0.3 — VentaPOS NextGen `product_id` Quota & Duration Mapping (`LIC-05`)**:
  - `VentaPOS_NextGen/backend/api/views/license_views.py` (`LicenseActivateView`):
    - Implement the confirmed quota and duration mapping table:
      - `product_id=1` (Trial 60 Days): Duration 2 months, `invoices_balance = 800`.
      - `product_id in (2, 4)` (1 Year): Duration 12 months, `invoices_balance = 4800`.
      - `product_id=5` (3 Years): Duration 36 months, `invoices_balance = 14400`.
      - `product_id=6` (5 Years): Duration 60 months, `invoices_balance = 24000`.
      - `product_id in (3, 7)` (Lifetime): Duration 99 years, `invoices_balance = 999999`.
      - `product_id in (10..15)` (Top-up): Add balance (`100`, `300`, `500`, `1000`, `3000`, `5000`) to existing active license balance without overwriting subscription expiry date.

- [x] **P0.4 — Mandatory Supabase Append-Only Cloud Logging (`Item 17`)**:
  - Connect `LicenseManager` to `https://tgfhyyfwgcvotxfwbnhd.supabase.co`.
  - Block offline license generation: require a successful HTTP `201 Created` `POST` to Supabase `/rest/v1/licenses` before saving locally or displaying any generated key.
  - Enforce append-only storage in `supabase_schema.sql` via Supabase RLS (`INSERT` and `SELECT` only) + a PostgreSQL trigger blocking `UPDATE` and `DELETE`.

---

## Priority 1 — Business Rules & UI/Workflow Alignment

- [x] **P1.1 — Deprecate Unused Cloud Products (`product_id=8, 9`)**:
  - `licenses/models.py` (`PRODUCT_CHOICES`):
    - Mark `product_id=8` and `product_id=9` as deprecated or hide them from the `LicenseForm` dropdown since VentaPOS NextGen operates strictly offline without cloud sync.

- [x] **P1.2 — 1-Click Clipboard Copy on Fulfillment Screen**:
  - `licenses/templates/license_success.html`:
    - Add a JavaScript copy-to-clipboard button next to the 16-character code with visual confirmation ("تم النسخ بنجاح!").

- [x] **P1.3 — WhatsApp Template Modernization**:
  - `licenses/views.py` (`license_success_view`):
    - Update WhatsApp message template to include clear step-by-step instructions for the business owner:
      1. فتح البرنامج والدخول إلى الإعدادات $\rightarrow$ الاشتراك.
      2. نسخ أو كتابة الكود في خانة التفعيل.
      3. الضغط على "تفعيل البرنامج".

---

## Priority 2 — Security, Code Quality & Automated Tests

- [x] **P2.1 — Automated Test Suite (`test_license_manager.py`)**:
  - Implemented 9/9 passing parity tests verifying bi-directional key generation and validation against `VentaPOS_NextGen.LicenseValidator`, hardware binding, date codes, tamper rejection, and recovery codes.

- [x] **P2.2 — Master Password Security Hardening**:
  - `core/settings.py`:
    - Read `MASTER_PASSWORD` from environment variable (`os.environ.get('VENTA_LICENSE_MASTER_PASSWORD', '...')`), falling back to a secure default rather than plain `'123'`.

- [x] **P2.3 — Client Blacklist Enforcement**:
  - `licenses/views.py` (`add_license_view`):
    - Prevent issuing new licenses to clients marked with `is_banned=True` unless explicitly unbanned.
