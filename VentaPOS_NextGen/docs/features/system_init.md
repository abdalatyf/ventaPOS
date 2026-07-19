# System Initialization Documentation

This document outlines the architecture and workflow for the first-time setup wizard in VentaPOS NextGen.

## 1. First-Time Setup Wizard (System Initialization)

The system initialization process sets up the core components necessary for VentaPOS to function locally. This happens when the application is launched for the first time without a valid admin user or license.

### 1.1 Initialization Workflow

- **Endpoint**: `POST /init/` (Mapped to `SystemInitializationView` in `api/views.py`)
- **Frontend Components**: `SystemInit.jsx` and `Setup.jsx`

The user provides the following mandatory data:

| Field | Arabic Label | Description |
| :--- | :--- | :--- |
| `company_name` | اسم الشركة | Company name |
| `branch_name` | اسم الفرع الرئيسي | Default branch name |
| `password` | كلمة سر النظام | Single admin password |
| `license_code` | كود التفعيل | License activation code |
| `phone1` | رقم الهاتف ١ | Primary phone number |
| `phone2` | رقم الهاتف ٢ | Secondary phone number |

### 1.2 Backend Validation and Provisioning

1. **License Validation**: The provided `license_code` is validated against the local machine's `machine_id` using `LicenseValidator`.

2. **Master User Creation**: A single superuser `admin` is created using the provided password.
   - **Recovery Code**: A unique 8-character alphanumeric recovery code (e.g., `VNTA-XXXX-XXXX`) is randomly generated. To avoid database schema changes, the hashed version of this code is stored in the `last_name` field of the user model.

3. **Branch Setup**: A default `Branch` is created with the provided branch name.

4. **License Activation**: A `ClientLicense` record is created.
   - Expiry date is calculated as 1 year from the license start month/year.
   - `invoices_balance` is defaulted to `999999` (unlimited for offline setups).
   - The license is cryptographically signed using `generate_record_signature` to prevent tampering.

> [!NOTE]
> There is **no `Tenant` model** in VentaPOS NextGen. The system is single-tenant — each installation is one company. Company metadata (name, phones) is stored directly on the `Branch` or `CompanySettings` model.

### 1.3 Post-Initialization UI

Upon successful initialization, `SystemInit.jsx` displays the **Recovery Code** to the user. The UI strictly warns the user to save this code, as it serves as the only fallback method for password recovery.

Following the initial setup, users are typically directed to the `Setup.jsx` dashboard which provides quick-access tabs to bootstrap system data:

| Tab | Component | Purpose |
| :--- | :--- | :--- |
| المخزن | `InventoryTab` | Add initial inventory items |
| المناديب | `SalespersonsTab` | Add salespersons |
| الموردين | `SuppliersTab` | Add suppliers |

---

## 2. Smart Import Tool (Excel Data Ingestion)

The Smart Import tool allows users to bulk-import inventory items using Excel files, which is particularly useful for initial system setup.

> [!TIP]
> For full Smart Import documentation including API details and backend processing, see [tools.md](./tools.md#3-أداة-الاستيراد-الذكي-smart-import).

### Quick Reference

- **Endpoint**: `POST /api/v1/tools/smart-import/`
- **Frontend Component**: `SmartImportTab.jsx`
- **Accepted formats**: `.xlsx` or `.xls`

### Expected Excel Columns

| Column Header (Arabic) | Maps To | Required? | Default |
| :--- | :--- | :--- | :--- |
| **اسم الصنف** (Item Name) | `name` | ✅ Yes | (row skipped if empty) |
| **الكمية** (Quantity) | `available_quantity` | No | `0` |

> [!IMPORTANT]
> Smart Import accepts **name and quantity only**. There is no fixed selling price on products in VentaPOS — the cashier enters the price at time of sale. Integer quantities only.

### Processing Logic

- Reads Excel file using `pandas` (`pd.read_excel`)
- Iterates through the DataFrame row by row inside `transaction.atomic()`
- Uses `update_or_create` on the `InventoryItem` model:
  - If an item with the exact name exists in the current branch → updates its quantity
  - Otherwise → creates a new record
