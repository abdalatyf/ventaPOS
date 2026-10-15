# Server Application - Database Schema Memory

This document contains a hyper-detailed, exhaustive record of every single model, table, and state entity found in the VentaPOS Server application (`D:\Projects\VentaPOS\Server\sync_api\models.py`).

## 1. ServerLicense
**Description**: Security Gate / License control table to verify machines allowed to sync.
**Fields**:
- `machine_id`: `CharField` (max_length=255, unique=True, verbose_name="بصمة الجهاز") - The unique hardware footprint.
- `client_name`: `CharField` (max_length=150, verbose_name="اسم العميل", blank=True)
- `is_active`: `BooleanField` (default=True, verbose_name="مسموح له بالمزامنة؟")
- `created_at`: `DateTimeField` (auto_now_add=True)
- `last_sync_at`: `DateTimeField` (null=True, blank=True, verbose_name="آخر مزامنة")
**Methods**:
- `__str__(self)`: returns `f"{self.client_name} ({self.machine_id})"`

## 2. ServerCompanySetting
**Description**: Company Settings for a specific client machine.
**Fields**:
- `source_machine_id`: `CharField` (max_length=255, db_index=True)
- `local_id`: `IntegerField` (default=1) - Typically only 1 row, but keeps consistency with local syncing.
- `name`: `CharField` (max_length=100, verbose_name="اسم الشركة")
- `description`: `CharField` (max_length=200, blank=True, null=True)
- `phone1`: `CharField` (max_length=20)
- `phone2`: `CharField` (max_length=20, blank=True, null=True)
- `footer_text`: `CharField` (max_length=250, blank=True, null=True)
- `synced_at`: `DateTimeField` (auto_now=True)
**Meta constraints**: 
- `unique_together = ('source_machine_id', 'local_id')`
- `verbose_name = "إعدادات شركة عميل"`

## 3. ServerBranch
**Description**: Branches for a given source machine.
**Fields**:
- `source_machine_id`: `CharField` (max_length=255, db_index=True)
- `local_id`: `IntegerField` (verbose_name="ID الفرع المحلي")
- `name`: `CharField` (max_length=150)
- `synced_at`: `DateTimeField` (auto_now=True)
**Meta constraints**: 
- `unique_together = ('source_machine_id', 'local_id')`

## 4. ServerSalesperson
**Description**: Salespersons tied to a machine and branch.
**Fields**:
- `source_machine_id`: `CharField` (max_length=255, db_index=True)
- `local_id`: `IntegerField` (verbose_name="ID الموظف المحلي")
- `local_branch_id`: `IntegerField` (verbose_name="ID فرع الموظف")
- `name`: `CharField` (max_length=100)
- `synced_at`: `DateTimeField` (auto_now=True)
**Meta constraints**: 
- `unique_together = ('source_machine_id', 'local_id')`

## 5. ServerInventoryItem
**Description**: Inventory/Products.
**Fields**:
- `source_machine_id`: `CharField` (max_length=255, db_index=True)
- `local_id`: `IntegerField` (verbose_name="ID المنتج المحلي")
- `local_branch_id`: `IntegerField` (verbose_name="ID المخزن")
- `name`: `CharField` (max_length=200)
- `quantity`: `PositiveIntegerField` (default=0)
- `purchase_price`: `DecimalField` (max_digits=12, decimal_places=2, default=0) - Converted to Decimal for Server precision.
- `salesperson_commission_amount`: `DecimalField` (max_digits=12, decimal_places=2, default=0)
- `created_at_local`: `DateTimeField` (null=True, blank=True)
- `synced_at`: `DateTimeField` (auto_now=True)
**Meta constraints**: 
- `unique_together = ('source_machine_id', 'local_id')`

## 6. ServerReceipt
**Description**: Invoices and sales receipts.
**Fields**:
- `source_machine_id`: `CharField` (max_length=255, db_index=True)
- `local_id`: `IntegerField` (verbose_name="ID الفاتورة المحلي")
- `receipt_number`: `PositiveIntegerField`()
- `local_branch_id`: `IntegerField`()
- `local_salesperson_id`: `IntegerField` (null=True, blank=True)
- `customer_name`: `CharField` (max_length=200, blank=True)
- `phone_number`: `CharField` (max_length=50, blank=True)
- `address`: `CharField` (max_length=255, blank=True)
- `area`: `CharField` (max_length=150, blank=True)
- `total_amount`: `DecimalField` (max_digits=12, decimal_places=2, default=0)
- `down_payment`: `DecimalField` (max_digits=12, decimal_places=2, default=0)
- `installment_system`: `CharField` (max_length=255, blank=True)
- `sale_year`: `IntegerField`()
- `sale_month`: `IntegerField`()
- `is_cash_sale`: `BooleanField` (default=False)
- `products_text`: `TextField` (blank=True, null=True)
- `synced_at`: `DateTimeField` (auto_now_add=True)
- `created_at_local`: `DateTimeField` (null=True, blank=True)
**Meta constraints**: 
- `unique_together = ('source_machine_id', 'local_id')`
- `ordering = ['-created_at_local']`

## 7. ServerSaleItem
**Description**: Sale items (Receipt details).
**Fields**:
- `receipt`: `ForeignKey` (to `ServerReceipt`, related_name='items', on_delete=models.CASCADE)
- `local_product_id`: `IntegerField`()
- `product_name_snapshot`: `CharField` (max_length=255)
- `quantity`: `PositiveIntegerField`()
- `unit_price`: `DecimalField` (max_digits=12, decimal_places=2)

## 8. ServerInstallmentPayment
**Description**: Installments tied to a receipt.
**Fields**:
- `receipt`: `ForeignKey` (to `ServerReceipt`, related_name='payments', on_delete=models.CASCADE)
- `payment_date`: `DateField`()
- `amount`: `DecimalField` (max_digits=12, decimal_places=2)

## 9. ServerExpense
**Description**: Expenses records.
**Fields**:
- `source_machine_id`: `CharField` (max_length=255, db_index=True)
- `local_id`: `IntegerField` (verbose_name="ID المصروف المحلي")
- `local_branch_id`: `IntegerField`()
- `amount`: `DecimalField` (max_digits=12, decimal_places=2)
- `description`: `CharField` (max_length=255)
- `expense_year`: `IntegerField`()
- `expense_month`: `IntegerField`()
- `created_at_local`: `DateTimeField` (null=True, blank=True)
- `synced_at`: `DateTimeField` (auto_now_add=True)
**Meta constraints**: 
- `unique_together = ('source_machine_id', 'local_id')`

## 10. ServerStockTransaction
**Description**: Inventory stock transactions.
**Fields**:
- `source_machine_id`: `CharField` (max_length=255, db_index=True)
- `local_id`: `IntegerField` (verbose_name="ID الحركة المحلي")
- `local_product_id`: `IntegerField`()
- `product_name_snapshot`: `CharField` (max_length=255, blank=True)
- `transaction_type`: `CharField` (max_length=50)
- `quantity`: `IntegerField`()
- `created_at_local`: `DateTimeField` (null=True, blank=True)
- `synced_at`: `DateTimeField` (auto_now_add=True)
**Meta constraints**: 
- `unique_together = ('source_machine_id', 'local_id')`
