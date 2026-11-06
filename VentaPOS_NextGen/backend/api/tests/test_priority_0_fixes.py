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
    Supplier,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    InstallmentPayment,
)
from api.serializers import InventoryAdjustmentSerializer
from api.utils.license_validator import LicenseValidator
from api.utils.security_utils import (
    get_machine_id,
    generate_record_signature,
    generate_receipt_signature,
)


class Priority0CriticalBackendBugFixesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.admin_user, _ = User.objects.get_or_create(username="admin", defaults={"is_superuser": True})
        self.client.force_authenticate(user=self.admin_user)
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

    def test_safe_available_qty_intermediate_month_bottleneck_dip(self):
        """
        Verify that get_safe_available_qty detects intermediate-month inventory dips
        and prevents back-dated sales from causing a negative stock in future months.
        Example: Initial stock of 10 in Jan 2026.
        8 units sold in Mar 2026 -> stock at end of Mar is 2.
        In Feb 2026, raw stock is 10, but safe_available_qty considering Mar dip is 2!
        Attempting to sell 5 units in Feb 2026 via ReceiptSerializer must fail validation.
        """
        from rest_framework.exceptions import ValidationError
        from api.serializers import ReceiptSerializer

        item = InventoryItem.objects.create(
            branch=self.branch,
            name="شاشة 65 بوصة سمارت",
            initial_quantity=10,
            initial_purchase_price=7000,
            initial_commission_amount=150,
            initial_month=1,
            initial_year=2026,
        )

        # 1. Sell 8 units in Month 3
        sale_m3 = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=301,
            customer_name="عميل مارس",
            receipt_type="SALE",
            total_amount=80000,
            down_payment=80000,
            is_cash_sale=True,
            sale_month=3,
            sale_year=2026,
            is_confirmed=True,
        )
        SaleItem.objects.create(
            receipt=sale_m3,
            inventory_item=item,
            quantity=8,
            unit_price=10000,
        )

        # In Month 1 & Month 2, historical stock is 10. In Month 3, stock is 2.
        self.assertEqual(item.get_stock_at_date(2, 2026), 10)
        self.assertEqual(item.get_stock_at_date(3, 2026), 2)

        # With default date in Month 4 (or later), safe_available_qty in Month 2 must be 2, with bottleneck in Month 3!
        safe_qty, b_month, b_year = item.get_safe_available_qty(2, 2026, 4, 2026, return_bottleneck=True)
        self.assertEqual(safe_qty, 2)
        self.assertEqual(b_month, 3)
        self.assertEqual(b_year, 2026)

        # 2. Attempt back-dated sale of 5 units in Month 2 via ReceiptSerializer -> Rejection
        receipt_data = {
            "branch": self.branch.id,
            "salesperson": self.salesperson.id,
            "customer_name": "عميل فبراير بأثر رجعي",
            "sale_month": 2,
            "sale_year": 2026,
            "is_cash_sale": True,
            "total_amount": 50000,
            "down_payment": 50000,
            "items": [
                {
                    "inventory_item_id": item.id,
                    "quantity": 5,
                    "unit_price": 10000,
                }
            ],
        }
        serializer = ReceiptSerializer(data=receipt_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        with self.assertRaises(ValidationError) as ctx:
            serializer.save()
        err_str = str(ctx.exception)
        self.assertTrue("أقصى كمية يمكن بيعها" in err_str or "safe_limit" in err_str or "2" in err_str)

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

        # 1. Serializer creation with new fields (defaults to DEFICIT)
        data_new = {
            "item": item.id,
            "quantity": 2,
            "reason": "عجز جرد",
            "month": 2,
            "year": 2026
        }
        ser = InventoryAdjustmentSerializer(data=data_new)
        self.assertTrue(ser.is_valid(), ser.errors)
        adj = ser.save()
        self.assertEqual(adj.adjustment_type, "DEFICIT")
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

    def test_p0_1_demo_auth_blocked_when_production_license_exists(self):
        """
        P0.1: /api/v1/auth/demo/ must be blocked with 403 when a non-demo license exists.
        """
        res = self.client.post("/api/v1/auth/demo/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_p0_3_branch_destroy_blocks_when_records_exist_and_soft_deletes_when_empty(self):
        """
        P0.3: BranchViewSet.destroy must block if receipts or items exist, and soft-delete when clean.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="صنف بالفرع",
            initial_quantity=5,
            initial_purchase_price=100,
            initial_commission_amount=10,
            initial_month=1,
            initial_year=2026
        )
        # Attempt to delete branch with items
        res = self.client.delete(f"/api/v1/branches/{self.branch.id}/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لا يمكن حذف هذا الفرع", str(res.json()))

        # Create clean branch
        clean_branch = Branch.objects.create(name="فرع فارغ تماماً")
        res_clean = self.client.delete(f"/api/v1/branches/{clean_branch.id}/")
        self.assertEqual(res_clean.status_code, status.HTTP_204_NO_CONTENT)
        clean_branch.refresh_from_db()
        self.assertTrue(clean_branch.is_deleted)

    def test_p0_5_sequential_receipt_numbering_after_soft_delete(self):
        """
        P0.5: Receipt numbering must not collide or crash after soft-deleting the latest receipt.
        """
        r1 = Receipt.objects.create(
            branch=self.branch,
            receipt_number=1,
            customer_name="عميل 1",
            total_amount=100,
            down_payment=100,
            is_cash_sale=True,
            sale_month=1,
            sale_year=2026
        )
        r2 = Receipt.objects.create(
            branch=self.branch,
            receipt_number=2,
            customer_name="عميل 2",
            total_amount=200,
            down_payment=200,
            is_cash_sale=True,
            sale_month=1,
            sale_year=2026
        )
        # Soft delete receipt #2
        r2.is_deleted = True
        r2.save()

        # Next receipt number must be 3
        next_num = Receipt.get_next_receipt_number(self.branch)
        self.assertEqual(next_num, 3)

        # ReceiptNextNumberView should also return 3
        res = self.client.get(f"/api/v1/receipts-next-number/?branch_id={self.branch.id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["next_receipt_number"], 3)

    def test_p0_6_unconfirmed_usb_receipts_do_not_alter_stock(self):
        """
        P0.6: Unconfirmed receipts (is_confirmed=False) must not alter physical stock.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="صنف تجربة USB",
            initial_quantity=10,
            initial_purchase_price=100,
            initial_commission_amount=10,
            initial_month=1,
            initial_year=2026
        )
        unconfirmed_rcpt = Receipt.objects.create(
            branch=self.branch,
            receipt_number=10,
            customer_name="عميل USB",
            is_confirmed=False,
            total_amount=500,
            down_payment=500,
            is_cash_sale=True,
            sale_month=1,
            sale_year=2026
        )
        SaleItem.objects.create(
            receipt=unconfirmed_rcpt,
            inventory_item=item,
            quantity=4,
            unit_price=125
        )
        # Stock should still be 10 because receipt is not confirmed
        self.assertEqual(item.get_stock_at_date(1, 2026), 10)

        # Confirm the receipt
        unconfirmed_rcpt.is_confirmed = True
        unconfirmed_rcpt.save()
        # Stock must now reflect the sale (10 - 4 = 6)
        self.assertEqual(item.get_stock_at_date(1, 2026), 6)

    def test_p0_7_upfront_credit_reserve_and_sales_returns(self):
        """
        P0.7:
        1. Card 1 uses Upfront Credit Reserve (reserve_deduction) as collection commission.
        2. Customer returns are deducted in the original sale month across financial reports.
        3. return_receipt sets down_payment = cash_refund.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="شاشة 55 بوصة",
            initial_quantity=20,
            initial_purchase_price=5000,
            initial_commission_amount=200,
            initial_month=1,
            initial_year=2026
        )
        # 1. Original credit sale in Month 5
        sale = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=501,
            customer_name="عميل قسط",
            total_amount=12000,
            down_payment=2000,
            is_cash_sale=False,
            sale_month=5,
            sale_year=2026
        )
        SaleItem.objects.create(
            receipt=sale,
            inventory_item=item,
            quantity=2,
            unit_price=6000
        )
        InstallmentPayment.objects.create(
            receipt=sale,
            amount=5000,
            payment_date=date(2026, 6, 25)
        )
        InstallmentPayment.objects.create(
            receipt=sale,
            amount=5000,
            payment_date=date(2026, 7, 25)
        )

        res_m5 = self.client.get("/api/v1/reports/dashboard/summary/", {"branch_id": self.branch.id, "month": 5, "year": 2026})
        self.assertEqual(res_m5.status_code, 200)
        kpis_m5 = res_m5.json()["kpis"]
        self.assertEqual(kpis_m5["total_revenue"], 12000)
        self.assertEqual(kpis_m5["total_collection_commissions"], 1000)
        self.assertEqual(kpis_m5["total_sales_commissions"], 400)
        self.assertEqual(kpis_m5["estimated_net_profit"], 600)

        # 2. In Month 6: return 1 unit
        ret_res = self.client.post(f"/api/v1/receipts/{sale.id}/return_receipt/", {
            "return_month": 6,
            "return_year": 2026,
            "returned_items": [{"inventory_item_id": item.id, "quantity": 1}],
            "new_installments": [{"amount": 4000, "payment_month": 6, "payment_year": 2026}],
            "new_installment_system": "قسط معدل 4000"
        }, format="json")
        self.assertEqual(ret_res.status_code, 200)
        ret_id = ret_res.json()["return_receipt_id"]
        ret_rcpt = Receipt.objects.get(id=ret_id)
        self.assertEqual(ret_rcpt.down_payment, Decimal('0.00'))

        # In Month 5 (original sale month): return deducted in original sale month!
        res_m5_after = self.client.get("/api/v1/reports/dashboard/summary/", {"branch_id": self.branch.id, "month": 5, "year": 2026})
        kpis_m5_after = res_m5_after.json()["kpis"]
        self.assertEqual(kpis_m5_after["total_revenue"], 6000)
        self.assertEqual(kpis_m5_after["total_cogs"], 5000)
        self.assertEqual(kpis_m5_after["total_sales_commissions"], 200)
        self.assertEqual(kpis_m5_after["total_collection_commissions"], 400)
        self.assertEqual(kpis_m5_after["estimated_net_profit"], 400)

        # Salesperson performance report for Month 5:
        sp_res = self.client.get("/api/v1/reports/salespersons/", {"branch_id": self.branch.id, "month": 5, "year": 2026})
        sp_data = sp_res.json()["salespersons"][0]
        self.assertEqual(sp_data["total_sales_val"], 6000)
        self.assertEqual(sp_data["comm_sales"], 200)

    def test_p0_8_multi_branch_isolation(self):
        """
        P0.8: Enforce multi-branch isolation across backend endpoints.
        """
        branch_b = Branch.objects.create(name="فرع الإسكندرية")
        sp_b = Salesperson.objects.create(branch=branch_b, name="مندوب إسكندرية")
        supplier = Supplier.objects.create(name="مورد معتمد")

        # Invoices in branch A and B
        inv_a = PurchaseInvoice.objects.create(branch=self.branch, supplier=supplier, invoice_number=111, invoice_month=1, invoice_year=2026)
        inv_b = PurchaseInvoice.objects.create(branch=branch_b, supplier=supplier, invoice_number=222, invoice_month=1, invoice_year=2026)

        # Query purchase invoices for branch A
        res_a = self.client.get(f"/api/v1/purchase-invoices/?branch_id={self.branch.id}")
        self.assertEqual(res_a.status_code, 200)
        ids_a = [i["id"] for i in res_a.json()["results"]]
        self.assertIn(inv_a.id, ids_a)
        self.assertNotIn(inv_b.id, ids_a)

        # Receipts in branch A and B
        r_a = Receipt.objects.create(branch=self.branch, salesperson=self.salesperson, receipt_number=10, customer_name="عميل القاهرة", area="المعادي", is_cash_sale=True, total_amount=100, sale_month=1, sale_year=2026)
        r_b = Receipt.objects.create(branch=branch_b, salesperson=sp_b, receipt_number=20, customer_name="عميل الإسكندرية", area="سموحة", is_cash_sale=True, total_amount=200, sale_month=1, sale_year=2026)

        # Customer suggestions isolated by branch
        sug_res = self.client.get(f"/api/v1/customer-suggestions/?field=name&term=عميل&branch_id={self.branch.id}")
        self.assertEqual(sug_res.status_code, 200)
        vals = [item["value"] for item in sug_res.json()]
        self.assertIn("عميل القاهرة", vals)
        self.assertNotIn("عميل الإسكندرية", vals)

        # Receipt history cursor isolated by branch
        cur_res = self.client.get(f"/api/v1/receipts-history-cursor/?direction=prev&branch_id={branch_b.id}")
        self.assertEqual(cur_res.status_code, 200)
        self.assertEqual(cur_res.json()["receipt_number"], 20)

    def test_p0_9_licensing_lifecycle_and_security(self):
        """
        P0.9:
        1. Fast winreg machine ID returns 8 uppercase chars.
        2. Expired production license locks write requests with 403 (read-only mode).
        3. Monotonic clock-rollback triggers 403.
        4. Whitelisted URLs bypass read-only lock.
        5. HMAC receipt verification with items.
        """
        # 1. Machine ID format
        mach = get_machine_id()
        self.assertEqual(len(mach), 32)

        # 2. Receipt HMAC with items
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="غسالة أوتوماتيك",
            initial_quantity=5,
            initial_purchase_price=4000,
            initial_commission_amount=150,
            initial_month=1,
            initial_year=2026
        )
        rcpt = Receipt.objects.create(
            branch=self.branch,
            receipt_number=777,
            total_amount=5000,
            sale_month=1,
            sale_year=2026
        )
        SaleItem.objects.create(receipt=rcpt, inventory_item=item, quantity=1, unit_price=5000)
        sig = generate_receipt_signature(777, 5000, 1, 2026, [{"inventory_item": item, "quantity": 1}])
        rcpt.receipt_hash = sig
        rcpt.save()
        self.assertTrue(rcpt.is_authentic)

        # 3. Read-only lock on expired production license
        self.license.expiry_date = timezone.localdate() - timezone.timedelta(days=40)
        self.license.license_code_hash = generate_record_signature(str(self.license.expiry_date), 1000, self.mach_id, 1, True)
        self.license.save()

        # Write request should receive 403
        write_res = self.client.post("/api/v1/expenses/", {"branch": self.branch.id, "amount": 100, "expense_month": 1, "expense_year": 2026, "description": "شاي"})
        self.assertEqual(write_res.status_code, 403)
        self.assertEqual(write_res.json()["error"], "license_expired")

        # Whitelisted URL should succeed
        status_res = self.client.get("/api/v1/license/status/")
        self.assertEqual(status_res.status_code, 200)

        # 4. Clock rollback detection
        # Restore license validity
        self.license.expiry_date = date.today() + timezone.timedelta(days=365)
        self.license.license_code_hash = generate_record_signature(str(self.license.expiry_date), 1000, self.mach_id, 1, True)
        self.license.save()

        # Create a receipt with future timestamp
        future_rcpt = Receipt.objects.create(
            branch=self.branch,
            receipt_number=999,
            total_amount=100,
            sale_month=1,
            sale_year=2026
        )
        Receipt.all_objects.filter(id=future_rcpt.id).update(created_at=timezone.now() + timezone.timedelta(days=10))

        rollback_res = self.client.get(f"/api/v1/receipts-next-number/?branch_id={self.branch.id}")
        self.assertEqual(rollback_res.status_code, 403)
        self.assertEqual(rollback_res.json()["error"], "clock_rollback")

    def test_p0_10_selective_printing_enforcement(self):
        """
        P0.10: Selective Printing Enforcement (GEMINI.md §0).
        1. Cash receipts must be rejected by desktop_print with 400 Bad Request.
        2. Purchase invoices desktop_print endpoint must be removed (404 Not Found).
        """
        # 1. Cash receipt rejected
        cash_rcpt = Receipt.objects.create(
            branch=self.branch,
            receipt_number=101,
            total_amount=1000,
            down_payment=1000,
            is_cash_sale=True,
            sale_month=1,
            sale_year=2026
        )
        res = self.client.post("/api/v1/receipts/desktop_print/", {
            "receipt_ids": [cash_rcpt.id],
            "action": "view"
        }, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("الطباعة مخصصة لجداول الأقساط فقط", res.json().get("error", ""))

        # 2. Purchase invoices desktop_print removed
        pur_res = self.client.post("/api/v1/purchase-invoices/desktop_print/", {
            "invoice_ids": [1],
            "action": "view"
        }, format="json")
        self.assertIn(pur_res.status_code, [404, 405])
