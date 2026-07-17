# System Initialization & Admin Tools

This document outlines the first-time setup process, the smart import tool for bulk data entry, and the system auditing logs in VentaPOS NextGen.

## 1. System Initialization Wizard (`SystemInit.jsx`)

The system initialization process is triggered when the system is run for the very first time. It ensures that critical business information and the master license are configured before any user can log in.

### First-Time Configuration Flow
1. **Redirection:** If the backend `/api/init/` endpoint indicates `initialized: false`, the user is directed to the `/init` route (`SystemInit.jsx`).
2. **Form Data Collection:** The wizard collects:
   - **License Code:** The master activation key.
   - **Company Name:** Appears on receipts and the application header.
   - **Password:** The master system password.
   - **Branch Name:** The initial/main branch for operations.
   - **Contact Details (Phone 1 & 2):** Optional contact numbers for the main branch.
3. **Submission:** Data is POSTed to `/api/init/`. 
4. **Recovery Code:** The backend responds with a unique `recovery_code`. The wizard displays this code with a critical warning (⚠️) asking the user to save it securely, as it is the only way to recover a lost master password.
5. **Completion:** Upon confirmation, the user is redirected to the `/login` screen.

## 2. Base Entity Setup (`Setup.jsx`)

After initialization, the user can navigate to the Setup section to configure the foundational entities required for POS operations.

The setup screen features a tabbed interface (Secondary Navbar) for managing:
- **Inventory (الأصناف):** Default and primary tab, utilizing `InventoryTab.jsx`.
- **Salespersons (المناديب):** Utilizing `SalespersonsTab.jsx`.
- **Suppliers (الموردين):** Utilizing `SuppliersTab.jsx`.

These components provide data grids and modals for CRUD operations on the core business objects.

---

## 3. Smart Import Tool (`SmartImportTab.jsx`)

The Smart Import Tool allows administrators to rapidly populate the database by uploading a single Excel file containing items, customers, and starting debts.

### Workflow
1. **File Selection:** The user selects an `.xlsx` or `.xls` file.
2. **Upload:** The file is sent via `multipart/form-data` to `/api/v1/tools/smart-import/`.
3. **Progress Tracking:** The UI displays a simulated progress bar during the upload and processing phase to improve perceived performance.
4. **Feedback:** Upon completion, a success or error message is displayed based on the backend response.

### Excel File Format Rules
While the backend handles the parsing logic, the expected Excel structure typically requires:
- Specific sheet names or a unified flat structure (depending on backend implementation).
- Columns for Item Name, Barcode, Purchase Price, Selling Price, and Category.
- The system handles the batch insertion atomically to prevent partial imports if an error occurs.

---

## 4. System Action Logs (`LogsTab.jsx`)

The Action Logs feature provides an audit trail of sensitive operations performed within the system.

### Details
- **Endpoint:** Fetches data from `/api/v1/action-logs/`.
- **Data Displayed:**
  - **Timestamp:** Formatted to the local Arabic timezone (`ar-EG`).
  - **Action Type:** A categorized badge (e.g., Update, Delete, Import).
  - **Details:** A descriptive text of what exactly was changed.
  - **User:** The name of the user who performed the action (defaults to "مدير النظام" for the admin).
- **Functionality:** Includes a manual refresh button to fetch the latest logs without reloading the page.
