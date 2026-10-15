# Server Application - Routing & UI Architecture Memory

This document maps the URL routing patterns and UI architecture for the VentaPOS Server application. 

## Architectural Overview
The Server application is designed strictly as a **Headless API Server and Administrative Backend**. It does not contain a custom frontend component tree, React/Vue/Flutter layouts, or custom HTML templates. 

The entire UI is auto-generated using the **Django Admin interface**, leveraging the model definitions and ModelAdmins defined in `admin.py`.

## Routing Topology

### 1. Root Router (`server_backend/urls.py`)
- **`/admin/`** -> Routes to `admin.site.urls` (The UI Portal).
- **`/`** -> Routes to `sync_api.urls` (The API Portal).

### 2. Sub-Router (`sync_api/urls.py`)
- **`/api/v1/sync/push/`** -> Routes to `SyncIngestView.as_view()` (No UI, JSON response only).

## UI Component Hierarchy (Django Admin)
The user interface is entirely managed via `sync_api/admin.py`. Below is the layout hierarchy configured for the administrators:

### A. License Management UI
- **Model**: `ServerLicense`
- **List Display**: Client Name, Machine ID, Is Active, Last Sync At, Created At
- **Filters**: Is Active status
- **Search**: Machine ID, Client Name

### B. Reference Data UIs
- **Company Settings**: Displays Name, Phone, Source Machine ID.
- **Branches**: Displays Name, Local ID, Source Machine ID.
- **Salespersons**: Displays Name, Local ID, Branch ID, Source Machine ID. Filters available by Machine ID and Branch.
- **Inventory**: Displays Name, Quantity, Purchase Price, Machine ID, Branch ID. Filters by Machine and Branch.

### C. Transactional UIs
- **Receipts (Invoices)**: 
  - **List Display**: Receipt Number, Customer Name, Total Amount, Source Machine ID, Local Creation Date.
  - **Filters**: Machine ID, Is Cash Sale, Sale Year, Sale Month.
  - **Hierarchy/Nesting (Inlines)**: 
    - Within the Receipt detail view, the UI nests a `SaleItemInline` (Tabular) to show the purchased products.
    - It also nests a `PaymentInline` (Tabular) to show installment payments.
  - **Constraints**: Historical transactional fields are marked `readonly_fields` to prevent accidental administrative tampering with synced financial data.

- **Expenses**: 
  - **List Display**: Description, Amount, Year, Month, Source Machine ID.
  - **Filters**: Machine ID, Expense Year.

- **Stock Transactions**:
  - **List Display**: Transaction Type, Product Name, Quantity, Source Machine ID.
  - **Filters**: Machine ID, Transaction Type.
