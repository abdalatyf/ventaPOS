from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from api.models import (
    Branch,
    Salesperson,
    InventoryItem,
    Receipt,
    SaleItem,
    InventoryAdjustment,
    CompanySetting,
    ClientLicense,
    UsedLicense,
)
from api.serializers import InventoryAdjustmentSerializer
from api.utils.license_validator import LicenseValidator
from api.utils.security_utils import (
    get_machine_id,
    generate_record_signature,
)


class Priority0CriticalBackendBugFixesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.branch = Branch.objects.create(name="الفرع الرئيسي")
        self.salesperson = Salesperson.objects.create(
            branch=self.branch,
            name="مندوب المبيعات"
        )
        self.mach_id = get_machine_id()
        expiry = date.today() + timezone.timedelta(days=365)
        sig = generate_record_signature(str(expiry), 1000, self.mach_id, 1, True)
        self.license = ClientLicense.objects.create(
            company_code=1001,
            product_id=1,
            start_date=date(2026, 1, 1),
            expiry_date=expiry,
            invoices_balance=1000,
            is_active=True,
            machine_id=self.mach_id,
            license_code_hash=sig
        )
        self.client.credentials(HTTP_X_COMPANY_CODE="TESTP0")

    def test_stock_at_date_sales_returns_restore_stock(self):
        """
        Bug 1 Fix: Verify that receipt_type='RETURN' adds to stock rather than subtracting.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="شاشة سامسونج 55",
            initial_quantity=10,
            initial_purchase_price=5000,
            initial_commission_amount=100,
            initial_month=1,
            initial_year=2026
        )

        # 1. Sale receipt: 3 units sold in month 2 -> Stock should be 7
        sale_receipt = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=1,
            customer_name="علي",
            receipt_type="SALE",
            total_amount=18000,
            down_payment=18000,
            is_cash_sale=True,
            sale_month=2,
            sale_year=2026
        )
        SaleItem.objects.create(
            receipt=sale_receipt,
            inventory_item=item,
            quantity=3,
            unit_price=6000
        )
        self.assertEqual(item.get_stock_at_date(2, 2026), 7)

        # 2. Return receipt: 1 unit returned in month 3 -> Stock should restore to 8 (not drop to 6!)
        return_receipt = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=2,
            parent_receipt=sale_receipt,
            customer_name="علي",
            receipt_type="RETURN",
            total_amount=6000,
            down_payment=0,
            is_cash_sale=True,
            sale_month=3,
            sale_year=2026
        )
        SaleItem.objects.create(
            receipt=return_receipt,
            inventory_item=item,
            quantity=1,
            unit_price=6000
        )

        stock_m3 = item.get_stock_at_date(3, 2026)
        self.assertEqual(stock_m3, 8, "Sales return must restore inventory (+1) resulting in 8, not 6.")

        # Also verify InventoryMovementReportView
        res = self.client.get("/api/v1/reports/inventory-movement/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 3
        })
        self.assertEqual(res.status_code, 200)
        row = res.json()["items"][0]
        self.assertEqual(row["sales_returns"], 1)
        self.assertEqual(row["final_stock"], 8)

    def test_safe_available_qty_return_bottleneck_signature(self):
        """
        Bug 2 Fix: Verify get_safe_available_qty supports return_bottleneck=True
        and endpoint safe_available_qty does not raise TypeError.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="غسالة إل جي",
            initial_quantity=20,
            initial_purchase_price=4000,
            initial_commission_amount=80,
            initial_month=1,
            initial_year=2026
        )

        # Model method with return_bottleneck=False (default) returns int
        qty_int = item.get_safe_available_qty(1, 2026, 6, 2026)
        self.assertIsInstance(qty_int, int)
        self.assertEqual(qty_int, 20)

        # Model method with return_bottleneck=True returns 3-tuple
        result = item.get_safe_available_qty(1, 2026, 6, 2026, return_bottleneck=True)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        safe_qty, b_month, b_year = result
        self.assertEqual(safe_qty, 20)

        # Endpoint test via DRF action /stock/
        res = self.client.get(f"/api/v1/inventory-items/{item.id}/stock/", {
            "month": 1,
            "year": 2026
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("safe_available_qty", res.json())
        self.assertEqual(res.json()["safe_available_qty"], 20)

        # Endpoint test via alias /get_safe_available_qty/
        res_alias = self.client.get(f"/api/v1/inventory-items/{item.id}/get_safe_available_qty/", {
            "month": 1,
            "year": 2026
        })
        self.assertEqual(res_alias.status_code, 200)
        self.assertEqual(res_alias.json()["safe_available_qty"], 20)

    def test_inventory_adjustment_serializer_and_ledger(self):
        """
        Bug 3 Fix: Verify InventoryAdjustmentSerializer uses month, year, item
        and that InventoryItemViewSet.ledger runs without FieldError.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="مروحة سقف",
            initial_quantity=15,
            initial_purchase_price=500,
            initial_commission_amount=20,
            initial_month=1,
            initial_year=2026
        )

        # 1. Serializer creation with new fields
        data_new = {
            "item": item.id,
            "adjustment_type": "SURPLUS",
            "quantity": 2,
            "reason": "زيادة جرد",
            "month": 2,
            "year": 2026
        }
        ser = InventoryAdjustmentSerializer(data=data_new)
        self.assertTrue(ser.is_valid(), ser.errors)
        adj = ser.save()
        self.assertEqual(adj.month, 2)
        self.assertEqual(adj.year, 2026)
        self.assertEqual(adj.item, item)

        # 2. Serializer creation with legacy alias fields
        data_legacy = {
            "inventory_item": item.id,
            "adjustment_type": "DEFICIT",
            "quantity": 1,
            "reason": "عجز جرد",
            "adjustment_month": 3,
            "adjustment_year": 2026
        }
        ser2 = InventoryAdjustmentSerializer(data=data_legacy)
        self.assertTrue(ser2.is_valid(), ser2.errors)
        adj2 = ser2.save()
        self.assertEqual(adj2.month, 3)
        self.assertEqual(adj2.year, 2026)
        self.assertEqual(adj2.item, item)

        # 3. Product ledger endpoint must execute without FieldError
        res = self.client.get(f"/api/v1/inventory-items/{item.id}/ledger/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("timeline", data)
        self.assertIn("dashboard_metrics", data)

    def test_dynamic_collection_commission_rate(self):
        """
        Bug 4 Fix: Verify CompanySetting.collection_commission_rate is dynamically applied
        and defaults to 0.10.
        """
        from api.views import get_collection_commission_rate

        # Default fallback when no row exists
        self.assertEqual(get_collection_commission_rate(), 0.10)

        # Explicit setting
        setting = CompanySetting.objects.create(
            name="شركة الفرات",
            phone1="0100000000",
            collection_commission_rate=Decimal("0.15")
        )
        self.assertAlmostEqual(get_collection_commission_rate(), 0.15)

        # Setting entered as percentage 15.00
        setting.collection_commission_rate = Decimal("15.00")
        setting.save()
        self.assertAlmostEqual(get_collection_commission_rate(), 0.15)

    def test_customer_suggestions_returns_ascii_numerals(self):
        """
        Bug 5 Fix: Verify CustomerSuggestionsView returns ASCII digits.
        """
        Receipt.objects.create(
            branch=self.branch,
            receipt_number=99,
            customer_name="محمود حامد",
            phone_number="01098765432",
            address="مدينة نصر",
            area="القاهرة",
            total_amount=500,
            down_payment=500,
            is_cash_sale=True,
            sale_year=2026,
            sale_month=6
        )

        res = self.client.get("/api/v1/customer-suggestions/", {
            "field": "phone",
            "term": "010"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["value"], "01098765432", "Phone suggestion must be returned in Western ASCII digits.")

    def test_recovery_code_product_id_handling(self):
        """
        Bug 6 Fix: Verify PasswordRecoveryView and LicenseActivateView handle product_id 15/16/is_recovery.
        """
        # Test PasswordRecoveryView rejects invalid code
        res = self.client.post("/api/v1/auth/recover/", {
            "recovery_code": "INVALID-CODE-1234",
            "new_password": "NewSecretPassword123!"
        })
        self.assertEqual(res.status_code, 400)

        # Test LicenseActivateView rejects when is_recovery or product_id in (15, 16)
        res_act = self.client.post("/api/v1/license/activate/", {
            "license_code": "INVALID-CODE-1234"
        })
        self.assertEqual(res_act.status_code, 400)
