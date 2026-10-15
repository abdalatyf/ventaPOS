# LicenseManager - Core Business Logic

This document details the exact mathematical steps, core algorithms, data transformations, and state management workflows of the LicenseManager application.

## 1. License Generation Algorithm (`crypto.py`)
The application generates a highly secure, machine-tied 16-character license key formatted as `XXXX-XXXX-XXXX-XXXX`.

### Steps:
1.  **Machine Hashing**:
    *   Input: `machine_id` string.
    *   Function: Computes `SHA256(machine_id)`.
    *   Extraction: Takes the first 4 bytes and unpacks them as a big-endian unsigned integer to create a 32-bit `machine_int`.
2.  **Product ID Transformation**:
    *   Input: `product_id` (1 to 16).
    *   Function: `(product_id - 1) & 0xF`.
    *   Result: A 4-bit `prod_int` (0 to 15).
3.  **Date Encoding**:
    *   Input: `start_date` object.
    *   Base Year: `2025`.
    *   Function: Calculates `year_diff = max(start_date.year - 2025, 0)`.
    *   Months Code: `months_code = (year_diff * 12) + (start_date.month - 1)`.
    *   Result: Bounded 8-bit `date_int` (min of `months_code` or `255`).
4.  **Signature Payload Structure**:
    *   Packs `machine_int` (4 bytes), `prod_int` (1 byte), and `date_int` (1 byte) into a 6-byte structure `>IBB` (Big-Endian: Unsigned Int, Unsigned Char, Unsigned Char).
5.  **Signature Generation (HMAC)**:
    *   Function: Computes `HMAC-SHA256` of the payload using a hardcoded `SECRET_KEY`.
    *   Extraction: Takes the first 8 bytes of the HMAC output and unpacks them as an unsigned long long (`>Q`).
    *   Masking: Keeps only the lowest 36 bits: `final_sig = sig_int & ((1 << 36) - 1)`.
6.  **Data Block Assembly**:
    *   Combines the data into a 44-bit block: `data_block = (machine_int << 12) | (date_int << 4) | prod_int`.
7.  **Data Masking (XOR)**:
    *   Creates a mask from the signature: `mask = (final_sig << 8) | (final_sig >> 28)`.
    *   Function: `masked_data = data_block ^ mask`.
8.  **Final Integer Assembly**:
    *   Combines the 36-bit signature and 44-bit masked data into an 80-bit integer: `full_code_int = (final_sig << 44) | masked_data`.
9.  **Custom Base32 Encoding**:
    *   Charset: `"ABCDEFGHJKLMNPQRSTUVWXYZ23456789"` (Omits confusing characters like I, O, 1, 0).
    *   Divides `full_code_int` by 32 repeatedly, taking the remainder as the index for the charset.
    *   Pads the resulting string to exactly 16 characters with the 0th character (`'A'`).
    *   Formats the output as `XXXX-XXXX-XXXX-XXXX`.

---

## 2. License Validation Algorithm (`crypto.py` & `VALIDATOR.py`)
Validates a given code against a specific machine.

### Steps:
1.  **Code Normalization & Decoding**:
    *   Removes hyphens and converts to uppercase.
    *   Validates characters against the `CHARSET`.
    *   Converts the Base32 string back to the 80-bit `full_int`.
2.  **Extraction & Unmasking**:
    *   Extracts `final_sig = full_int >> 44`.
    *   Extracts `masked_data = full_int & ((1 << 44) - 1)`.
    *   Reconstructs the `mask` (same logic as generation) and XORs with `masked_data` to get `data_block`.
3.  **Data Deconstruction**:
    *   `extracted_prod = data_block & 0xF`.
    *   `extracted_date_code = (data_block >> 4) & 0xFF`.
    *   `extracted_machine_hash = (data_block >> 12) & 0xFFFFFFFF`.
4.  **Cryptographic Verification**:
    *   Recreates the 6-byte payload using the extracted data.
    *   Computes the HMAC-SHA256 signature using the `SECRET_KEY` (or obfuscated byte array in the client validator).
    *   Extracts the 36-bit signature.
    *   **Rule**: If the calculated signature != `final_sig`, return `Valid: False` (Forged Code).
5.  **Machine Verification**:
    *   Hashes the provided `machine_id` via SHA256, taking the first 4 bytes as a 32-bit int.
    *   **Rule**: If the calculated machine hash != `extracted_machine_hash`, return `Valid: False` (Code not for this machine).
6.  **Human Data Reconstruction**:
    *   `year = BASE_YEAR + (extracted_date_code // 12)`.
    *   `month = (extracted_date_code % 12) + 1`.
    *   `real_product_id = extracted_prod + 1`.

---

## 3. Key Obfuscation Workflow (`obfuscate_key.py`)
To protect the `SECRET_KEY` inside client applications, it is not stored as a string.
1.  Reads the 64-character secret string.
2.  Converts the string into a list of UTF-8 byte integers (e.g., `'J'` -> 74, `'q'` -> 113).
3.  The client validator (`VALIDATOR.py`) reconstructs the bytes directly from this integer array in memory during validation, preventing simple string extraction attacks.

---

## 4. State Management and Dashboard Logic (`views.py`)

### Authentication State
*   A very simple session-based authentication is used.
*   **Login**: Checks if the submitted `password` matches `settings.MASTER_PASSWORD`. If true, sets `request.session['is_logged_in'] = True`.
*   **Logout**: Sets `request.session['is_logged_in'] = False`.
*   **Middleware/Decorator Alternative**: All protected views manually call `is_authenticated(request)` which returns the session value. If False, redirects to `login`.

### Dashboard Aggregations
*   **Global Stats**:
    *   Total Clients: `Client.objects.count()`.
    *   Active Licenses: `License.objects.filter(is_active=True).count()`.
    *   Total Revenue: Sum of `price` across all licenses.
*   **Monthly Stats**:
    *   Calculated by filtering `created_at__gte=current_month_start`.
*   **"Expiring Soon" Logic**:
    *   Iterates over all active licenses.
    *   Calculates `days_left = (lic.get_expiry_date() - today).days`.
    *   If `0 <= days_left <= 30`, the client and license data are appended to the `expiring_soon_list` to be shown on the dashboard.
