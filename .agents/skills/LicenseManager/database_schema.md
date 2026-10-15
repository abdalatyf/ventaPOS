# LicenseManager - Database Schema

This document provides a deep, line-by-line scan of the data models and schemas in the LicenseManager application.

## 1. Model: `Client`
Represents a client registered in the LicenseManager.

### Fields
*   **`id`**: `BigAutoField` (Implicit primary key added by Django).
*   **`name`**: `CharField`
    *   **Max Length**: 100
    *   **Verbose Name**: "اسم العميل"
*   **`phone`**: `CharField`
    *   **Max Length**: 20
    *   **Verbose Name**: "رقم الهاتف"
*   **`machine_id`**: `CharField`
    *   **Max Length**: 100
    *   **Database Constraints**: `unique=True`
    *   **Verbose Name**: "بصمة الجهاز (Machine ID)"
*   **`store_name`**: `CharField`
    *   **Max Length**: 100
    *   **Database Constraints**: `blank=True, null=True`
    *   **Verbose Name**: "اسم المحل"
*   **`is_banned`**: `BooleanField`
    *   **Default Value**: `False`
    *   **Verbose Name**: "حظر هذا الجهاز (Blacklist)"
    *   **Purpose**: "الجدار الثامن" (The 8th Wall) - Server-side ban for the machine.
*   **`created_at`**: `DateTimeField`
    *   **Database Constraints**: `auto_now_add=True` (Set to current date/time when the object is first created)
    *   **Verbose Name**: "تاريخ التسجيل"

### Relationships
*   Has a reverse relation `licenses` from the `License` model.

---

## 2. Model: `License`
Represents a license issued to a client.

### Choices (`PRODUCT_CHOICES`)
Defines the product/package type for the license.
*   `1`: 'تجربة مجانية (Trial 60 Days)'
*   `2`: 'طباعة فقط - سنة واحدة'
*   `3`: 'طباعة فقط - مدى الحياة'
*   `4`: 'إدارة كاملة - سنة واحدة'
*   `5`: 'إدارة كاملة - 3 سنوات'
*   `6`: 'إدارة كاملة - 5 سنوات'
*   `7`: 'إدارة كاملة - مدى الحياة (VIP)'
*   `8`: 'إضافة الأونلاين - سنة'
*   `9`: 'إضافة الأونلاين - 5 سنوات'
*   `10`: 'كود شحن (100 فاتورة)'
*   `11`: 'كود شحن (300 فاتورة)'
*   `12`: 'كود شحن (500 فاتورة)'
*   `13`: 'كود شحن (1000 فاتورة)'
*   `14`: 'كود شحن (3000 فاتورة)'
*   `15`: 'كود شحن (5000 فاتورة)'
*   `16`: 'كود الطوارئ (استعادة وضبط - لمرة واحدة)'

### Fields
*   **`id`**: `BigAutoField` (Implicit primary key added by Django).
*   **`client`**: `ForeignKey`
    *   **To**: `Client`
    *   **On Delete**: `models.CASCADE` (Deletes licenses if the client is deleted).
    *   **Related Name**: `licenses`
    *   **Verbose Name**: "العميل"
*   **`product_id`**: `IntegerField`
    *   **Choices**: `PRODUCT_CHOICES`
    *   **Verbose Name**: "نوع الباقة"
*   **`price`**: `IntegerField`
    *   **Default Value**: `0`
    *   **Verbose Name**: "المبلغ المدفوع (جنية)"
*   **`notes`**: `TextField`
    *   **Database Constraints**: `blank=True, null=True`
    *   **Verbose Name**: "ملاحظات فنية (سري)"
*   **`start_date`**: `DateField`
    *   **Default Value**: `django.utils.timezone.now`
    *   **Verbose Name**: "تاريخ بداية الترخيص"
*   **`generated_code`**: `CharField`
    *   **Max Length**: 20
    *   **Database Constraints**: `editable=False` (Prevents modification in forms/admin).
    *   **Verbose Name**: "كود التفعيل"
*   **`created_at`**: `DateTimeField`
    *   **Database Constraints**: `auto_now_add=True`
    *   **Verbose Name**: "تاريخ الإنشاء"
*   **`is_active`**: `BooleanField`
    *   **Default Value**: `True`
    *   **Verbose Name**: "فعال"

### Custom Validation / Signals / Methods

#### Overridden `save` method
*   Intercepts the object before saving it to the database.
*   **Logic**: If `self.generated_code` is empty (i.e., on the first save), it dynamically generates the license code by calling `LicenseGenerator.generate(machine_id=self.client.machine_id, product_id=self.product_id, start_date=self.start_date)`.
*   Calls `super().save(*args, **kwargs)` to commit to the database.

#### Properties
*   **`is_lifetime`**: Returns `True` if `product_id` is 3 or 7.
*   **`is_invoice_based`**: Returns `True` if `product_id` is between 10 and 15 (inclusive).
*   **`is_emergency_code`**: Returns `True` if `product_id` is 16.

#### Helper Methods
*   **`get_duration_days()`**: Maps the `product_id` to its respective validity duration in days (e.g., 60 for Trial, 365 for 1-year plans, 365*99 for lifetime plans). Returns `0` if not found.
*   **`get_expiry_date()`**:
    *   Returns `None` if the license `is_invoice_based`, `is_emergency_code`, or `is_lifetime`.
    *   Otherwise, adds the days from `get_duration_days()` to the `start_date` and returns the resulting expiry date.
*   **`get_whatsapp_date_str()`**: Returns a human-readable string of the expiry date for WhatsApp messages. Returns "مدى الحياة (Lifetime)", "استخدام لمرة واحدة (One-Time Use)", "رصيد فواتير (غير محدد المدة)", or the formatted string `%Y-%m-%d` of the expiry date.
