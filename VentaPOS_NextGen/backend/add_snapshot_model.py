import os

models_path = r"D:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\models.py"

with open(models_path, "r", encoding="utf-8") as f:
    content = f.read()

snapshot_model = """
# ===========================================================================
# 11. Reporting Optimizations (Snapshots)
# ===========================================================================
class MonthlyInventorySnapshot(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='snapshots')
    year = models.PositiveIntegerField(db_index=True)
    month = models.PositiveIntegerField(db_index=True)
    closing_stock = models.IntegerField()
    closing_value = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('item', 'year', 'month')
        indexes = [
            models.Index(fields=['item', 'year', 'month']),
        ]

    def __str__(self):
        return f"{self.item.name} - {self.month}/{self.year}: {self.closing_stock}"
"""

if "class MonthlyInventorySnapshot" not in content:
    with open(models_path, "a", encoding="utf-8") as f:
        f.write("\n" + snapshot_model)
    print("Added MonthlyInventorySnapshot to models.py")
else:
    print("MonthlyInventorySnapshot already exists.")
