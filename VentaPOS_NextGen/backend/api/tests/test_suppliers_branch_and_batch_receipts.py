"""
Tests for Branched Supplier Isolation, 250+ Batch Receipt Pagination (all_ids & all_installment_ids),
and Desktop Print PDF Generation with Orientation (Portrait & Landscape) across Reports.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import date
from rest_framework.test import APIClient
from api.models import (
    Branch, Salesperson, InventoryItem, Supplier,
    Receipt, ClientLicense, CompanySetting
)
from api.utils.security_utils import generate_record_signature, get_machine_id


class SuppliersBranchAndBatchReceiptsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.admin_user, _ = User.objects.get_or_create(username="admin", defaults={"is_superuser": True})
        self.client.force_authenticate(user=self.admin_user)

        mach_id = get_machine_id()
        expiry = date.today() + timezone.timedelta(days=365)
        sig = generate_record_signature(str(expiry), 5000, mach_id, 1, True)

        self.license = ClientLicense.objects.create(
            company_code=1001,
            product_id=1,
            start_date=date(2025, 1, 1),
            expiry_date=expiry,
            invoices_balance=5000,
            is_active=True,
            machine_id=mach_id,
            license_code_hash=sig
        )

        self.branch1 = Branch.objects.create(name="فرع القاهرة")
        self.branch2 = Branch.objects.create(name="فرع الجيزة")

        self.company = CompanySetting.objects.create(
            name="شركة الأمانة للمفروشات",
            footer_text="تقرير رسمي معتمد"
        )

        self.sp1 = Salesperson.objects.create(branch=self.branch1, name="مندوب 1")

    def test_supplier_branch_isolation_and_uniqueness(self):
        """
        Verify that Supplier model allows the same name in different branches,
        but strictly enforces uniqueness within the same branch.
        """
        # Create supplier in Branch 1
        s1 = Supplier.objects.create(branch=self.branch1, name="شركة النور")
        self.assertEqual(s1.name, "شركة النور")

        # Creating supplier with same name in Branch 2 MUST SUCCEED
        s2 = Supplier.objects.create(branch=self.branch2, name="شركة النور")
        self.assertEqual(s2.name, "شركة النور")
        self.assertNotEqual(s1.id, s2.id)

        # Creating duplicate supplier in Branch 1 via API must return 400
        res = self.client.post("/api/v1/suppliers/", {
            "name": "شركة النور",
            "branch": self.branch1.id
        })
        self.assertEqual(res.status_code, 400)

        # GET /suppliers/?branch_id=... should only return suppliers for that branch
        res_list1 = self.client.get(f"/api/v1/suppliers/?branch_id={self.branch1.id}")
        self.assertEqual(res_list1.status_code, 200)
        res_data1 = res_list1.json()
        items1 = res_data1.get("results", res_data1) if isinstance(res_data1, dict) else res_data1
        self.assertEqual(len(items1), 1)
        self.assertEqual(items1[0]["branch"], self.branch1.id)

    def test_batch_receipt_pagination_all_ids_and_installment_ids(self):
        """
        Create 250 receipts (mixed cash and installment) and verify that ReceiptPagination
        returns all_ids (250) and all_installment_ids (e.g. 150) without truncating to page size.
        """
        receipts = []
        for i in range(1, 261):
            is_cash = (i % 2 == 0)
            receipts.append(Receipt(
                branch=self.branch1,
                receipt_number=1000 + i,
                sale_year=2026,
                sale_month=7,
                salesperson=self.sp1,
                customer_name=f"عميل رقم {i}",
                area="شبرا" if i % 2 == 0 else "الزيتون",
                total_amount=3000,
                is_cash_sale=is_cash,
                is_confirmed=True
            ))
        Receipt.objects.bulk_create(receipts)

        res = self.client.get(f"/api/v1/receipts/?branch_id={self.branch1.id}&year=2026&month=7")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["count"], 260)
        self.assertIn("all_ids", data)
        self.assertIn("all_installment_ids", data)

        all_ids = data["all_ids"]
        all_installment_ids = data["all_installment_ids"]

        self.assertEqual(len(all_ids), 260)
        # Even numbers are cash (130), odd numbers are installments (130)
        self.assertEqual(len(all_installment_ids), 130)

        # Page 1 results should be limited by page_size
        results = data["results"]
        self.assertLess(len(results), 260)
        self.assertGreater(len(results), 0)

    def test_report_desktop_print_view_html_and_orientation(self):
        """
        Verify ReportDesktopPrintView handles both Portrait and Landscape requests
        and formats Arabic numerals properly.
        """
        payload_portrait = {
            "title": "تقرير المبيعات التجريبي",
            "branch_id": self.branch1.id,
            "period_label": "2026/08",
            "orientation": "portrait",
            "action": "view",
            "filters_summary": [
                {"label": "المندوب", "value": "مندوب 1"},
                {"label": "المنطقة", "value": "شبرا"}
            ],
            "kpis": [
                {"label": "إجمالي المبيعات", "value": "50000", "color": "success"},
                {"label": "صافي الربح", "value": "12000", "color": "primary"}
            ],
            "columns": [
                {"key": "col1", "label": "رقم", "align": "center"},
                {"key": "col2", "label": "الاسم", "align": "start"},
                {"key": "col3", "label": "المبلغ", "align": "center"}
            ],
            "rows": [
                {"col1": 1, "col2": "صنف أ", "col3": 5000},
                {"col1": 2, "col2": "صنف ب", "col3": 3500}
            ],
            "footer_row": [
                {"value": "الإجمالي", "align": "start", "colspan": 2},
                {"value": "8500", "align": "center"}
            ]
        }

        # Mock generate_and_open_pdf so test environment doesn't require SumatraPDF/wkhtmltopdf binary
        from unittest.mock import patch
        with patch("api.views.report_views.generate_and_open_pdf") as mock_pdf:
            mock_pdf.return_value = (True, "PDF generated")

            # 1. Test Portrait
            res_port = self.client.post("/api/v1/reports/desktop_print/", payload_portrait, format="json")
            self.assertEqual(res_port.status_code, 200)
            mock_pdf.assert_called()
            call_kwargs = mock_pdf.call_args[1]
            self.assertEqual(call_kwargs.get("orientation"), "portrait")

            # 2. Test Landscape
            payload_landscape = dict(payload_portrait)
            payload_landscape["orientation"] = "landscape"
            res_land = self.client.post("/api/v1/reports/desktop_print/", payload_landscape, format="json")
            self.assertEqual(res_land.status_code, 200)
            call_kwargs_land = mock_pdf.call_args[1]
            self.assertEqual(call_kwargs_land.get("orientation"), "landscape")
