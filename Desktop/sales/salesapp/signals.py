from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Receipt, InventoryItem, Salesperson, Expense, SyncDeletionLog

@receiver(post_delete, sender=Receipt)
@receiver(post_delete, sender=InventoryItem)
@receiver(post_delete, sender=Salesperson)
@receiver(post_delete, sender=Expense)
def log_deletion(sender, instance, **kwargs):
    """
    هذه الدالة تعمل أوتوماتيكياً بعد حذف أي عنصر من الجداول المذكورة أعلاه
    """
    model_name = sender.__name__ # هيجيب اسم الكلاس (مثلاً Receipt)
    
    # نسجل أن هذا العنصر تم حذفه
    SyncDeletionLog.objects.create(
        table_name=model_name,
        record_id=instance.id
    )