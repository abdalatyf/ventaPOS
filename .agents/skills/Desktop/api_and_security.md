# API and Security 

## 1. Hardware ID Binding Flow
The Hardware ID binding process ensures that a license code is exclusively tied to a specific machine.
1. **Extraction of Hardware ID**:
   - `security_utils.py -> get_machine_id()` uses a cascade of three methods to retrieve a unique machine ID:
     1. **WMIC**: `wmic csproduct get uuid`
     2. **PowerShell**: `(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID`
     3. **Registry**: `SOFTWARE\Microsoft\Cryptography\MachineGuid`
     4. **Fallback**: `"UNKNOWN-ID-999"`
2. **Hashing Machine ID**:
   - `LicenseValidator._get_machine_hash(machine_id)` takes the retrieved `machine_id`, hashes it using `hashlib.sha256(machine_id.encode()).digest()`, and extracts the first 4 bytes using `struct.unpack('>I', raw_hash[:4])[0]` as an unsigned integer.
3. **License Validation**:
   - `LicenseValidator.validate(license_code, machine_id)` is invoked with the user-provided code and the machine ID.
   - The license code is decoded using a custom Base32 charset to a large integer.
   - The integer is bit-shifted to separate the signature and the masked data block.
   - A bitwise XOR is used to unmask the data block.
   - `extracted_machine_hash` is isolated from the unmasked data block (bits 12 to 43).
   - The extracted hash is compared with the current machine's hash (`current_machine_hash = cls._get_machine_hash(machine_id)`).
   - If they do not match, validation fails with the error `"هذا الكود غير مخصص لهذا الجهاز"` (This code is not meant for this device).

## 2. Encryption/Decryption Process for Backups and Databases (AES/Fernet)
- **Current State**: AES or Fernet encryption is **not implemented** for backups or databases in the current codebase.
- **Backup Flow (`backup_views.py -> download_backup`)**:
  - The default database path is retrieved from `settings.DATABASES['default']['NAME']`.
  - A hot backup is created directly as a plain SQLite file using `sqlite3.connect(db_path).backup(dest_conn, pages=100, sleep=0.01)`.
  - The plain `.sqlite3` file is served to the user for download via `FileResponse`.
- **Restore Flow (`backup_views.py -> restore_backup`)**:
  - The user uploads a plain `.sqlite3` or `.db` file.
  - The uploaded file is saved in chunks as `restore_pending.bin` in the `LOCALAPPDATA\VentaPOS` directory.
  - No AES/Fernet decryption is performed upon upload or restoration.
- **Database File**: The main SQLite database is not encrypted at rest. Data integrity against tampering is managed through HMAC-SHA256 signatures (`generate_record_signature` and `generate_receipt_signature` in `security_utils.py` using a runtime-only `SECRET_DB_KEY`), but the raw data itself is stored in plain text without AES/Fernet.

## 3. Role-Based Decorators
The application utilizes the following decorators for access control and authorization:

1. **`@login_required(login_url='login')`**:
   - **Source**: `django.contrib.auth.decorators`
   - **Usage**: Used in `subscription_views.py` (`subscription_dashboard`) and `backup_views.py` (`download_backup`, `restore_backup`).
   - **Purpose**: Ensures that only authenticated users can access the respective views. Redirects to the login URL if unauthenticated.

2. **`@branch_required`**:
   - **Source**: `salesapp.views.decorators`
   - **Usage**: Added to views to ensure the user has selected an active branch.
   - **Purpose**: Checks `request.session.get('selected_branch_id')`. If missing or invalid, it redirects the user to `select_branch`. It fetches the corresponding `Branch` object and attaches it to `request.branch` for use within the view.

3. **`@pro_plan_required`**:
   - **Source**: `salesapp.views.decorators`
   - **Usage**: Guards views and features that belong exclusively to the "Pro" plan.
   - **Purpose**: Validates that `ClientLicense.get_active_license()` returns a license with a `product_id` of `1` (Trial), `4` (Pro 1-yr), `5` (Pro 3-yr), `6` (Pro 5-yr), or `7` (Lifetime Unlimited). Users on basic plans are blocked and redirected to `dashboard` with a warning message.