from django.urls import path
# 🔴 تغيير الاسم هنا لتجنب التعارض مع ملف auth_views الخاص بنا
from django.contrib.auth import views as django_auth_views

# 🟢 استدعاء صريح لكل ملفات الـ Views
from salesapp.views import (
    auth_views,
    branch_views,
    settings_views,
    inventory_views,
    purchase_views,  # 🔴 ضيف دي هنا
    receipt_views,
    print_views,
    collections_views,
    expense_views,
    report_views,
    subscription_views,
    backup_views,
    import_views,
    utility_views,
    sync_views,
    cloud_user_views,
    initial_sync_views
)

urlpatterns = [
    # --- Cloud Users Management ---
    path('cloud-users/', cloud_user_views.manage_cloud_users, name='manage_cloud_users'),
    path('cloud-users/delete/<int:user_id>/', cloud_user_views.delete_cloud_user, name='delete_cloud_user'),
    path('cloud-users/edit/<int:user_id>/', cloud_user_views.edit_cloud_user, name='edit_cloud_user'),
    path('cloud-sync/initial/', initial_sync_views.cloud_initial_sync, name='cloud_initial_sync'),

    # --- المصادقة والإعدادات الأساسية ---
    path('', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('emergency-reset/', auth_views.emergency_reset_view, name='emergency_reset'),
    path('setup-company/', auth_views.setup_company, name='setup_company'),
    path('general-settings/', auth_views.general_settings, name='general_settings'),
    
    path('password-change/', django_auth_views.PasswordChangeView.as_view(
        template_name='salesapp/password_change.html',
        success_url='/password-change/done/'
    ), name='password_change'),
    path('password-change/done/', django_auth_views.PasswordChangeDoneView.as_view(
        template_name='salesapp/password_change_done.html'
    ), name='password_change_done'),

    path('backup-dashboard/', backup_views.backup_dashboard, name='backup_dashboard'),
    path('backup-db/', backup_views.download_backup, name='download_backup'),
    path('restore-db/', backup_views.restore_backup, name='restore_backup'),
    
    # --- الفروع والواجهة الرئيسية ---
    path('select_branch/', branch_views.select_branch, name='select_branch'), 
    path('set_branch/<int:branch_id>/', branch_views.set_branch, name='set_branch'),
    path('dashboard/', branch_views.dashboard, name='dashboard'),

    # ==========================================
    # 📦 موديول المخازن والمشتريات (الجديد)
    # ==========================================
    path('inventory/products/', inventory_views.manage_products, name='manage_products'),
    path('inventory/products/delete/<int:pk>/', inventory_views.delete_product, name='delete_product'),
    path('inventory/products/update-commission/', inventory_views.update_commission, name='update_commission'),
    
    # مسارات آلة الزمن (المندبات)
    path('inventory/products/commission/update/', inventory_views.update_commission, name='update_commission'),
    path('inventory/products/commission/edit/<int:record_id>/', inventory_views.edit_commission_record, name='edit_commission_record'),
    path('inventory/products/commission/delete/<int:record_id>/', inventory_views.delete_commission_record, name='delete_commission_record'),
    
    path('inventory/suppliers/', purchase_views.manage_suppliers, name='manage_suppliers'),
    path('inventory/suppliers/delete/<int:pk>/', purchase_views.delete_supplier, name='delete_supplier'),
    
    path('inventory/purchases/', purchase_views.manage_purchase_invoices, name='manage_purchase_invoices'),
    path('inventory/purchases/search/', purchase_views.search_purchase_invoices, name='search_purchase_invoices'),
    path('inventory/purchases/edit/<int:invoice_id>/', purchase_views.edit_purchase_invoice, name='edit_purchase_invoice'),
    path('inventory/purchases/delete/<int:invoice_id>/', purchase_views.delete_purchase_invoice, name='delete_purchase_invoice'),
    path('inventory/adjustment/add/', inventory_views.add_adjustment, name='add_adjustment'),

    path('product/<int:pk>/ledger/', inventory_views.product_ledger, name='product_ledger'),

    # ==========================================
    # 🧾 موديول المبيعات والإيصالات
    # ==========================================
    path('receipts/add/', receipt_views.add_receipt, name='add_receipt'),
    path('receipts/search/', receipt_views.search_receipts, name='search_receipts'),
    path('receipts/edit/<int:receipt_id>/', receipt_views.edit_receipt, name='edit_receipt'),
    path('receipts/print/<int:receipt_id>/', print_views.print_single_receipt_view, name='print_single_receipt_view'),
    path('receipts/print_batch/', print_views.print_batch_receipts_view, name='print_batch_receipts'),
    path('receipt/delete/<int:pk>/', receipt_views.delete_receipt, name='delete_receipt'),
    path('receipt/delete-all/', receipt_views.delete_all_receipts, name='delete_all_receipts'),
    
    path('api/customer-suggestions/', receipt_views.get_customer_suggestions, name='get_customer_suggestions'),
    path('api/product-suggestions/', receipt_views.product_suggestions_api, name='product_suggestions_api'),
    path('collections/', collections_views.manage_collections, name='manage_collections'),
    path('reports/sales/', report_views.sales_reports, name='sales_reports'),
    path('reports/invoices/', report_views.invoices_report, name='invoices_report'),

    # ==========================================
    # ⚙️ الإعدادات الفرعية والمصروفات
    # ==========================================
    # إعدادات الفروع والمناديب
    path('settings/branches/', settings_views.manage_branches, name='manage_branches'),
    path('settings/branches/edit/<int:pk>/', settings_views.edit_branch, name='edit_branch'),
    path('settings/branches/delete/<int:pk>/', settings_views.delete_branch, name='delete_branch'),
    
    path('settings/salespersons/', settings_views.manage_salespersons, name='manage_salespersons'),
    path('settings/salespersons/edit/<int:pk>/', settings_views.edit_salesperson, name='edit_salesperson'),
    path('settings/salespersons/delete/<int:pk>/', settings_views.delete_salesperson, name='delete_salesperson'),
    
    path('settings/subscription/', subscription_views.subscription_dashboard, name='subscription_dashboard'),
    path('settings/import-legacy/', import_views.smart_import_wizard, name='smart_import_wizard'),
    
    path('tools/mobile-sync/', sync_views.cloud_hub_view, name='mobile_sync'),
    path('tools/mobile-sync/preview/', sync_views.mobile_import_preview, name='mobile_import_preview'),
    path('tools/mobile-sync/confirm/', sync_views.mobile_import_confirm, name='mobile_import_confirm'),
    path('tools/mobile-sync/export-setup/', sync_views.export_setup_json, name='export_setup_json'),
    path('tools/export-mobile-json/', sync_views.export_mobile_json, name='export_mobile_json'),
    
    path('tools/cloud-status/', sync_views.cloud_hub_view, name='cloud_status'),
    path('tools/cloud-push-ajax/', sync_views.push_to_cloud_ajax, name='push_to_cloud_ajax'),
    path('tools/manage-devices/', sync_views.cloud_hub_view, name='manage_devices'),
    
    # Unified Staging
    path('tools/pending-receipts/', sync_views.cloud_hub_view, name='pending_receipts'),
    path('tools/pending-receipts/approve/', sync_views.approve_pending_receipts, name='approve_pending_receipts'),
    path('tools/pending-receipts/edit/<int:pk>/', sync_views.edit_pending_receipt, name='edit_pending_receipt'),
    path('tools/pending-receipts/delete/<int:pk>/', sync_views.delete_pending_receipt, name='delete_pending_receipt'),

    # Cloud Hub & USB
    path('cloud-hub/', sync_views.cloud_hub_view, name='cloud_hub'),
    path('cloud-hub/add-online-device/', sync_views.add_online_device_view, name='add_online_device_view'),
    path('tools/usb-devices/', sync_views.usb_devices_api, name='usb_devices_api'),
    path('tools/usb-sync/<str:device_id>/', sync_views.usb_sync_api, name='usb_sync_api'),

    # Offline APIs
    path('api/local/setup/', sync_views.local_setup_api, name='local_setup_api'),
    path('api/local/push/', sync_views.local_push_api, name='local_push_api'),

    path('expenses/', expense_views.manage_expenses, name='manage_expenses'),
    path('expenses/delete/<int:pk>/', expense_views.delete_expense, name='delete_expense'),  

    # --- التحكم في التطبيق (Desktop) ---
    path('activate/', subscription_views.activate_app_view, name='activate_app'),
    path('shutdown-app/', utility_views.exit_app, name='shutdown_app'),
]