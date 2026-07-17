# Procurement & Supplier Management (المشتريات والموردين)

## Overview
The Procurement module in VentaPOS NextGen handles the complete purchasing lifecycle, from managing supplier profiles to recording purchase invoices and factory returns. It directly impacts inventory stock levels and average cost calculations.

## 1. Supplier Management
Suppliers are the source of inventory items. They are managed through a standard CRUD interface:
- **API Endpoint:** `GET`, `POST`, `PUT`, `DELETE` at `/api/suppliers/`
- **Architecture:** Inherits from `SoftDeleteModelViewSet`. Suppliers are never permanently deleted from the database to preserve historical invoice integrity.

## 2. Purchasing Flow (`PurchaseEntry.jsx`)
The `PurchaseEntry` screen allows users to record new incoming stock or outgoing returns.

### Invoice Types
- **PURCHASE (شراء):** Represents new stock entering the warehouse from a supplier.
- **RETURN (مرتجع):** Represents damaged or unsold stock returned to the supplier (مرتجع مصنع).

### Data Structure & Submission
When saving an invoice, the frontend constructs a payload encompassing the header details and an array of items, sending it to `POST /api/purchase-invoices/`:
```json
{
  "supplier": 1,
  "invoice_type": "PURCHASE",
  "invoice_month": 7,
  "invoice_year": 2026,
  "items": [
    {
      "inventory_item": 15,
      "quantity": 10,
      "purchase_price": 120.5
    }
  ]
}
```

## 3. Impact on Inventory Stock
Purchases and returns automatically dynamically affect the inventory ledger evaluated at runtime (as seen in `InventoryItemViewSet.ledger`):
- **PURCHASE:** 
  - **Quantity:** Increases the `current_qty` of the inventory item.
  - **Cost:** Recalculates the item's average cost using a weighted average formula based on the previous stock value and the new incoming quantity and price.
- **RETURN:** 
  - **Quantity:** Decreases the `current_qty` of the item.
  - **Cost:** The total value of the returned goods is subtracted from the total inventory value, maintaining an accurate ongoing average cost.

## 4. Searching and Managing Invoices (`SearchPurchases.jsx`)
The `SearchPurchases` screen provides a comprehensive ledger for all procurement activities:
- **Filtering:** Users can filter invoices by invoice type, number, month, year, and specific supplier.
- **Pagination & Aggregation:** The backend (`PurchaseInvoicePagination`) returns paginated results alongside real-time aggregated totals (`total_purchases`).
- **Bulk Actions:** Supports selecting multiple invoices for bulk deletion.
- **Printing:** Invoices can be printed or viewed as PDFs. Due to the offline-first architecture, the frontend calls the `/api/purchase-invoices/desktop_print/` endpoint, which utilizes `os.startfile` to open local PDF readers (like SumatraPDF) natively.
- **Soft Deletes:** Deleting an invoice performs a soft-delete (setting `is_deleted=True`), ensuring that financial records can be audited if necessary.
