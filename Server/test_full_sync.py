"""
test_full_sync.py — اختبار شامل لـ AdminSyncPushView
يُرسل كل أنواع الكيانات ويتحقق من تسجيلها في قاعدة بيانات Django.
يُشغَّل بعد تشغيل السيرفر على http://127.0.0.1:8000
"""
import requests
import json
import sys
import django
import os
sys.path.insert(0, r'D:\Projects\VentaPOS\Server')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server_backend.settings')

BASE_URL = 'http://127.0.0.1:8000'
MACHINE_ID = 'TEST_MOBILE_MACHINE_001'
COMPANY_CODE = '9999'

PAYLOAD = {
    'machine_id': MACHINE_ID,
    'company_code': COMPANY_CODE,
    'payload': {
        'settings': {
            'company_name': 'شركة VentaPOS للاختبار',
            'footer_text': 'شكراً لتعاملكم معنا'
        },
        'branches': [
            {'id': 1, 'name': 'الفرع الرئيسي', 'local_id': 1, 'action': 'CREATE'},
        ],
        'products': [
            {'id': 1, 'local_id': 1, 'name': 'شاشة سامسونج', 'initial_quantity': 50,
             'initial_purchase_price': 8000, 'branch_id': 1, 'action': 'CREATE'},
            {'id': 2, 'local_id': 2, 'name': 'لابتوب ديل', 'initial_quantity': 20,
             'initial_purchase_price': 15000, 'branch_id': 1, 'action': 'CREATE'},
        ],
        'users': [
            {'id': 1, 'local_id': 1, 'name': 'أحمد محمد', 'branch_id': 1,
             'cloud_username': 'ahmed', 'cloud_password': 'pass123', 'action': 'CREATE'},
        ],
        'suppliers': [
            {'id': 1, 'local_id': 1, 'name': 'مورد الإلكترونيات', 'phone': '01012345678',
             'address': 'القاهرة - الموسكي', 'action': 'CREATE'},
        ],
        'expenses': [
            {'id': 1, 'local_id': 1, 'amount': 1500, 'description': 'إيجار المحل',
             'expense_year': 2026, 'expense_month': 6, 'branch_id': 1},
        ],
        'purchase_invoices': [
            {
                'id': 1, 'local_id': 1, 'invoice_number': 1001, 'invoice_month': 6,
                'invoice_year': 2026, 'invoice_type': 'PURCHASE', 'supplier_id': 1,
                'items': [
                    {'inventory_item_id': 1, 'product_name': 'شاشة سامسونج',
                     'quantity': 10, 'purchase_price': 7500}
                ]
            },
        ],
        'receipts': [
            {
                'id': 1, 'local_id': 1, 'receipt_number': 5001, 'branch_id': 1,
                'salesperson_id': 1, 'customer_name': 'محمد علي', 'phone_number': '01099999999',
                'address': 'المعادي', 'area': 'القاهرة', 'total_amount': 8000,
                'down_payment': 2000, 'installment_system': '6×1000',
                'sale_year': 2026, 'sale_month': 6, 'is_cash_sale': False,
                'products_text': 'شاشة سامسونج', 'receipt_hash': 'HASH_TEST_001',
                'sync_action': 'NEW', 'is_confirmed': False,
                'items': [
                    {'inventory_item_id': 1, 'product_name': 'شاشة سامسونج',
                     'quantity': 1, 'unit_price': 8000}
                ],
                'installment_payments': [
                    {'payment_date': '2026-07-01', 'amount': 1000},
                    {'payment_date': '2026-08-01', 'amount': 1000},
                ]
            },
        ],
        'commission_history': [
            {'id': 1, 'local_id': 1, 'salesperson_id': 1, 'amount': 200,
             'reason': 'عمولة فاتورة 5001', 'date': '2026-06-24'},
        ],
    }
}

def run_test():
    print("=" * 60)
    print("🧪 اختبار Full Sync API — VentaPOS Central Server")
    print("=" * 60)

    # أولاً: تسجيل الجهاز
    print("\n[1] تسجيل الجهاز...")
    reg_resp = requests.post(
        f'{BASE_URL}/api/v1/sync/push/',
        json={'machine_id': MACHINE_ID, 'payload': {'company_settings': {'name': 'شركة اختبار'}}},
        timeout=10
    )
    print(f"    → Status: {reg_resp.status_code} | {reg_resp.text[:200]}")

    # ثانياً: تفعيل الترخيص مباشرةً في DB
    print("\n[2] تفعيل الترخيص على السيرفر...")
    try:
        django.setup()
        from sync_api.models import ServerLicense
        lic, _ = ServerLicense.objects.get_or_create(
            machine_id=MACHINE_ID,
            defaults={'client_name': 'عميل اختبار', 'is_active': True,
                      'is_online_active': True, 'company_code': COMPANY_CODE}
        )
        lic.is_active = True
        lic.is_online_active = True
        lic.company_code = COMPANY_CODE
        lic.save()
        print(f"    ✅ الترخيص مفعّل (company_code={lic.company_code})")
    except Exception as e:
        print(f"    ⚠️  تعذّر تفعيل الترخيص برمجياً: {e}")
        print("    ℹ️  تأكد من تفعيله يدوياً في Django Admin ثم أعد التشغيل")

    # ثالثاً: إرسال الـ payload الشامل
    print("\n[3] إرسال Full Payload لـ /api/v1/sync/admin-push/ ...")
    resp = requests.post(
        f'{BASE_URL}/api/v1/sync/admin-push/',
        json=PAYLOAD,
        timeout=30
    )
    print(f"    → Status: {resp.status_code}")
    try:
        data = resp.json()
        print(f"    → Response: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except Exception:
        print(f"    → Raw: {resp.text[:500]}")

    # رابعاً: التحقق من قاعدة البيانات
    if resp.status_code == 200:
        print("\n[4] التحقق من قاعدة البيانات...")
        try:
            from sync_api.models import (
                ServerBranch, ServerInventoryItem, ServerSalesperson,
                ServerSupplier, ServerExpense, ServerPurchaseInvoice,
                ServerReceipt, ServerCommissionHistory
            )
            checks = [
                ('الفروع', ServerBranch.objects.filter(source_machine_id=MACHINE_ID).count()),
                ('المنتجات', ServerInventoryItem.objects.filter(source_machine_id=MACHINE_ID).count()),
                ('المندوبين', ServerSalesperson.objects.filter(source_machine_id=MACHINE_ID).count()),
                ('الموردين', ServerSupplier.objects.filter(source_machine_id=MACHINE_ID).count()),
                ('المصروفات', ServerExpense.objects.filter(source_machine_id=MACHINE_ID).count()),
                ('فواتير المشتريات', ServerPurchaseInvoice.objects.filter(source_machine_id=MACHINE_ID).count()),
                ('الفواتير/الوصلات', ServerReceipt.objects.filter(source_machine_id=MACHINE_ID).count()),
                ('سجلات العمولات', ServerCommissionHistory.objects.filter(source_machine_id=MACHINE_ID).count()),
            ]
            all_pass = True
            for name, count in checks:
                status = "✅" if count > 0 else "❌"
                print(f"    {status} {name}: {count} سجل")
                if count == 0:
                    all_pass = False
            print("\n" + ("✅ جميع الاختبارات نجحت!" if all_pass else "❌ بعض الاختبارات فشلت"))
        except Exception as e:
            print(f"    ⚠️  خطأ في التحقق: {e}")
    else:
        print("\n❌ الاختبار فشل — السيرفر أعاد خطأ")

if __name__ == '__main__':
    run_test()
