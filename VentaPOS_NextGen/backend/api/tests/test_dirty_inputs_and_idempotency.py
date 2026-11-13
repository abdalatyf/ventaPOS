from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from api.models import (
    Branch,
    Salesperson,
    InventoryItem,
    CommissionHistory,
    InventoryAdjustment,
    Supplier,
    PurchaseInvoice,
    Receipt,
    SaleItem,
    InstallmentPayment,
    Expense,
    CompanySetting,
    ClientLicense,
)
from api.utils.security_utils import get_machine_id, generate_record_signature


class DirtyInputsAndCrossBranchTests(TestCase):
    """
    Wave 2 Backend Adversarial Suite:
    - Dirty numeric strings, Arabic-Indic numerals, grouping commas, negative/zero bounds
    - Out-of-range months/years & malformed payloads (must return 400, never 500)
    - Cross-branch FK isolation across Receipt, PurchaseInvoice, CommissionHistory,
      InventoryAdjustment, and ReceiptViewSet.bulk_delete
    - Whitespace-only names & XSS/SQL-like literal storage safety
    """

    def setUp(self):
        self.client = APIClient()
        self.admin_user, _ = User.objects.get_or_create(
            username="admin", defaults={"is_superuser": True}
        )
        self.client.force_authenticate(user=self.admin_user)

        self.branch1 = Branch.objects.create(name="فرع القاهرة")
        self.branch2 = Branch.objects.create(name="فرع الإسكندرية")

        self.sp1 = Salesperson.objects.create(branch=self.branch1, name="مندوب فرع 1")
        self.sp2 = Salesperson.objects.create(branch=self.branch2, name="مندوب فرع 2")

        self.sup1 = Supplier.objects.create(branch=self.branch1, name="مورد فرع 1")
        self.sup2 = Supplier.objects.create(branch=self.branch2, name="مورد فرع 2")
        self.sup_shared = Supplier.objects.create(branch=None, name="مورد مشترك")

        self.item1 = InventoryItem.objects.create(
            branch=self.branch1,
            name="ثلاجة فرع 1",
            initial_quantity=20,
            initial_purchase_price=Decimal("5000.00"),
            initial_commission_amount=Decimal("100.00"),
            initial_month=1,
            initial_year=2026,
        )
        self.item2 = InventoryItem.objects.create(
            branch=self.branch2,
            name="غسالة فرع 2",
            initial_quantity=20,
            initial_purchase_price=Decimal("4000.00"),
            initial_commission_amount=Decimal("80.00"),
            initial_month=1,
            initial_year=2026,
        )

        CompanySetting.objects.create(
            name="مؤسسة الاختبار",
            phone1="01000000000",
            collection_commission_rate=Decimal("0.10"),
        )

        self.mach_id = get_machine_id()
        start = date(2026, 1, 1)
        expiry = date(2027, 12, 1)
        sig = generate_record_signature(str(expiry), 5000, self.mach_id, 1, True)
        self.license = ClientLicense.objects.create(
            company_code=1001,
            product_id=1,
            start_date=start,
            expiry_date=expiry,
            invoices_balance=5000,
            is_active=True,
            machine_id=self.mach_id,
            license_code_hash=sig,
        )

    def test_arabic_indic_numerals_and_commas_accepted_on_receipt_purchase_and_expense(self):
        res_pur = self.client.post(
            "/api/v1/purchase-invoices/",
            {
                "branch": self.branch1.id,
                "supplier": self.sup1.id,
                "invoice_type": "PURCHASE",
                "invoice_month": "٦",
                "invoice_year": "٢٠٢٦",
                "items": [
                    {
                        "inventory_item": self.item1.id,
                        "quantity": "٥",
                        "purchase_price": "٥٬٢٠٠",
                    }
                ],
            },
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch1.id),
        )
        self.assertEqual(res_pur.status_code, status.HTTP_201_CREATED, res_pur.content)
        inv = PurchaseInvoice.objects.get(id=res_pur.data["id"])
        self.assertEqual(inv.invoice_month, 6)
        self.assertEqual(inv.invoice_year, 2026)

        res_rcpt = self.client.post(
            "/api/v1/receipts/",
            {
                "branch": self.branch1.id,
                "salesperson": self.sp1.id,
                "customer_name": "   عميل أرقام هندية   ",
                "is_cash_sale": False,
                "sale_month": "٦",
                "sale_year": "٢٠٢٦",
                "total_amount": "٧٬٠٠٠",
                "down_payment": "١٬٠٠٠",
                "installment_system": "6*1000",
                "items": [
                    {
                        "inventory_item": self.item1.id,
                        "quantity": "١",
                        "unit_price": "٧٬٠٠٠",
                    }
                ],
                "installments": [
                    {"payment_month": "٧", "payment_year": "٢٠٢٦", "amount": "٦٬٠٠٠"}
                ],
            },
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch1.id),
        )
        self.assertEqual(res_rcpt.status_code, status.HTTP_201_CREATED, res_rcpt.content)
        rcpt = Receipt.objects.get(id=res_rcpt.data["id"])
        self.assertEqual(rcpt.customer_name, "عميل أرقام هندية")
        self.assertEqual(rcpt.sale_month, 6)
        self.assertEqual(rcpt.total_amount, 7000)

        res_exp = self.client.post(
            "/api/v1/expenses/",
            {
                "branch": self.branch1.id,
                "description": "إيجار شهر يونيو",
                "category": "إيجارات",
                "amount": "١٬٥٠٠",
                "expense_month": "٦",
                "expense_year": "٢٠٢٦",
            },
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch1.id),
        )
        self.assertEqual(res_exp.status_code, status.HTTP_201_CREATED, res_exp.content)
        exp = Expense.objects.get(id=res_exp.data["id"])
        self.assertEqual(exp.amount, 1500)
        self.assertEqual(exp.expense_month, 6)

    def test_dirty_receipt_and_installment_dates_and_bounds_return_400_never_500(self):
        bad_payloads = [
            # Invalid month 0 / 13 / -5 / non-numeric
            {"sale_month": 0, "sale_year": 2026},
            {"sale_month": 13, "sale_year": 2026},
            {"sale_month": -5, "sale_year": 2026},
            {"sale_month": "abc", "sale_year": 2026},
            {"sale_month": 6, "sale_year": -5},
            {"sale_month": 6, "sale_year": 9999},
            # Negative / zero quantities & prices
            {"total_amount": 0, "down_payment": 0, "items": [{"inventory_item": self.item1.id, "quantity": 0, "unit_price": 1000}]},
            {"total_amount": -500, "down_payment": 0, "items": [{"inventory_item": self.item1.id, "quantity": 1, "unit_price": -500}]},
            # Whitespace-only customer_name on installment receipt
            {"is_cash_sale": False, "customer_name": "   ", "total_amount": 2000, "down_payment": 2000, "installments": []},
            # Negative down_payment & down_payment > total
            {"is_cash_sale": False, "down_payment": -100, "total_amount": 2000},
            {"is_cash_sale": False, "down_payment": 3000, "total_amount": 2000},
            # Installment dirty payment_month / negative amount (previously crashed 500 inside int()/datetime.date)
            {
                "is_cash_sale": False,
                "total_amount": 2000,
                "down_payment": 1000,
                "installments": [{"payment_month": "abc", "payment_year": 2026, "amount": 1000}],
            },
            {
                "is_cash_sale": False,
                "total_amount": 2000,
                "down_payment": 1000,
                "installments": [{"payment_month": 13, "payment_year": 2026, "amount": 1000}],
            },
            {
                "is_cash_sale": False,
                "total_amount": 2000,
                "down_payment": 2500,
                "installments": [{"payment_month": 7, "payment_year": 2026, "amount": -500}],
            },
        ]

        for extra in bad_payloads:
            payload = {
                "branch": self.branch1.id,
                "salesperson": self.sp1.id,
                "customer_name": "عميل تجربة",
                "is_cash_sale": True,
                "sale_month": 6,
                "sale_year": 2026,
                "total_amount": 6000,
                "down_payment": 0,
                "items": [{"inventory_item": self.item1.id, "quantity": 1, "unit_price": 6000}],
            }
            payload.update(extra)
            res = self.client.post("/api/v1/receipts/", payload, format="json", HTTP_X_BRANCH_ID=str(self.branch1.id))
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST, f"Expected 400 for {extra}, got {res.status_code}: {res.content}")

        # Cash sale with whitespace-only customer_name defaults cleanly to عميل نقدي
        cash_res = self.client.post(
            "/api/v1/receipts/",
            {
                "branch": self.branch1.id,
                "salesperson": self.sp1.id,
                "customer_name": "   ",
                "is_cash_sale": True,
                "sale_month": 6,
                "sale_year": 2026,
                "total_amount": 6000,
                "down_payment": 0,
                "items": [{"inventory_item": self.item1.id, "quantity": 1, "unit_price": 6000}],
            },
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch1.id),
        )
        self.assertEqual(cash_res.status_code, status.HTTP_201_CREATED, cash_res.content)
        self.assertEqual(Receipt.objects.get(id=cash_res.data["id"]).customer_name, "عميل نقدي")

    def test_cross_branch_fk_isolation_enforced(self):
        # 1. Receipt in branch 2 with salesperson from branch 1 -> 400
        res1 = self.client.post(
            "/api/v1/receipts/",
            {
                "branch": self.branch2.id,
                "salesperson": self.sp1.id,
                "customer_name": "عميل",
                "is_cash_sale": True,
                "sale_month": 6,
                "sale_year": 2026,
                "total_amount": 5000,
                "down_payment": 0,
                "items": [{"inventory_item": self.item2.id, "quantity": 1, "unit_price": 5000}],
            },
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch2.id),
        )
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST, res1.content)

        # 2. Receipt in branch 2 with item from branch 1 -> 400
        res2 = self.client.post(
            "/api/v1/receipts/",
            {
                "branch": self.branch2.id,
                "salesperson": self.sp2.id,
                "customer_name": "عميل",
                "is_cash_sale": True,
                "sale_month": 6,
                "sale_year": 2026,
                "total_amount": 5000,
                "down_payment": 0,
                "items": [{"inventory_item": self.item1.id, "quantity": 1, "unit_price": 5000}],
            },
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch2.id),
        )
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST, res2.content)

        # 3. Purchase in branch 2 with supplier from branch 1 -> 400
        res3 = self.client.post(
            "/api/v1/purchase-invoices/",
            {
                "branch": self.branch2.id,
                "supplier": self.sup1.id,
                "invoice_type": "PURCHASE",
                "invoice_month": 6,
                "invoice_year": 2026,
                "items": [{"inventory_item": self.item2.id, "quantity": 2, "purchase_price": 4000}],
            },
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch2.id),
        )
        self.assertEqual(res3.status_code, status.HTTP_400_BAD_REQUEST, res3.content)

        # 4. Purchase in branch 2 with item from branch 1 -> 400
        res4 = self.client.post(
            "/api/v1/purchase-invoices/",
            {
                "branch": self.branch2.id,
                "supplier": self.sup2.id,
                "invoice_type": "PURCHASE",
                "invoice_month": 6,
                "invoice_year": 2026,
                "items": [{"inventory_item": self.item1.id, "quantity": 2, "purchase_price": 5000}],
            },
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch2.id),
        )
        self.assertEqual(res4.status_code, status.HTTP_400_BAD_REQUEST, res4.content)

        # 5. Legacy shared supplier (branch=None) succeeds in branch 2
        res5 = self.client.post(
            "/api/v1/purchase-invoices/",
            {
                "branch": self.branch2.id,
                "supplier": self.sup_shared.id,
                "invoice_type": "PURCHASE",
                "invoice_month": 6,
                "invoice_year": 2026,
                "items": [{"inventory_item": self.item2.id, "quantity": 2, "purchase_price": 4000}],
            },
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch2.id),
        )
        self.assertEqual(res5.status_code, status.HTTP_201_CREATED, res5.content)

        # 6. CommissionHistory on branch 1 item while X-Branch-ID=2 -> 400
        res6 = self.client.post(
            "/api/v1/commission-history/",
            {"item": self.item1.id, "commission_amount": 50, "activation_month": 6, "activation_year": 2026},
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch2.id),
        )
        self.assertEqual(res6.status_code, status.HTTP_400_BAD_REQUEST, res6.content)

    def test_commission_adjustment_dimensions_expense_and_settings_validation(self):
        # CommissionHistory: create valid, then reject negative overwrite & dirty month
        ok_comm = self.client.post(
            "/api/v1/commission-history/",
            {"item": self.item1.id, "commission_amount": 120, "activation_month": 6, "activation_year": 2026},
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch1.id),
        )
        self.assertEqual(ok_comm.status_code, status.HTTP_201_CREATED)

        neg_overwrite = self.client.post(
            "/api/v1/commission-history/",
            {"item": self.item1.id, "commission_amount": -50, "activation_month": 6, "activation_year": 2026},
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch1.id),
        )
        self.assertEqual(neg_overwrite.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CommissionHistory.objects.get(id=ok_comm.data["id"]).commission_amount, Decimal("120.00"))

        bad_comm_month = self.client.post(
            "/api/v1/commission-history/",
            {"item": self.item1.id, "commission_amount": 80, "activation_month": "abc", "activation_year": 2026},
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch1.id),
        )
        self.assertEqual(bad_comm_month.status_code, status.HTTP_400_BAD_REQUEST)

        # InventoryAdjustment (deficit): 0 qty and bad month rejected; > safe stock rejected
        self.assertEqual(
            self.client.post(
                "/api/v1/inventory-adjustments/",
                {"item": self.item1.id, "quantity": 0, "month": 6, "year": 2026},
                format="json",
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.client.post(
                "/api/v1/inventory-adjustments/",
                {"item": self.item1.id, "quantity": 1, "month": 13, "year": 2026},
                format="json",
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        # Whitespace names rejected across dimensions & expenses
        for url, payload in [
            ("/api/v1/branches/", {"name": "   "}),
            ("/api/v1/salespersons/", {"branch": self.branch1.id, "name": "   "}),
            ("/api/v1/suppliers/", {"branch": self.branch1.id, "name": "   "}),
            ("/api/v1/expenses/", {"branch": self.branch1.id, "description": "   ", "amount": 100, "expense_month": 6, "expense_year": 2026}),
            ("/api/v1/expenses/", {"branch": self.branch1.id, "description": "كهرباء", "amount": 0, "expense_month": 6, "expense_year": 2026}),
            ("/api/v1/expenses/", {"branch": self.branch1.id, "description": "كهرباء", "amount": 100, "expense_month": 0, "expense_year": 2026}),
            ("/api/v1/company-settings/", {"name": "شركة", "collection_commission_rate": -1}),
            ("/api/v1/company-settings/", {"name": "شركة", "zoom_level": 9}),
            ("/api/v1/purchase-invoices/", {"branch": self.branch1.id, "supplier": self.sup1.id, "invoice_month": 6, "invoice_year": 2026, "items": []}),
        ]:
            r = self.client.post(url, payload, format="json", HTTP_X_BRANCH_ID=str(self.branch1.id))
            self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST, f"Expected 400 on {url} {payload}: {r.content}")

    def test_dirty_query_filters_bulk_delete_desktop_print_and_returns_no_500(self):
        r1 = Receipt.objects.create(
            branch=self.branch1, salesperson=self.sp1, receipt_number=101,
            customer_name="عميل 1", is_cash_sale=False, total_amount=4000, down_payment=1000,
            sale_month=5, sale_year=2026, is_confirmed=True
        )
        SaleItem.objects.create(receipt=r1, inventory_item=self.item1, quantity=2, unit_price=2000)
        r2 = Receipt.objects.create(
            branch=self.branch2, salesperson=self.sp2, receipt_number=101,
            customer_name="عميل 2", is_cash_sale=True, total_amount=4000, down_payment=0,
            sale_month=5, sale_year=2026, is_confirmed=True
        )

        # Dirty list query params must not 500
        self.assertEqual(self.client.get("/api/v1/receipts/?salesperson_id=abc&month=١٣&year=bad").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/purchase-invoices/?month=abc&supplier=xyz&invoice_number=nope").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/commission-history/?item_id=abc").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/inventory-adjustments/?item_id=abc").status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/inventory-items/{self.item1.id}/stock/?month=13&year=2026").status_code, 400)

        # bulk_delete & desktop_print reject non-int / empty IDs with 400 and respect branch isolation
        self.assertEqual(self.client.post("/api/v1/receipts/bulk_delete/", {"receipt_ids": []}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/v1/receipts/bulk_delete/", {"receipt_ids": ["abc"]}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/v1/receipts/desktop_print/", {"receipt_ids": ["abc"]}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/v1/purchase-invoices/desktop_print/", {"invoice_ids": ["abc"]}, format="json").status_code, 400)

        # Bulk delete with X-Branch-ID=1 must NOT delete branch 2 receipt r2
        bulk_res = self.client.post(
            "/api/v1/receipts/bulk_delete/",
            {"receipt_ids": [r2.id]},
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch1.id),
        )
        self.assertEqual(bulk_res.status_code, 200)
        self.assertEqual(bulk_res.data["deleted_count"], 0)
        self.assertTrue(Receipt.objects.filter(id=r2.id, is_deleted=False).exists())

        # Return receipt dirty inputs return 400 cleanly, never 500
        for bad_ret in [
            {"returned_items": [], "return_month": 6, "return_year": 2026},
            {"returned_items": [{"inventory_item_id": self.item1.id, "quantity": "abc"}], "return_month": 6, "return_year": 2026},
            {"returned_items": [{"inventory_item_id": self.item1.id, "quantity": -1}], "return_month": 6, "return_year": 2026},
            {"returned_items": [{"inventory_item_id": self.item1.id, "quantity": 1}], "return_month": 13, "return_year": 2026},
            {
                "returned_items": [{"inventory_item_id": self.item1.id, "quantity": 1}],
                "return_month": 6,
                "return_year": 2026,
                "new_installments": [{"payment_month": 13, "payment_year": 2026, "amount": 1000}],
            },
            {
                "returned_items": [{"inventory_item_id": self.item1.id, "quantity": 1}],
                "return_month": 6,
                "return_year": 2026,
                "new_installments": [{"payment_month": 7, "payment_year": 2026, "amount": -1000}],
            },
        ]:
            rr = self.client.post(f"/api/v1/receipts/{r1.id}/return_receipt/", bad_ret, format="json")
            self.assertEqual(rr.status_code, status.HTTP_400_BAD_REQUEST, f"Expected 400 on return {bad_ret}: {rr.content}")

    def test_xss_and_sql_like_strings_stored_safely_without_crash(self):
        xss = "<script>alert('xss')</script>"
        sqli = "'; DROP TABLE api_receipt; --"
        res = self.client.post(
            "/api/v1/receipts/",
            {
                "branch": self.branch1.id,
                "salesperson": self.sp1.id,
                "customer_name": xss,
                "area": sqli,
                "is_cash_sale": True,
                "sale_month": 6,
                "sale_year": 2026,
                "total_amount": 5000,
                "down_payment": 0,
                "items": [{"inventory_item": self.item1.id, "quantity": 1, "unit_price": 5000}],
            },
            format="json",
            HTTP_X_BRANCH_ID=str(self.branch1.id),
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        saved = Receipt.objects.get(id=res.data["id"])
        self.assertEqual(saved.customer_name, xss)
        self.assertEqual(saved.area, sqli)
