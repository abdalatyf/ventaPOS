import os
import django
from django.db.models import Sum

# 1. تهيئة بيئة جانجو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales.settings')
django.setup()

from salesapp.models import Receipt

def reconcile_receipt_totals():
    print("🚀 بدء عملية تسوية إجماليات الفواتير...")

    # نجلب جميع فواتير التقسيط فقط (لأن الكاش الإجمالي هو نفسه المقدم/المدفوع)
    installment_receipts = Receipt.objects.filter(is_cash_sale=False)
    
    updated_count = 0
    skipped_count = 0

    for receipt in installment_receipts:
        # جلب المقدم (أو صفر إذا كان فارغاً)
        down_payment = receipt.down_payment or 0
        
        # حساب إجمالي الأقساط المرتبطة بهذه الفاتورة مباشرة من الداتا بيز
        installments_total = receipt.payments.aggregate(total=Sum('amount'))['total'] or 0
        
        # الإجمالي الحقيقي (قيمة العقد الفعلية)
        actual_total = down_payment + installments_total

        # إذا كان هناك فرق بين الإجمالي المسجل والإجمالي الحقيقي
        if receipt.total_amount != actual_total:
            old_total = receipt.total_amount
            receipt.total_amount = actual_total
            # نحفظ الحقل المحدد فقط لسرعة الأداء وعدم تفعيل signals غير ضرورية
            receipt.save(update_fields=['total_amount'])
            
            print(f"🔄 تم تصحيح الوصل #{receipt.receipt_number}: كان ({old_total}) وأصبح ({actual_total})")
            updated_count += 1
        else:
            skipped_count += 1

    print("="*40)
    print(f"✅ تمت التسوية بنجاح!")
    print(f"📊 الفواتير التي تم تصحيحها: {updated_count}")
    print(f"⏭️ الفواتير السليمة (تم تخطيها): {skipped_count}")
    print("="*40)

if __name__ == '__main__':
    reconcile_receipt_totals()
