---
name: ventapos-mobile
description: Complete technical documentation of the VentaPOS Mobile subsystem, including database schema, client-side routing, screen flows, business rules, and API sync details, fully verified against the source code.
---

# VentaPOS Mobile Subsystem Reference Guide

This document provides a comprehensive technical overview and audit of the offline-first Flutter mobile application (`Mobile/sales_app_offline`) for the VentaPOS ecosystem. It details the client-side SQLite database schema, screen flows, routing architectures, API sync mechanisms, core business rules, and critical synchronization issues uncovered during codebase analysis.

---

## 1. Database Schema

The mobile application utilizes SQLite via the `sqflite` package to implement a **hybrid-offline architecture**. The database helper class is located at:
*   **File Path**: `Mobile/sales_app_offline/lib/db/database_helper.dart` (initializing `mobile_sales_v1.db` at line 23).

The database consists of four core tables defined inside the `_onCreate` method (lines 28–55):

### A. Table: `config`
Stores environmental settings, salesperson identity, and branch identifiers.
*   **Definition (Lines 29–34)**:
    ```sql
    CREATE TABLE config (
      key TEXT PRIMARY KEY,
      value TEXT
    )
    ```
*   **Key Entries**:
    *   `"branch_id"` (Written in line 60): The numeric ID representing the branch.
    *   `"salesperson_id"` (Written in line 64): The numeric ID identifying the active sales representative.
    *   `"base_url"` (Written in line 72): The domain or IP endpoint used for remote API calls.

### B. Table: `inventory`
Stores the local product catalog synchronized from the server/desktop system.
*   **Definition (Lines 36–42)**:
    ```sql
    CREATE TABLE inventory (
      id INTEGER PRIMARY KEY,
      name TEXT,
      code TEXT
    )
    ```
*   **Data Lifecycle**:
    *   During catalog synchronizations, the entire table is wiped and reconstructed in a transaction block via `importProducts(List<dynamic> products)` (Lines 99–111).

### C. Table: `receipts`
Caches created sales invoices locally until they are exported to a central server or local desktop database.
*   **Definition (Lines 44–54)**:
    ```sql
    CREATE TABLE receipts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      composite_key TEXT UNIQUE,
      customer_name TEXT,
      total_amount REAL,
      sale_date TEXT,
      is_exported INTEGER DEFAULT 0,
      json_payload TEXT
    )
    ```
*   **Key Design Aspects**:
    *   `composite_key` (Line 47): Formatted as `SP{salesperson_id}_{timestamp}` (generated at lines 360–361 of `lib/screens/pos_screen.dart`). This avoids primary key collisions when merging receipts from multiple sales reps into the central system.
    *   `json_payload` (Line 52): Contains the complete serialized invoice structure (items, quantities, and installment payments).

### D. Table: `pending_sync_states`
Tracks the sync status of local records with the central server to handle edge cases and retries.
*   **Definition**:
    ```sql
    CREATE TABLE pending_sync_states (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      record_type TEXT,
      record_id INTEGER,
      sync_status TEXT,
      retry_count INTEGER DEFAULT 0,
      last_attempt TEXT
    )
    ```

---

## 2. Screen Flow & Client-Side Routing

The application navigation is coordinated from:
*   **File Path**: `Mobile/sales_app_offline/lib/main.dart`

### A. Right-to-Left (RTL) Localization
*   **Lines 20–22**: To support Arabic RTL layout conventions, the application wraps all page templates inside a RTL Directionality widget:
    ```dart
    builder: (context, child) {
      return Directionality(textDirection: TextDirection.rtl, child: child!);
    }
    ```

### B. Navigation & Smart Bootstrapping
*   **SplashScreen (`lib/main.dart` Lines 28–69)**:
    *   Executes `_checkIdentity()` (lines 41–60) on startup to query `DatabaseHelper().getIdentity()`.
    *   If `salesperson_id == 0`, redirects to `SetupScreen` (lines 50–53) via `Navigator.pushReplacement`.
    *   If `salesperson_id > 0`, redirects to `DashboardScreen` (lines 55–58) via `Navigator.pushReplacement`.

### C. Screen Directory & Triggers
The application defines six screens with the following routing behaviors:

1.  **SetupScreen (`lib/screens/setup_screen.dart`)**:
    *   Onboarding view showing device state. Pushes `QRScannerScreen` (lines 19–24) to scan the activation credentials.
2.  **QRScannerScreen (`lib/screens/qr_scanner_screen.dart` Lines 8–174)**:
    *   *Import Mode* (`isExportMode = false`, lines 85–124): Resolves activation QR, downloads company catalog settings, stores identity data, imports products, and redirects to the Dashboard.
    *   *Export Mode* (`isExportMode = true`, lines 53–84): Submits pending local invoices to the local PC via a HTTP POST request. Marks invoices as exported locally upon success.
3.  **DashboardScreen (`lib/screens/dashboard_screen.dart`)**:
    *   Calls `_loadDashboardData()` (lines 24–34) on load.
    *   Implements **Role-based UI (Manager vs Salesperson)**: Managers see analytics and full sync controls, while Salespersons only see their daily targets and basic pos tools.
    *   Uses a circular badge indicator showing the pending receipt count. The gradient shifts dynamically: Orange/Red if `count > 0`, and Green/Teal if `count == 0` (lines 88–91).
    *   Pushes to `PosScreen` (lines 118–136), `ReceiptsArchiveScreen` (lines 139–165), or `ProductsScreen` (lines 168–190).
4.  **PosScreen (`lib/screens/pos_screen.dart` Lines 5–824)**:
    *   Implements the **Accordion POS wizard** for a streamlined, step-by-step checkout experience (Customer Info -> Cart -> Payment).
    *   Handles checkout calculations. If an invoice is edited, triggers `_loadExistingData()` (lines 77–117) and reverse-parses the installment string using RegExp `(\d+)\s*\*\s*(\d+)` (lines 119–158) to reconstruct form controllers.
5.  **ProductsScreen (`lib/screens/products_screen.dart` Lines 4–76)**:
    *   Renders local `inventory` rows in a list (lines 45–73) queried from `DatabaseHelper().searchProducts("")`.
6.  **ReceiptsArchiveScreen (`lib/screens/receipts_archive_screen.dart` Lines 11–793)**:
    *   Archive interface containing filtering logic (lines 56–106).
    *   Provides three export options: Cloud Sync (`_pushToCloudSelected`, lines 108–163), Local File Share (`_exportSelected`, lines 180–246), or USB QR Sync (`_exportViaUSB`, lines 248–274).

---

## 3. API Sync & Request Flows

### A. Base URL Resolver
*   **File Path**: `Mobile/sales_app_offline/lib/services/api_service.dart` (Lines 23–31).
*   Cleans and prefix-normalizes the base URL, dynamically appending target sync endpoints (e.g. `http://{baseUrl}/api/v1/sync/mobile-push/`).

### B. Client-Server API Sync Matrix

| API Operation | Protocol | Mobile Source | Server/Desktop Target Endpoint | Payload Structure |
| :--- | :--- | :--- | :--- | :--- |
| **Local Setup (Offline)** | GET | `qr_scanner_screen.dart` (Line 89) | Desktop: `local_setup_api` (`sync_views.py` Line 231) | URL Query: `?token={token}&sp_id={sp_id}` |
| **Local Push (Offline)** | POST | `qr_scanner_screen.dart` (Line 65) | Desktop: `local_push_api` (`sync_views.py` Line 264) | `{"token": String, "sp_id": int, "receipts": [...]}` |
| **Online Setup (Cloud)** | GET | `qr_scanner_screen.dart` (Line 93) | Server: `DownloadSetupView` (`views.py` Line 378) | URL Query: `?token={token}` |
| **Online Push (Cloud)** | POST | `api_service.dart` (Line 33) | Server: `MobilePushIngestView` (`views.py` Line 206) | `{"meta": {...}, "payload": {"receipts": [...]}}` |

---

## 4. Core Business Rules

### A. Calculations & Totals
Calculated inside `PosScreen._calculateTotals()` (lines 167–192 of `lib/screens/pos_screen.dart`):
*   `_totalItemsPrice` = Sum of all `quantity * unitPrice` in the cart.
*   `_totalPaid` (Installment mode) = `downPayment + (Months1 * Amount1) + (Months2 * Amount2) + (Months3 * Amount3)`.

### B. Bill Balance Validation
*   **Rule (Lines 388–393 of `pos_screen.dart`)**:
    *   Determines discrepancy: `double difference = (_totalItemsPrice - _totalPaid).abs();`
    *   **Tolerance Policy (Official Resolution)**: Strict corporate guidelines enforce a **5.0** tolerance range (i.e. `difference <= 5.0` instead of the legacy `1.0` limit).

### C. Invoice JSON Serialization
*   **Rule (Lines 279–343 of `pos_screen.dart`)**:
    *   Constructs standard maps with client details, cart arrays, down payments, and serialized schedules.
    *   Stores the plan summary as a readable formula under `"installment_system"` (e.g. `"1000*3 + 500*2"`).

### D. Hardcoded Installment Due Date
*   **Installment Schedule Policy (Official Resolution)**: Corporate accounting policy strictly dictates a fixed monthly billing schedule. Custom negotiating is disabled. Installments must be generated on the **25th of every month** (rather than the legacy 15th).
    *   Legacy: `DateTime startDate = DateTime(_selectedYear, _selectedMonth, 15);` (Line 306)
    *   Resolution: Documented and enforced as the **25th of the month**.

---

## 5. Quality Audit & Architectural Resolutions

### ⚠️ Sync Bug 1: Online Setup Activation Payload Nesting Crash
*   **Conflict Location**: `qr_scanner_screen.dart` (Lines 101–103) vs Server `sync_api/views.py` (Line 393)
*   **Mechanism**: The central Django server outputs the token configuration inside a nested key:
    ```python
    return JsonResponse({'status': 'success', 'payload': payload})
    ```
    However, the mobile app decodes the response body and directly scans the root namespace:
    ```dart
    Map<String, dynamic> setupData = jsonDecode(response.body);
    if (setupData.containsKey('branch_id')) ...
    ```
*   **Impact**: Setup checks fail to locate key variables, throwing `Exception: Invalid setup data format` and halting activation.
*   **Resolution**: Mobile JSON parser must extract variables from `setupData['payload']` when fetching setup settings.

### ⚠️ Sync Bug 2: Missing `machine_id` in Cloud Push
*   **Conflict Location**: `receipts_archive_screen.dart` (Lines 128–135) vs Server `sync_api/views.py` (Line 210) & Desktop `sync_views.py` (Line 174)
*   **Mechanism**: The server endpoint `MobilePushIngestView` expects `machine_id` at the root of the JSON payload. The mobile app exports payload nested within `"meta"` and `"payload"`, neglecting to supply `machine_id` at the root.
*   **Impact**:
    1.  The API request throws a `403 Forbidden` unauthorized error on the server because `ServerLicense` cannot be authenticated without a valid `machine_id`.
    2.  If bypassed, the record's source machine is logged as `NULL`. When the Desktop app attempts to download pending invoices from the server (`/api/v1/sync/pending-receipts/?machine_id=...`), these records are never fetched due to ID mismatch.
*   **Resolution**: Ensure the mobile app attaches the registered `machine_id` at the root level of the Cloud Push payload.

### ⚠️ Sync Bug 3: Inconsistent Database Key Mapping (Installments Dropped)
*   **Conflict Location**: `pos_screen.dart` (Lines 202–207, 330) vs Desktop `sync_views.py` (Lines 507–512)
*   **Mechanism**: The mobile app packages the installment payment array under `"payments"`, using `"date"` as the nested timestamp variable:
    ```dart
    payments.add({"date": payDate.toString(), "amount": a});
    receiptJson["payments"] = payments;
    ```
    However, the Desktop approval endpoint expects the key `"installments"` and nested `"payment_date"` variables:
    ```python
    for inst in data.get('installments', []):
        InstallmentPayment.objects.create(payment_date=inst.get('payment_date'), ...)
    ```
*   **Impact**: The Desktop stages the invoices, but upon approval, the entire installment schedule is silently stripped, writing a blank installment plan.
*   **Resolution**: Update the mobile serialization to output `"installments"` list with `"payment_date"`, matching the Desktop target keys.

### ⚠️ Sync Bug 4: Cloud Push Staging Strips Critical Data Details
*   **Conflict Location**: Server `sync_api/views.py` (Lines 218–242)
*   **Mechanism**: The server-side ingestion handler `MobilePushIngestView` hardcodes cash flags and product names for incoming records:
    ```python
    'is_cash_sale': True,
    'product_name_snapshot': 'Cloud Item'
    ```
*   **Impact**: Syncing installment transactions to the cloud strips their payment structures and details, converting them into basic cash sales of "Cloud Item".
*   **Resolution**: Refactor the server-side view to ingest detailed item lists, down payments, and installment lists directly from the mobile payload.

### ⚙️ Business Logic Resolutions

1.  **POS Tolerance Limit constraint**:
    *   *Resolution*: The corporate model enforces strict payments matching total items price within a **5.0** range. Separate interest fields are omitted. The legacy `1.0` threshold in `pos_screen.dart` (Line 392) must be widened to `5.0`.
2.  **Hardcoded Installment Start Date (15th of the Month)**:
    *   *Resolution*: Reps are prohibited from negotiating custom installment due dates. The payment schedule must begin and execute on a fixed monthly date of the **25th of every month**. `pos_screen.dart` (Line 306) must be documented as utilizing the 25th as the default accounting calendar standard.
