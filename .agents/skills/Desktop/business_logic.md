# Business Logic of Venta POS

## 1. Installment Generation
The system generates installment schedules through precise mathematical calculations originating from a specific anchor date:
- **Receipt Creation (`receipt_views.py`)**:
  - The schedule is parsed from explicit user inputs (`sys1_count`, `sys1_amount`, etc.) or parsed strings to create an array of `installment_amounts`.
  - The `start_date` is strictly anchored to the 25th of the sale's month and year: `start_date = date(sale_year, sale_month, 25)`.
  - For each installment `amount` in `installment_amounts` at index `i` (0-indexed), the `due_date` is computed sequentially as: `due_date = start_date + relativedelta(months=i + 1)`.
  - The total amount of the receipt is dynamically calculated as: `actual_receipt_total = down_payment + sum(installment_amounts)`.
  - `InstallmentPayment` records are created efficiently in memory and inserted into the database using `bulk_create`.

## 2. Commission History (Time Machine)
The system leverages a "Time Machine" architecture to maintain historical accuracy for pricing and sales commissions over time:
- **Data Structure**: Commissions are stored in `CommissionHistory` records linked to `InventoryItem`, defining a `commission_amount` effective from a specific `activation_month` and `activation_year`.
- **Modifications (`inventory_views.py`)**: When updating commissions (`update_commission`), the system uses `update_or_create` targeting the exact month and year. This enables retroactively adjusting past commissions or scheduling future ones without mutating historical data for other periods.
- **Profit Calculation (`product_ledger`)**: 
  - The ledger dynamically queries the active commission unit (`comm_unit`) for a given month via `product.get_commission_at_date(temp_m, temp_y)`.
  - The base item cost is retrieved via `cost_unit = product.get_price_at_date(temp_m, temp_y)`.
  - **Installment Profit Calculation**:
    - Collection Commission (`i_coll_comm`): Calculated dynamically as 10% of the item's proportional value in the installment plan: `(((qty * unit_price) * (total_amount - down_payment) * 0.10) / total_amount)`.
    - Final Installment Profit (`i_profit`): `revenue - (qty * cost_unit) - (qty * comm_unit) - i_coll_comm`.

## 3. The 'Clean Slate' Edit Rule
To avoid complex and error-prone surgical updates to child objects during edits, the system utilizes a strict "clean slate" deletion and recreation strategy:
- **Receipts (`edit_receipt`)**:
  - Validates the new data (including checking backdated safelocks).
  - Wipes existing items: `receipt.items.all().delete()`.
  - Wipes existing installments: `receipt.payments.all().delete()`.
  - Updates the parent `Receipt` object.
  - Re-generates and inserts the new `SaleItem` and `InstallmentPayment` arrays using `bulk_create`.
- **Purchase Invoices (`edit_purchase_invoice`)**:
  - Reverses the historical inventory effects of the old items: if the old type was `PURCHASE`, it subtracts the old quantity from the `InventoryItem`'s total quantity (raising an error if it drops below 0); if `RETURN`, it adds it back.
  - Wipes existing invoice items: `invoice.items.all().delete()`.
  - Updates the parent `PurchaseInvoice` object.
  - Creates new `PurchaseInvoiceItem` records.
  - Applies the new inventory effects (adding quantity for `PURCHASE`, subtracting for `RETURN`) and updates the `purchase_price` of the `InventoryItem`.

## 4. Backdated Safelocks
The system prevents users from making backdated or future-dated sales that would result in negative inventory balances at any point in time:
- **Logic (`get_safe_available_qty` in `utils.py`)**:
  - Defines an iteration boundary from the invoice date (`start_m`, `start_y`) to the default branch date (`end_m`, `end_y`).
  - Iterates through each month in that timeframe.
  - Queries the historical stock for that specific month via `product.get_stock_at_date(m, y)`.
  - **Short-circuiting**: If the stock drops to `<= 0` in any month checked, the function immediately returns `0` (halting the loop).
  - Otherwise, it tracks and returns the absolute minimum stock value (`safe_qty`) found across all evaluated months.
- **Enforcement (`receipt_views.py`)**:
  - During `add_receipt` and `edit_receipt`, the system calls `get_safe_available_qty` to determine the minimum running balance.
  - If the requested sale `quantity` strictly exceeds this `min_future_stock`, a `ValueError` is thrown, blocking the transaction to safeguard inventory integrity.
