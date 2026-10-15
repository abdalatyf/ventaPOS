# هيكل قاعدة البيانات (Database Schema) - VentaPOS NextGen
*المرجع الأساسي (Single Source of Truth) لهيكل الجداول والعلاقات في نظام PostgreSQL.*

## 1. نظرة عامة على المعمارية
يعتمد VentaPOS NextGen على قاعدة بيانات **PostgreSQL** موحدة تدعم تعدد الشركات (Multi-Tenant Architecture)، حيث يتم عزل بيانات كل شركة عن الأخرى بشكل آمن باستخدام حقل `tenant`.

**السياسات العامة المطبقة:**
- **المعرفات الأساسية (PK):** حقول رقمية متسلسلة (`BigAutoField`).
- **العزل (Isolation):** جميع جداول النظام تحتوي على مفتاح أجنبي `tenant_id`.
- **الحذف الآمن (Soft Delete):** حقل `is_deleted = FALSE` مدمج في كافة العمليات لتجنب فقدان البيانات.
- **الدقة المالية:** جميع الحقول الخاصة بالأموال تستخدم `DECIMAL(12, 2)` لضمان الدقة في الحسابات.
- **قيود الأمان:** يتم فرض قيود فريدة (Unique Constraints) معرّفة على مستوى الـ Tenant لمنع التكرار.

---

## 2. الكيانات الأساسية (Core Entities)

### 2.1 الشركة (`tenant`)
الكيان الجذري الذي تعتمد عليه كافة الجداول.
- `id`: BigAutoField (PK)
- `company_code`: VARCHAR(10) [فريد]
- `name`: VARCHAR(100) (اسم الشركة)
- `is_active`: BOOLEAN (حالة الحساب)
- `is_deleted`: BOOLEAN
- `created_at`: TIMESTAMPTZ

### 2.2 إعدادات الشركة (`company_setting`)
- `tenant_id`: OneToOne (علاقة 1:1 مع الشركة)
- `name`: VARCHAR(100)
- `phone1` / `phone2`: VARCHAR(20)
- `footer_text`: VARCHAR(250) (نص تذييل الفاتورة)
- `is_cloud_viewer`: BOOLEAN

### 2.3 مستخدم السحابة (`cloud_user`)
- `tenant_id`: FK
- `username`: VARCHAR(150)
- `password_hash`: VARCHAR(255)
- `role`: VARCHAR(50) (مدير النظام، أمين الخزنة، إلخ)

### 2.4 الفرع / المخزن (`branch`)
- `tenant_id`: FK
- `local_id`: INTEGER (مُعرف محلي للفرع)
- `name`: VARCHAR(150)

### 2.5 المندوب (`salesperson`)
- `tenant_id` / `branch_id`: FK
- `local_id`: INTEGER
- `name`: VARCHAR(100)
- `is_device_active`: BOOLEAN

---

## 3. البضاعة والمخازن (Inventory)

### 3.1 الصنف / البضاعة (`inventory_item`)
- `tenant_id` / `branch_id`: FK
- `local_id`: INTEGER
- `name`: VARCHAR(200)
- `initial_quantity`: INTEGER (الرصيد الافتتاحي)
- `initial_purchase_price`: DECIMAL(12,2) (سعر الشراء الافتتاحي)
- `initial_commission_amount`: DECIMAL(12,2) (العمولة الأساسية)
- `initial_month` / `initial_year`: INTEGER (تاريخ الرصيد الافتتاحي)

### 3.2 سجل العمولات (`commission_history`)
تتبع تاريخي لتغييرات نسب عمولة المندوب للصنف.
- `inventory_item_id`: FK
- `commission_amount`: DECIMAL(12,2)
- `activation_month` / `activation_year`: INTEGER

### 3.3 تسويات الجرد (`inventory_adjustment`)
- `inventory_item_id`: FK
- `adjustment_type`: VARCHAR(20) (عجز `DEFICIT` / زيادة `SURPLUS`)
- `quantity`: INTEGER
- `reason`: VARCHAR(255)
- `adjustment_month` / `adjustment_year`: INTEGER

---

## 4. المشتريات (Procurement)

### 4.1 المورد (`supplier`)
- `tenant_id`: FK
- `name`: VARCHAR(200)

### 4.2 فاتورة الشراء (`purchase_invoice`)
- `tenant_id` / `branch_id` / `supplier_id`: FK
- `invoice_number`: INTEGER
- `invoice_type`: VARCHAR(20) (فاتورة شراء `PURCHASE` / مرتجع `RETURN`)
- `invoice_month` / `invoice_year`: INTEGER

### 4.3 أصناف الشراء (`purchase_invoice_item`)
- `purchase_invoice_id` / `inventory_item_id`: FK
- `quantity`: INTEGER
- `purchase_price`: DECIMAL(12,2)

---

## 5. المبيعات والخزنة (Sales & Finance)

### 5.1 الفاتورة (`receipt`)
- `tenant_id` / `branch_id` / `salesperson_id`: FK
- `receipt_number`: INTEGER
- `receipt_hash`: VARCHAR(255) (بصمة تشفير لحماية الفاتورة من التلاعب)
- `customer_name`: VARCHAR(200) (العميل)
- `phone_number` / `address` / `area`: VARCHAR
- `total_amount` / `down_payment`: DECIMAL(12,2)
- `sale_month` / `sale_year`: INTEGER
- `is_cash_sale`: BOOLEAN (نقدية أم آجلة)
- `products_text`: TEXT (ملخص نصي للأصناف)

### 5.2 الصنف المباع (`sale_item`)
- `receipt_id` / `inventory_item_id`: FK
- `quantity`: INTEGER
- `unit_price`: DECIMAL(12,2)

### 5.3 القسط المجدول (`installment_payment`)
- `receipt_id`: FK
- `payment_date`: DATE (تاريخ الاستحقاق)
- `amount`: DECIMAL(12,2)

### 5.4 المصروفات (`expense`)
- `tenant_id` / `branch_id`: FK
- `amount`: DECIMAL(12,2)
- `description`: VARCHAR(255) (بند الصرف)
- `expense_month` / `expense_year`: INTEGER

---

## 6. نظام التراخيص والأمان (Licensing & Security)

### 6.1 ترخيص العميل (`client_license`)
- `tenant_id`: FK
- `machine_id`: VARCHAR(255) (بصمة الجهاز)
- `license_code_hash`: VARCHAR(64)
- `product_id`: INTEGER
- `start_date` / `expiry_date`: DATE
- `invoices_balance`: INTEGER (رصيد الفواتير)
- `is_active`: BOOLEAN

### 6.2 الأكواد المستخدمة (`used_license`)
- `code_hash`: VARCHAR(64) [فريد لمنع التكرار]

### 6.3 أرشيف التراخيص (`license_history`)
- `operation_type`: VARCHAR(50) (تفعيل، تجديد، إلخ)
- `status`: VARCHAR(50)
- `added_balance`: INTEGER

### 6.4 الفواتير المعلقة (`pending_external_receipt`)
- `tenant_id` / `branch_id`: FK
- `batch_id`: VARCHAR(100)
- `source`: VARCHAR(20) (`CLOUD`, `USB`)
- `payload`: JSONField (البيانات الخام للفواتير)
- `is_processed`: BOOLEAN
