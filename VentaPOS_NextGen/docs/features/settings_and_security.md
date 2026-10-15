# Settings and Security

This document outlines the architecture, data models, and API interactions for the Settings module in VentaPOS NextGen, covering Company Settings, Security (Password Management), and Subscription Licensing.

## 1. Company Settings (`CompanyTab.jsx`)

### Overview
The **CompanyTab** allows administrators to define the core identity of the business, which is reflected across receipts, reports, and the UI.

### Data Model
- **Table**: `company_setting` (Mapped to the `CompanySetting` Django Model)
- **Architecture**: Implemented as a *Singleton*. Since the system is single-tenant, there is exactly one `CompanySetting` record.
- **Fields**:
  - `name`: Business Name.
  - `description`: Subtitle or business activity description.
  - `phone1`, `phone2`: Contact numbers.
  - `footer_text`: A unified message printed at the bottom of thermal receipts.

### API Integration
- **Endpoint**: `/api/company-settings/` (Handled by `CompanySettingViewSet`)
- **Flow**:
  1. `GET /api/company-settings/`: The frontend fetches the active company profile.
  2. `PATCH /api/company-settings/{id}/`: The frontend sends the updated fields. This relies on the standard `SoftDeleteModelViewSet`.
  3. Updates are immediately reflected locally in `localStorage` for fast UI rendering (e.g., `company_name`).

## 2. Security & Account (`SecurityTab.jsx`)

### Overview
The **SecurityTab** provides a secure mechanism for the store administrator to update their master password and manage recovery codes.

### Security Mechanisms
- VentaPOS NextGen uses a robust local authentication architecture tailored for offline-first operations.
- The system identifies the single local administrator by looking for `is_superuser=True` in the Django `User` table.
- Changing the password requires the user to successfully validate the **Old Password** before applying the new hash.

### API Integration (Password Change)
- **Endpoint**: `POST /api/auth/change-password/` (Handled by `ChangePasswordView`)
- **Payload**:
  ```json
  {
      "old_password": "current_password",
      "new_password": "secure_new_password"
  }
  ```
- **Flow**:
  1. The backend searches for the superuser.
  2. Uses `check_password(old_password)` to securely verify the existing credentials.
  3. If valid, uses `set_password(new_password)` to hash and save the new credential securely in the SQLite database.

### Recovery Code Mechanism
If the administrator forgets their password, they can use a **Recovery Code**.
- The Recovery Code is generated during the initial System Setup.
- It is created and validated as a **Special License Type** stored in the `client_license` table (using the same 80-bit cryptographic system as standard licenses).
- At the password recovery screen, the user inputs the recovery code. The backend uses the `LicenseValidator` to ensure the code is valid and of the "Recovery" type before allowing a password reset.

## 3. Subscription & Licenses (`SubscriptionTab.jsx`)

### Overview
The **SubscriptionTab** acts as the gateway to the VentaPOS Licensing service. It tracks the physical machine signature and validates the current billing state (expiry dates and invoice quota).

> **Note:** For the full cryptographic specification, 80-bit layout, and validation pipeline, see the [Licensing Specification](../architecture/05_licensing.md).

### Data Model
- **Tables**: `client_license`, `used_license`, `license_history`
- **Machine Identification**: The system generates a unique, immutable physical fingerprint using `api.utils.security_utils.get_machine_id()`. This prevents license spoofing or unauthorized duplication of the POS software.

### API Integration
- **Endpoints**:
  - `GET /api/license/status/`: Fetches the current license state.
  - `POST /api/license/activate/`: Submits a prepaid license key for activation.
  
- **Data Returned**:
  ```json
  {
      "status": "active",
      "total_invoices_balance": 1500,
      "expiry_date": "2026-12-31",
      "machine_id": "8F3A9C-D7E1B2-..."
  }
  ```
- **Flow**:
  1. On component mount, the frontend fetches `/api/license/status/` to populate the dashboard metrics (Days remaining, Status, Machine ID).
  2. When a user inputs a new code, it is sent to `/api/license/activate/`.
  3. The backend securely checks the `ClientLicense` and `UsedLicense` tables to ensure the code hasn't been redeemed. Upon successful validation, the new expiry and invoice quota are applied.
