from django.contrib import admin
from .models import (
    ServerLicense, ServerReceipt, ServerSaleItem, ServerInstallmentPayment,
    ServerBranch, ServerInventoryItem, ServerExpense, ServerStockTransaction,
    ServerSalesperson, ServerCompanySetting
)

# 1. إعدادات الترخيص
@admin.register(ServerLicense)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'machine_id', 'is_active', 'last_sync_at', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('machine_id', 'client_name')
    readonly_fields = ('machine_id',)

# 2. إعدادات الشركة
@admin.register(ServerCompanySetting)
class CompanySettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone1', 'source_machine_id', 'synced_at')
    list_filter = ('source_machine_id',)
    search_fields = ('name', 'source_machine_id')

# 3. الفروع
@admin.register(ServerBranch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'local_id', 'source_machine_id', 'synced_at')
    list_filter = ('source_machine_id',)
    search_fields = ('name',)

# 4. الموظفين
@admin.register(ServerSalesperson)
class SalespersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'local_id', 'local_branch_id', 'source_machine_id')
    list_filter = ('source_machine_id', 'local_branch_id')
    search_fields = ('name',)

# 5. المخزون (المنتجات)
@admin.register(ServerInventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'purchase_price', 'source_machine_id', 'local_branch_id')
    list_filter = ('source_machine_id', 'local_branch_id')
    search_fields = ('name',)

# 6. الفواتير وتفاصيلها (استخدام Inlines)
class SaleItemInline(admin.TabularInline):
    model = ServerSaleItem
    extra = 0
    can_delete = False
    readonly_fields = ('local_product_id', 'product_name_snapshot', 'quantity', 'unit_price')

class PaymentInline(admin.TabularInline):
    model = ServerInstallmentPayment
    extra = 0
    can_delete = False
    readonly_fields = ('payment_date', 'amount')

@admin.register(ServerReceipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'customer_name', 'total_amount', 'source_machine_id', 'created_at_local')
    list_filter = ('source_machine_id', 'is_cash_sale', 'sale_year', 'sale_month')
    search_fields = ('receipt_number', 'customer_name', 'phone_number', 'source_machine_id')
    inlines = [SaleItemInline, PaymentInline] # عرض المنتجات والأقساط داخل الفاتورة
    
    # جعل الحقول للقراءة فقط لأنها بيانات تاريخية قادمة من العميل
    readonly_fields = ('source_machine_id', 'local_id', 'receipt_number', 'total_amount', 'created_at_local')

# 7. المصروفات
@admin.register(ServerExpense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'expense_year', 'expense_month', 'source_machine_id')
    list_filter = ('source_machine_id', 'expense_year')
    search_fields = ('description',)

# 8. حركات المخزن
@admin.register(ServerStockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'product_name_snapshot', 'quantity', 'source_machine_id', 'created_at_local')
    list_filter = ('source_machine_id', 'transaction_type')
    search_fields = ('product_name_snapshot',)