from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.name
