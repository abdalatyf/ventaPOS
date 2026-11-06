"""
Tests for Batch V1-1 in VentaPOS NextGen:
- Item 1: Collection and sales sum fixes across reports & Search Receipts.
- Item 4: Print-Only Basic Plan Mode (product_id in (2, 3)).
- Item 5: Old external data support (pre-license receipts: zero stock deduction, zero balance deduction).
- Item 6: Unauthenticated backup restore from application startup.
- Item 10: Dedicated Purchases Report (GET /api/v1/reports/purchases/).
- Item 11: Expense categorization (Expense.category & filtering).
"""
import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from api.models import (
    Branch,
    Salesperson,
    InventoryItem,
    Supplier,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    Receipt,
    SaleItem,
    InstallmentPayment,
    Expense,
    ClientLicense,
    CompanySetting,
)
from api.utils.security_utils import get_machine_id, generate_record_signature


def create_valid_license(product_id=1, start_date=None, expiry_date=None, invoices_balance=1000):
    ClientLicense.objects.all().delete()
    machine_id = get_machine_id()
    start_date = start_date or datetime.date(2026, 1, 1)
    expiry_date = expiry_date or datetime.date(2027, 1, 1)
    sig = generate_record_signature(expiry_date, invoices_balance, machine_id, product_id, True)
    return ClientLicense.objects.create(
        product_id=product_id,
        start_date=start_date,
        expiry_date=expiry_date,
        invoices_balance=invoices_balance,
        is_active=True,
        machine_id=machine_id,
        license_code_hash=sig,
    )


class BatchV11Tests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(username="admin", password="password123")
        self.client.force_authenticate(user=self.user)

        # Default valid full-feature license
        self.license = create_valid_license(product_id=5, start_date=datetime.date(2026, 1, 1), expiry_date=datetime.date(2027, 1, 1))

        self.branch = Branch.objects.create(name="الفرع الرئيسي")
        self.sp = Salesperson.objects.create(name="أحمد محمود", branch=self.branch)
        self.supplier = Supplier.objects.create(name="مورد التوحيد")

        self.item = InventoryItem.objects.create(
            branch=self.branch,
            name="شاشة 43 بوصة",
            initial_quantity=20,
            initial_purchase_price=5000,
            initial_month=1,
            initial_year=2026,
        )

        self.setting = CompanySetting.objects.create(
            collection_commission_rate=0.10
        )

    def test_purchases_report_endpoint_and_kpis(self):
        """Test GET /api/v1/reports/purchases/ calculation and filters."""
        inv1 = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=101,
            invoice_type="PURCHASE",
            invoice_month=5,
            invoice_year=2026,
        )
        PurchaseInvoiceItem.objects.create(
            invoice=inv1,
            inventory_item=self.item,
            quantity=2,
            purchase_price=5000,
        )

        inv2 = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=102,
            invoice_type="RETURN",
            invoice_month=5,
            invoice_year=2026,
        )
        PurchaseInvoiceItem.objects.create(
            invoice=inv2,
            inventory_item=self.item,
            quantity=1,
            purchase_price=5000,
        )

        url = f"/api/v1/reports/purchases/?branch_id={self.branch.id}&year=2026&month=5"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        kpis = res.data["kpis"]
        self.assertEqual(kpis["purchase_invoices_count"], 1)
        self.assertEqual(kpis["returns_count"], 1)
        self.assertEqual(kpis["gross_purchases_amount"], 10000)
        self.assertEqual(kpis["returns_amount"], 5000)
        self.assertEqual(kpis["net_purchases_amount"], 5000)
        self.assertEqual(kpis["total_units"], 1)
        self.assertEqual(len(res.data["invoices"]), 2)

    def test_expense_category_field_and_filter(self):
        """Test Expense.category defaults, storage, and viewset filtering."""
        exp1 = Expense.objects.create(
            branch=self.branch,
            description="فاتورة كهرباء",
            amount=450,
            expense_month=5,
            expense_year=2026,
            category="كهرباء ومياه",
        )
        exp2 = Expense.objects.create(
            branch=self.branch,
            description="أدوات مكتبية",
            amount=150,
            expense_month=5,
            expense_year=2026,
        )
        self.assertEqual(exp2.category, "مصروفات عامة")

        res_all = self.client.get(f"/api/v1/expenses/?month=5&year=2026")
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        results = res_all.data if isinstance(res_all.data, list) else res_all.data.get("results", [])
        self.assertEqual(len(results), 2)

        res_filtered = self.client.get(f"/api/v1/expenses/?month=5&year=2026&category=كهرباء ومياه")
        self.assertEqual(res_filtered.status_code, status.HTTP_200_OK)
        results_filtered = res_filtered.data if isinstance(res_filtered.data, list) else res_filtered.data.get("results", [])
        self.assertEqual(len(results_filtered), 1)
        self.assertEqual(results_filtered[0]["category"], "كهرباء ومياه")

    def test_print_only_basic_plan_restrictions(self):
        """Test product_id=2 (طباعة فقط) blocks inventory, purchases, and analytical reports."""
        lic = create_valid_license(
            product_id=2,
            start_date=datetime.date(2026, 1, 1),
            expiry_date=datetime.date(2027, 1, 1),
            invoices_balance=500
        )

        res_status = self.client.get("/api/v1/license/status/")
        self.assertEqual(res_status.status_code, status.HTTP_200_OK)
        self.assertTrue(res_status.data.get("is_print_only"))

        # Restricted endpoints must return HTTP 403
        res_purchases = self.client.get("/api/v1/purchase-invoices/")
        self.assertEqual(res_purchases.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error", res_purchases.json())

        res_report = self.client.get(f"/api/v1/reports/inventory-movement/?branch_id={self.branch.id}&year=2026&month=5")
        self.assertEqual(res_report.status_code, status.HTTP_403_FORBIDDEN)

        # Allowed endpoint: Receipts list
        res_receipts = self.client.get("/api/v1/receipts/")
        self.assertEqual(res_receipts.status_code, status.HTTP_200_OK)

    def test_pre_license_receipt_zero_stock_and_zero_balance_deduction(self):
        """Pre-license receipt (sale_date < lic_start_date) does not deduct stock or invoice balance."""
        lic = create_valid_license(
            product_id=5,
            start_date=datetime.date(2026, 6, 1),
            expiry_date=datetime.date(2027, 6, 1),
            invoices_balance=100
        )

        initial_balance = lic.invoices_balance
        initial_stock = self.item.get_stock_at_date(5, 2026)

        # 1. Attempting to add sale_items to pre-license receipt should be rejected
        invalid_data = {
            "branch": self.branch.id,
            "salesperson": self.sp.id,
            "customer_name": "عميل قديم",
            "sale_month": 5,
            "sale_year": 2026,
            "is_cash_sale": True,
            "total_amount": 5000,
            "products_text": "صنف تجريبي",
            "sale_items": [
                {
                    "inventory_item": self.item.id,
                    "quantity": 1,
                    "sell_price": 5000,
                }
            ],
        }
        res_invalid = self.client.post("/api/v1/receipts/", invalid_data, format="json")
        self.assertEqual(res_invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", res_invalid.data)

        # 2. Free-text pre-license receipt succeeds
        valid_data = {
            "branch": self.branch.id,
            "salesperson": self.sp.id,
            "customer_name": "عميل قديم",
            "sale_month": 5,
            "sale_year": 2026,
            "is_cash_sale": False,
            "total_amount": 6000,
            "down_payment": 1000,
            "installment_system": "1000 x 5",
            "products_text": "غرفة نوم كاملة",
            "installment_payments": [
                {"payment_month": 6, "payment_year": 2026, "amount": 1000},
                {"payment_month": 7, "payment_year": 2026, "amount": 1000},
                {"payment_month": 8, "payment_year": 2026, "amount": 1000},
                {"payment_month": 9, "payment_year": 2026, "amount": 1000},
                {"payment_month": 10, "payment_year": 2026, "amount": 1000},
            ],
        }
        res_valid = self.client.post("/api/v1/receipts/", valid_data, format="json")
        self.assertEqual(res_valid.status_code, status.HTTP_201_CREATED)

        # Verify balance was NOT deducted
        lic.refresh_from_db()
        self.assertEqual(lic.invoices_balance, initial_balance)

        # Verify stock was NOT deducted
        new_stock = self.item.get_stock_at_date(5, 2026)
        self.assertEqual(new_stock, initial_stock)

        # Verify scheduled installments in 06/2026 are included in collection inflows
        from api.services.financial_service import calculate_cash_drawer_summary
        drawer_m6 = calculate_cash_drawer_summary(self.branch.id, 6, 2026)
        self.assertEqual(drawer_m6["collection_inflow"], 1000)

    def test_unauthenticated_backup_upload_access(self):
        """Test BackupUploadView allows unauthenticated access for setup and login restore."""
        self.client.logout()
        res = self.client.post("/api/v1/tools/backup/upload/", {})
        # Should NOT be 401 Unauthorized or 403 Forbidden; should be 400 Bad Request because no file was attached
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res.data)
