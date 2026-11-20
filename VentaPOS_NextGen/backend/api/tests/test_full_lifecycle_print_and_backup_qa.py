"""
Comprehensive Backend QA Suite (C1):
1. Full Lifecycle (Demo -> First Activation Wipe -> Setup -> Multi-Year Renewal -> Historical Reports)
2. Quota & Expiry Enforcement (0-balance exemptions, expired balance exclusion, latest-expiry lookup)
3. Auth & License Security (ChangePasswordView token rotation, PasswordRecoveryView 16 vs 15, replay canon)
4. LicenseStatusView Metadata (is_expired, company_name, earliest production start_date)
5. Backup & Auto-Updater Hardening (401 auth gates, corrupt/missing-table/rollback SQLite checks, launcher pending restore, version traversal)
6. PDF Print Engine Hardening (to_arabic_numerals decimals, UUID filenames, accounting sale/invoice dates, Arabic phone preservation, ReportDesktopPrintView auto-fetch)
"""
import os
import glob
import sqlite3
import tempfile
import unittest.mock
from datetime import date, timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from api.models import (
    Branch,
    ClientLicense,
    CompanySetting,
    InstallmentPayment,
    InventoryItem,
    LicenseHistory,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    Receipt,
    SaleItem,
    Salesperson,
    Supplier,
    UsedLicense,
)
from api.print_utils import ed2ad, to_arabic_numerals
from api.services.receipt_service import (
    get_active_license,
    get_first_production_license_start_date,
    get_subscription_date_bounds,
    is_pre_license_month,
)
from api.tests.test_licensing_and_security import mint_test_license_code
from api.utils.security_utils import generate_record_signature, get_machine_id

User = get_user_model()

REQUIRED_BACKUP_TABLES = (
    "salesapp_receipt",
    "salesapp_saleitem",
    "salesapp_inventoryitem",
    "salesapp_purchaseinvoice",
    "salesapp_branch",
    "salesapp_salesperson",
    "salesapp_companysetting",
    "salesapp_clientlicense",
)


def _create_sqlite_db(path: Path, tables=REQUIRED_BACKUP_TABLES, seed_marker="SEED"):
    conn = sqlite3.connect(str(path))
    try:
        for tbl in tables:
            conn.execute(f"CREATE TABLE IF NOT EXISTS {tbl} (id INTEGER PRIMARY KEY, label TEXT);")
        if "salesapp_companysetting" in tables:
            conn.execute("INSERT INTO salesapp_companysetting (label) VALUES (?);", (seed_marker,))
        conn.commit()
    finally:
        conn.close()


class FullLifecycleAndRenewalTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.mach_id = get_machine_id()
        self.admin_user, _ = User.objects.get_or_create(
            username="admin", defaults={"is_superuser": True, "is_staff": True}
        )
        self.admin_user.set_unusable_password()
        self.admin_user.save()

    def test_demo_to_activation_wipe_setup_multi_year_renewal_and_reports(self):
        # 1. Start in Demo Mode with sample data
        ClientLicense.all_objects.all().delete()
        ClientLicense.objects.create(
            company_code=1001,
            product_id=1,
            start_date=date(2026, 1, 1),
            expiry_date=date(2027, 1, 1),
            invoices_balance=500,
            is_active=True,
            machine_id="DEMO_MACHINE",
            license_code_hash="demo_hash",
        )
        demo_branch = Branch.objects.create(name="فرع تجريبي")
        demo_sp = Salesperson.objects.create(branch=demo_branch, name="مندوب تجريبي")
        Receipt.objects.create(
            branch=demo_branch,
            salesperson=demo_sp,
            receipt_number=1,
            customer_name="عميل تجريبي",
            total_amount=2000,
            down_payment=2000,
            is_cash_sale=True,
            sale_month=2,
            sale_year=2026,
        )

        # Verify demo status & demo auth
        st_demo = self.client.get("/api/v1/license/status/")
        self.assertEqual(st_demo.status_code, status.HTTP_200_OK)
        self.assertTrue(st_demo.json()["is_demo"])
        self.assertEqual(st_demo.json()["status"], "active")
        self.assertFalse(st_demo.json()["is_expired"])

        demo_tok = self.client.post("/api/v1/auth/demo/")
        self.assertEqual(demo_tok.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {demo_tok.json()['token']}")

        # 2. First production activation (Year 1: 2026-01-01 -> 2027-01-01) wipes demo data
        y1_code = mint_test_license_code(self.mach_id, product_id=4, year=2026, month=1)
        act1 = self.client.post("/api/v1/license/activate/", {"license_code": y1_code})
        self.assertEqual(act1.status_code, status.HTTP_201_CREATED)
        self.assertTrue(act1.json()["wiped_demo"])
        self.assertEqual(Branch.objects.count(), 0)
        self.assertEqual(Salesperson.objects.count(), 0)
        self.assertEqual(Receipt.objects.count(), 0)

        # Re-authenticate after wipe & complete setup
        self.client.force_authenticate(user=self.admin_user)
        CompanySetting.objects.update_or_create(
            id=1, defaults={"name": "شركة النور للأجهزة", "phone1": "٠١٠١٢٣٤٥٦٧٨", "collection_commission_rate": "0.10"}
        )
        branch = Branch.objects.create(name="الفرع الرئيسي")
        sp = Salesperson.objects.create(branch=branch, name="أحمد علي")
        item = InventoryItem.objects.create(
            branch=branch, name="ثلاجة ١٦ قدم", initial_purchase_price=10000, initial_commission_amount=100, initial_quantity=10
        )

        # Create Year-1 cash receipt in 2026/02 and pre-license receipt in 2025/12
        r_y1 = self.client.post(
            "/api/v1/receipts/",
            {
                "branch": branch.id,
                "salesperson": sp.id,
                "customer_name": "محمود حسن",
                "area": "المعادي",
                "total_amount": 15000,
                "down_payment": 15000,
                "is_cash_sale": True,
                "sale_month": 2,
                "sale_year": 2026,
                "items": [{"inventory_item_id": item.id, "quantity": 1, "unit_price": 15000}],
            },
            format="json",
        )
        self.assertEqual(r_y1.status_code, status.HTTP_201_CREATED)

        r_pre = self.client.post(
            "/api/v1/receipts/",
            {
                "branch": branch.id,
                "salesperson": sp.id,
                "customer_name": "عميل قديم",
                "area": "حلوان",
                "total_amount": 4000,
                "down_payment": 1000,
                "is_cash_sale": False,
                "installment_system": "قسطين",
                "sale_month": 12,
                "sale_year": 2025,
                "products_text": "بوتاجاز قديم",
                "items": [],
                "installments": [
                    {"amount": 1500, "payment_date": "2026-01-25"},
                    {"amount": 1500, "payment_date": "2026-02-25"},
                ],
            },
            format="json",
        )
        self.assertEqual(r_pre.status_code, status.HTTP_201_CREATED)

        # 3. Renew with Year-2 license (2027-01-01 -> 2028-01-01) -> preserves ALL data
        y2_code = mint_test_license_code(self.mach_id, product_id=4, year=2027, month=1)
        act2 = self.client.post("/api/v1/license/activate/", {"license_code": y2_code})
        self.assertEqual(act2.status_code, status.HTTP_201_CREATED)
        self.assertFalse(act2.json()["wiped_demo"])
        self.assertEqual(Branch.objects.count(), 1)
        self.assertEqual(Receipt.objects.count(), 2)
        self.assertGreaterEqual(LicenseHistory.objects.count(), 2)

        # Earliest production start date remains 2026-01-01 (not overwritten by 2027-01-01)
        self.assertEqual(get_first_production_license_start_date(), date(2026, 1, 1))
        self.assertFalse(is_pre_license_month(2026, 2))
        self.assertTrue(is_pre_license_month(2025, 12))

        st_y2 = self.client.get("/api/v1/license/status/").json()
        self.assertEqual(st_y2["start_date"], "2026-01-01")
        self.assertEqual(st_y2["company_name"], "شركة النور للأجهزة")
        self.assertFalse(st_y2["is_expired"])

        # All financial reports MUST still include Year-1 (2026/02) after Year-2 renewal
        params = {"branch_id": branch.id, "year": 2026, "month": 2}
        dash = self.client.get("/api/v1/reports/dashboard/summary/", params).json()
        self.assertEqual(int(dash["kpis"]["total_revenue"]), 15000)

        pnl = self.client.get("/api/v1/reports/sales-pl/", params).json()
        self.assertEqual(int(pnl["summary"]["grand_revenue"]), 15000)

        drawer = self.client.get("/api/v1/reports/cash-drawer-details/", params).json()
        self.assertEqual(sum(int(c["amount"]) for c in drawer["cash_sales"]), 15000)

        areas = self.client.get("/api/v1/reports/areas/", params).json()
        area_map = {a["area"]: a for a in areas["areas"]}
        self.assertIn("المعادي", area_map)
        self.assertEqual(area_map["المعادي"]["gross_sales"], 15000)
        if "حلوان" in area_map:
            self.assertEqual(area_map["حلوان"]["gross_sales"], 0)
            self.assertEqual(area_map["حلوان"]["due_installments_month"], 1500)

        # And pre-license month (2025/12) MUST remain excluded from all 4 reports
        pre_params = {"branch_id": branch.id, "year": 2025, "month": 12}
        self.assertEqual(int(self.client.get("/api/v1/reports/dashboard/summary/", pre_params).json()["kpis"]["total_revenue"]), 0)
        self.assertEqual(int(self.client.get("/api/v1/reports/sales-pl/", pre_params).json()["summary"]["grand_revenue"]), 0)
        self.assertEqual(sum(int(c["amount"]) for c in self.client.get("/api/v1/reports/cash-drawer-details/", pre_params).json()["cash_sales"]), 0)
        self.assertEqual(len(self.client.get("/api/v1/reports/areas/", pre_params).json()["areas"]), 0)


class QuotaAndExpiryEnforcementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.mach_id = get_machine_id()
        self.admin_user, _ = User.objects.get_or_create(
            username="admin", defaults={"is_superuser": True, "is_staff": True}
        )
        self.client.force_authenticate(user=self.admin_user)
        self.branch = Branch.objects.create(name="فرع الرصيد")
        self.sp = Salesperson.objects.create(branch=self.branch, name="مندوب الرصيد")
        self.item = InventoryItem.objects.create(
            branch=self.branch, name="غسالة أوتوماتيك", initial_purchase_price=8000, initial_quantity=5
        )

    def test_expired_quota_excluded_and_latest_expiry_selected(self):
        # Expired license holding 9000 leftover invoices + Active non-expired license with 25
        ClientLicense.all_objects.all().delete()
        ClientLicense.objects.create(
            machine_id=self.mach_id,
            product_id=4,
            start_date=date(2024, 1, 1),
            expiry_date=date(2025, 1, 1),
            invoices_balance=9000,
            is_active=True,
            license_code_hash="exp_old_hash",
        )
        newer_active = ClientLicense.objects.create(
            machine_id=self.mach_id,
            product_id=4,
            start_date=date(2026, 1, 1),
            expiry_date=date(2028, 1, 1),
            invoices_balance=25,
            is_active=True,
            license_code_hash=generate_record_signature(date(2028, 1, 1), 25, self.mach_id, 4, True),
        )

        self.assertEqual(get_active_license().id, newer_active.id)
        st = self.client.get("/api/v1/license/status/").json()
        self.assertFalse(st["is_expired"])
        # Expired 9000 balance MUST NOT be included in total_invoices_balance
        self.assertEqual(st["total_invoices_balance"], 25)

    def test_zero_balance_exemptions_for_pre_license_returns_bulk_delete_and_desktop_print(self):
        ClientLicense.all_objects.all().delete()
        ClientLicense.objects.create(
            machine_id=self.mach_id,
            product_id=4,
            start_date=date(2026, 1, 1),
            expiry_date=date(2028, 1, 1),
            invoices_balance=0,
            is_active=True,
            license_code_hash=generate_record_signature(date(2028, 1, 1), 0, self.mach_id, 4, True),
        )

        # Normal production receipt creation at 0 balance MUST be blocked with 403
        blocked = self.client.post(
            "/api/v1/receipts/",
            {
                "branch": self.branch.id,
                "salesperson": self.sp.id,
                "customer_name": "عميل مرفوض",
                "total_amount": 5000,
                "down_payment": 5000,
                "is_cash_sale": True,
                "sale_month": 3,
                "sale_year": 2026,
                "items": [{"inventory_item_id": self.item.id, "quantity": 1, "unit_price": 5000}],
            },
            format="json",
        )
        self.assertEqual(blocked.status_code, status.HTTP_403_FORBIDDEN)

        # Pre-license receipt creation at 0 balance MUST be ALLOWED
        pre_res = self.client.post(
            "/api/v1/receipts/",
            {
                "branch": self.branch.id,
                "salesperson": self.sp.id,
                "customer_name": "عميل ما قبل الترخيص",
                "total_amount": 3000,
                "down_payment": 500,
                "is_cash_sale": False,
                "installment_system": "5 شهور",
                "sale_month": 11,
                "sale_year": 2025,
                "products_text": "سخان قديم",
                "items": [],
                "installments": [
                    {"amount": 500, "payment_date": "2025-12-25"},
                    {"amount": 500, "payment_date": "2026-01-25"},
                    {"amount": 500, "payment_date": "2026-02-25"},
                    {"amount": 500, "payment_date": "2026-03-25"},
                    {"amount": 500, "payment_date": "2026-04-25"},
                ],
            },
            format="json",
        )
        self.assertEqual(pre_res.status_code, status.HTTP_201_CREATED)

        # Seed a confirmed production installment receipt & a deletable receipt to test exempt actions at 0 balance
        installment_rcpt = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.sp,
            receipt_number=101,
            customer_name="عميل قسط",
            total_amount=6000,
            down_payment=1000,
            is_cash_sale=False,
            sale_month=2,
            sale_year=2026,
        )
        SaleItem.objects.create(receipt=installment_rcpt, inventory_item=self.item, quantity=1, unit_price=6000)
        InstallmentPayment.objects.create(receipt=installment_rcpt, amount=500, payment_date=date(2026, 3, 25))

        temp_rcpt = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.sp,
            receipt_number=102,
            customer_name="عميل حذف",
            total_amount=1000,
            down_payment=1000,
            is_cash_sale=True,
            sale_month=2,
            sale_year=2026,
        )

        # 1. desktop_print NOT blocked at 0 balance
        with unittest.mock.patch("api.print_utils.pdfkit.from_string", return_value=True), \
             unittest.mock.patch("api.print_utils.get_wkhtmltopdf_config", return_value=None), \
             unittest.mock.patch("api.print_utils.os.startfile", create=True), \
             unittest.mock.patch("time.sleep"), \
             tempfile.TemporaryDirectory() as tmpdir, \
             unittest.mock.patch("api.print_utils.get_save_directory", return_value=tmpdir):
            dp_res = self.client.post(
                "/api/v1/receipts/desktop_print/",
                {"receipt_ids": [installment_rcpt.id], "action": "view"},
                format="json",
            )
            self.assertEqual(dp_res.status_code, status.HTTP_200_OK)

        # 2. bulk_delete NOT blocked at 0 balance
        del_res = self.client.post(
            "/api/v1/receipts/bulk_delete/", {"receipt_ids": [temp_rcpt.id]}, format="json"
        )
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)

        # 3. return_receipt NOT blocked at 0 balance
        ret_res = self.client.post(
            f"/api/v1/receipts/{installment_rcpt.id}/return_receipt/",
            {"return_month": 3, "return_year": 2026, "returned_items": [{"inventory_item_id": self.item.id, "quantity": 1, "unit_price": 6000}], "new_installment_system": "بدون أرباح", "new_installments": []},
            format="json",
        )
        self.assertEqual(ret_res.status_code, status.HTTP_200_OK)

    def test_expired_status_flag_and_null_expiry_bounds(self):
        ClientLicense.all_objects.all().delete()
        ClientLicense.objects.create(
            machine_id=self.mach_id,
            product_id=4,
            start_date=date(2025, 1, 1),
            expiry_date=date(2025, 12, 1),
            invoices_balance=500,
            is_active=True,
            license_code_hash="past_expired_hash",
        )
        st = self.client.get("/api/v1/license/status/").json()
        self.assertTrue(st["is_expired"])
        self.assertEqual(st["status"], "active")
        self.assertEqual(st["total_invoices_balance"], 0)

        # Lifetime production license (expiry_date=None) has non-crashing unbounded end date
        ClientLicense.all_objects.all().delete()
        ClientLicense.objects.create(
            machine_id=self.mach_id,
            product_id=7,
            start_date=date(2026, 1, 1),
            expiry_date=None,
            invoices_balance=5000,
            is_active=True,
            license_code_hash="lifetime_hash",
        )
        bounds_start, bounds_end, bounds_grace = get_subscription_date_bounds()
        self.assertEqual(bounds_start, date(2026, 1, 1))
        self.assertIsNone(bounds_end)
        self.assertIsNone(bounds_grace)


class AuthSecurityAndTokenRevocationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.mach_id = get_machine_id()
        self.admin_user, _ = User.objects.get_or_create(
            username="admin", defaults={"is_superuser": True, "is_staff": True}
        )
        self.admin_user.set_password("OldPass123!")
        self.admin_user.save()

        ClientLicense.all_objects.all().delete()
        ClientLicense.objects.create(
            machine_id=self.mach_id,
            product_id=4,
            start_date=date(2026, 1, 1),
            expiry_date=date(2028, 1, 1),
            invoices_balance=100,
            is_active=True,
            license_code_hash=generate_record_signature(date(2028, 1, 1), 100, self.mach_id, 4, True),
        )
        Branch.objects.create(name="فرع الأمان")

    def test_change_password_rejects_whitespace_rotates_token_and_allows_password_removal(self):
        old_token, _ = Token.objects.get_or_create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {old_token.key}")

        # 1. Whitespace-only non-empty password rejected with 400
        ws_res = self.client.post("/api/v1/auth/change-password/", {"new_password": "   "})
        self.assertEqual(ws_res.status_code, status.HTTP_400_BAD_REQUEST)

        # 1b. Wrong old_password rejected with 400
        bad_old = self.client.post(
            "/api/v1/auth/change-password/",
            {"old_password": "WrongOldPassword!", "new_password": "NewStrongPassword!9"},
        )
        self.assertEqual(bad_old.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. Valid new password revokes old token & returns rotated token
        ok_res = self.client.post(
            "/api/v1/auth/change-password/",
            {"old_password": "OldPass123!", "new_password": "NewStrongPassword!9"},
        )
        self.assertEqual(ok_res.status_code, status.HTTP_200_OK)
        new_token = ok_res.json().get("token")
        self.assertTrue(new_token)
        self.assertNotEqual(new_token, old_token.key)

        # Old token immediately returns 401
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {old_token.key}")
        self.assertEqual(self.client.get("/api/v1/branches/").status_code, status.HTTP_401_UNAUTHORIZED)

        # New token succeeds & has_password is True
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {new_token}")
        self.assertEqual(self.client.get("/api/v1/branches/").status_code, status.HTTP_200_OK)
        self.assertTrue(self.client.get("/api/v1/auth/has-password/").json()["has_password"])

        # 3. Password removal (empty string) sets has_password=False and rotates token again
        rem_res = self.client.post(
            "/api/v1/auth/change-password/",
            {"old_password": "NewStrongPassword!9", "new_password": ""},
        )
        self.assertEqual(rem_res.status_code, status.HTTP_200_OK)
        self.assertTrue(rem_res.json()["token"])
        self.assertNotEqual(rem_res.json()["token"], new_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {rem_res.json()['token']}")
        self.assertFalse(self.client.get("/api/v1/auth/has-password/").json()["has_password"])

    def test_recovery_code_revokes_existing_tokens_and_rejects_blank_password(self):
        active_tok, _ = Token.objects.get_or_create(user=self.admin_user)
        rec_code = mint_test_license_code(self.mach_id, product_id=16, year=2026, month=6)

        # Blank password rejected
        blank_res = self.client.post("/api/v1/auth/recover/", {"recovery_code": rec_code, "new_password": "   "})
        self.assertEqual(blank_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(UsedLicense.objects.exists())

        # Successful recovery deletes active token
        ok_res = self.client.post("/api/v1/auth/recover/", {"recovery_code": rec_code, "new_password": "Recovered!2026"})
        self.assertEqual(ok_res.status_code, status.HTTP_200_OK)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {active_tok.key}")
        self.assertEqual(self.client.get("/api/v1/branches/").status_code, status.HTTP_401_UNAUTHORIZED)


class BackupAndUpdaterHardeningTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.mach_id = get_machine_id()
        self.admin_user, _ = User.objects.get_or_create(
            username="admin", defaults={"is_superuser": True, "is_staff": True}
        )
        self.admin_user.set_password("SecretBackupPass!1")
        self.admin_user.save()

        ClientLicense.all_objects.all().delete()
        ClientLicense.objects.create(
            machine_id=self.mach_id,
            product_id=4,
            start_date=date(2026, 1, 1),
            expiry_date=date(2028, 1, 1),
            invoices_balance=100,
            is_active=True,
            license_code_hash="backup_auth_hash",
        )

    def test_backup_upload_and_apply_update_require_auth_when_activated_with_password(self):
        fake_db = SimpleUploadedFile("test.sqlite3", b"invalid", content_type="application/octet-stream")
        up_res = self.client.post("/api/v1/tools/backup/upload/", {"backup_file": fake_db})
        self.assertEqual(up_res.status_code, status.HTTP_401_UNAUTHORIZED)

        upd_res = self.client.post(
            "/api/v1/system/apply-update/",
            {"download_url": "https://github.com/venta-pos/releases/v1.0.1.exe", "sha256": "a" * 64, "version": "1.0.1"},
            format="json",
        )
        self.assertEqual(upd_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_backup_upload_corrupt_missing_tables_and_post_copy_rollback_and_download(self):
        self.client.force_authenticate(user=self.admin_user)
        with tempfile.TemporaryDirectory() as db_dir:
            live_db = Path(db_dir) / "db.sqlite3"
            _create_sqlite_db(live_db, REQUIRED_BACKUP_TABLES, seed_marker="ORIGINAL_LIVE")
            orig_bytes = live_db.read_bytes()

            with override_settings(
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": str(live_db)}}
            ):
                # 1. Valid backup download returns real SQLite binary stream
                dl_res = self.client.get("/api/v1/tools/backup/download/")
                self.assertEqual(dl_res.status_code, status.HTTP_200_OK)
                downloaded = b"".join(dl_res.streaming_content)
                dl_res.close()
                self.assertTrue(downloaded.startswith(b"SQLite format 3\x00"))

                # 2. Corrupt file -> 400 + zero leaked temp files
                before_temps = set(glob.glob(os.path.join(tempfile.gettempdir(), "ventapos_restore_*")))
                corrupt_file = SimpleUploadedFile("corrupt.sqlite3", b"NOT_A_SQLITE_FILE", content_type="application/octet-stream")
                c_res = self.client.post("/api/v1/tools/backup/upload/", {"backup_file": corrupt_file})
                self.assertEqual(c_res.status_code, status.HTTP_400_BAD_REQUEST)
                after_temps = set(glob.glob(os.path.join(tempfile.gettempdir(), "ventapos_restore_*")))
                self.assertEqual(before_temps, after_temps)
                self.assertEqual(live_db.read_bytes(), orig_bytes)

                # 3. Valid SQLite missing required VentaPOS tables -> 400
                partial_db = Path(db_dir) / "partial.sqlite3"
                _create_sqlite_db(partial_db, tables=("salesapp_branch",), seed_marker="PARTIAL")
                p_file = SimpleUploadedFile("partial.sqlite3", partial_db.read_bytes(), content_type="application/octet-stream")
                p_res = self.client.post("/api/v1/tools/backup/upload/", {"backup_file": p_file})
                self.assertEqual(p_res.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("جداول مفقودة", p_res.json()["error"])
                self.assertEqual(live_db.read_bytes(), orig_bytes)

                # 4. Simulate post-copy PRAGMA integrity_check failure -> restores pre_restore snapshot
                new_valid_db = Path(db_dir) / "new_valid.sqlite3"
                _create_sqlite_db(new_valid_db, REQUIRED_BACKUP_TABLES, seed_marker="NEW_DATA")
                real_connect = sqlite3.connect

                class _BadPostCopyConn:
                    def __init__(self, inner):
                        self._inner = inner

                    def execute(self, sql, *args, **kwargs):
                        return self._inner.execute(sql, *args, **kwargs)

                    def cursor(self):
                        return _BadPostCopyCursor(self._inner.cursor())

                    def close(self):
                        return self._inner.close()

                class _BadPostCopyCursor:
                    def __init__(self, inner):
                        self._inner = inner
                        self._bad = False

                    def execute(self, sql, *args, **kwargs):
                        self._bad = "PRAGMA INTEGRITY_CHECK" in sql.upper()
                        return self._inner.execute(sql, *args, **kwargs)

                    def fetchone(self):
                        if self._bad:
                            return ("database disk image is malformed",)
                        return self._inner.fetchone()

                    def __getattr__(self, name):
                        return getattr(self._inner, name)

                def _connect_spy(target, *args, **kwargs):
                    conn = real_connect(target, *args, **kwargs)
                    # Post-copy check opens db_path directly with timeout=30
                    if str(target) == str(live_db) and kwargs.get("timeout") == 30:
                        return _BadPostCopyConn(conn)
                    return conn

                rb_file = SimpleUploadedFile("rollback.sqlite3", new_valid_db.read_bytes(), content_type="application/octet-stream")
                with unittest.mock.patch("api.tools_views.sqlite3.connect", side_effect=_connect_spy), \
                     unittest.mock.patch("django.db.connections.close_all"):
                    rb_res = self.client.post("/api/v1/tools/backup/upload/", {"backup_file": rb_file})
                self.assertEqual(rb_res.status_code, status.HTTP_400_BAD_REQUEST, msg=rb_res.json())
                self.assertIn("تم التراجع تلقائياً", rb_res.json()["error"])

                # Verify live_db still contains ORIGINAL_LIVE after rollback!
                check_conn = real_connect(str(live_db))
                row = check_conn.execute("SELECT label FROM salesapp_companysetting LIMIT 1;").fetchone()
                check_conn.close()
                self.assertEqual(row[0], "ORIGINAL_LIVE")

    def test_launcher_check_pending_restore_rejects_corrupt_and_applies_valid_cleanly(self):
        import sys
        repo_root = str(Path(__file__).resolve().parents[3])
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        import launcher

        with tempfile.TemporaryDirectory() as db_dir:
            live_db = Path(db_dir) / "db.sqlite3"
            _create_sqlite_db(live_db, REQUIRED_BACKUP_TABLES, seed_marker="BEFORE_LAUNCHER")
            pending_file = Path(db_dir) / "restore_pending.bin"
            wal_file = Path(str(live_db) + "-wal")
            shm_file = Path(str(live_db) + "-shm")
            wal_file.write_bytes(b"stale-wal")
            shm_file.write_bytes(b"stale-shm")

            with override_settings(
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": str(live_db)}}
            ):
                # 1. Corrupt restore_pending.bin -> unlinked without harming live_db
                pending_file.write_bytes(b"corrupted_binary_junk")
                launcher.check_pending_restore()
                self.assertFalse(pending_file.exists())
                self.assertTrue(wal_file.exists())
                c1 = sqlite3.connect(str(live_db))
                self.assertEqual(c1.execute("SELECT label FROM salesapp_companysetting;").fetchone()[0], "BEFORE_LAUNCHER")
                c1.close()

                # 2. Valid restore_pending.bin -> backs up old DB, swaps DB, deletes wal/shm & pending file
                new_db = Path(db_dir) / "valid_pending.sqlite3"
                _create_sqlite_db(new_db, REQUIRED_BACKUP_TABLES, seed_marker="AFTER_LAUNCHER")
                pending_file.write_bytes(new_db.read_bytes())

                launcher.check_pending_restore()
                self.assertFalse(pending_file.exists())
                self.assertFalse(wal_file.exists())
                self.assertFalse(shm_file.exists())
                backups = list((Path(db_dir) / "backups").glob("pre_pending_restore_*.sqlite3"))
                self.assertEqual(len(backups), 1)
                c2 = sqlite3.connect(str(live_db))
                self.assertEqual(c2.execute("SELECT label FROM salesapp_companysetting;").fetchone()[0], "AFTER_LAUNCHER")
                c2.close()

    def test_system_apply_update_rejects_version_traversal_and_untrusted_url(self):
        self.client.force_authenticate(user=self.admin_user)

        for bad_ver in ("../evil", "1.0/../../bad", "1.0\\..\\bad"):
            res = self.client.post(
                "/api/v1/system/apply-update/",
                {
                    "download_url": "https://github.com/venta-pos/releases/v1.0.2.exe",
                    "sha256": "a" * 64,
                    "version": bad_ver,
                },
                format="json",
            )
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(res.json()["error"], "invalid_version")

        bad_url_res = self.client.post(
            "/api/v1/system/apply-update/",
            {"download_url": "https://evil.example.com/payload.exe", "sha256": "a" * 64, "version": "1.0.2"},
            format="json",
        )
        self.assertEqual(bad_url_res.status_code, status.HTTP_400_BAD_REQUEST)


class PrintEngineHardeningTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.mach_id = get_machine_id()
        self.admin_user, _ = User.objects.get_or_create(
            username="admin", defaults={"is_superuser": True, "is_staff": True}
        )
        self.client.force_authenticate(user=self.admin_user)
        ClientLicense.all_objects.all().delete()
        ClientLicense.objects.create(
            machine_id=self.mach_id,
            product_id=4,
            start_date=date(2026, 1, 1),
            expiry_date=date(2028, 1, 1),
            invoices_balance=500,
            is_active=True,
            license_code_hash=generate_record_signature(date(2028, 1, 1), 500, self.mach_id, 4, True),
        )
        CompanySetting.objects.update_or_create(
            id=1,
            defaults={
                "name": "معرض الأمل",
                "phone1": "٠١٠٠١١١٢٢٢٣",
                "phone2": "٠١٢٢٣٣٣٤٤٤٥",
            },
        )
        self.branch = Branch.objects.create(name="فرع الطباعة")
        self.sp = Salesperson.objects.create(branch=self.branch, name="مندوب الطباعة")
        self.supplier = Supplier.objects.create(branch=self.branch, name="مورد أجهزة")
        self.item = InventoryItem.objects.create(
            branch=self.branch, name="شاشة 50 بوصة", initial_purchase_price=9000, initial_quantity=10
        )

    def test_to_arabic_numerals_decimals_and_formatting(self):
        self.assertEqual(to_arabic_numerals("1250.00"), "١٢٥٠")
        self.assertEqual(to_arabic_numerals("1,250.00"), "١,٢٥٠")
        self.assertEqual(to_arabic_numerals(1250.6), "١٢٥١")
        self.assertEqual(to_arabic_numerals("2026/02"), "٢٠٢٦/٠٢")
        self.assertEqual(ed2ad("قسط 1 من 6 - 500.00 ج.م"), "قسط ١ من ٦ - ٥٠٠ ج.م")

    def test_receipt_purchase_and_report_desktop_print_hardening(self):
        receipt = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.sp,
            receipt_number=55,
            customer_name="كريم عادل",
            area="الدقي",
            total_amount=5000,
            down_payment=1000,
            is_cash_sale=False,
            installment_system="8 شهور",
            sale_month=2,
            sale_year=2026,
            products_text="شاشة 50 بوصة",
        )
        SaleItem.objects.create(receipt=receipt, inventory_item=self.item, quantity=1, unit_price=5000)
        # Intentionally insert payments out of chronological order
        InstallmentPayment.objects.create(receipt=receipt, amount=2000, payment_date=date(2026, 4, 25))
        InstallmentPayment.objects.create(receipt=receipt, amount=2000, payment_date=date(2026, 3, 25))

        pur_inv = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=77,
            invoice_type="PURCHASE",
            invoice_month=2,
            invoice_year=2026,
        )
        PurchaseInvoiceItem.objects.create(invoice=pur_inv, inventory_item=self.item, quantity=2, purchase_price=9000)

        captured_html = []
        captured_paths = []

        def _fake_from_string(html_str, full_path, configuration=None, options=None):
            captured_html.append(html_str)
            captured_paths.append(full_path)
            return True

        with tempfile.TemporaryDirectory() as tmpdir, \
             unittest.mock.patch("api.print_utils.pdfkit.from_string", side_effect=_fake_from_string), \
             unittest.mock.patch("api.print_utils.get_wkhtmltopdf_config", return_value=None), \
             unittest.mock.patch("api.print_utils.os.startfile", create=True), \
             unittest.mock.patch("time.sleep"), \
             unittest.mock.patch("api.print_utils.get_save_directory", return_value=tmpdir):

            # 1. Receipt schedule print twice -> unique UUID filenames, accounting date, preserved Arabic phones, chronological sort
            res1 = self.client.post(
                "/api/v1/receipts/desktop_print/",
                {"receipt_ids": [receipt.id], "action": "view"},
                format="json",
            )
            res2 = self.client.post(
                "/api/v1/receipts/desktop_print/",
                {"receipt_ids": [receipt.id], "action": "view"},
                format="json",
            )
            self.assertEqual(res1.status_code, status.HTTP_200_OK)
            self.assertEqual(res2.status_code, status.HTTP_200_OK)
            self.assertNotEqual(captured_paths[0], captured_paths[1])
            self.assertRegex(os.path.basename(captured_paths[0]), r"_[0-9a-f]{6}\.pdf$")

            # CompanySetting phone1/phone2 preserved cleanly on model & rendered in PDF
            cs = CompanySetting.objects.first()
            self.assertEqual(cs.phone1, "٠١٠٠١١١٢٢٢٣")
            self.assertEqual(cs.phone2, "٠١٢٢٣٣٣٤٤٤٥")
            self.assertIn("٢٠٢٦/٠٢", captured_html[0])
            # Chronological installment sorting: 2026/03/25 appears before 2026/04/25
            idx_mar = captured_html[0].find("٢٠٢٦/٠٣/٢٥")
            idx_apr = captured_html[0].find("٢٠٢٦/٠٤/٢٥")
            self.assertGreater(idx_mar, -1)
            self.assertGreater(idx_apr, idx_mar)

            # 2. Purchase desktop print uses accounting invoice_year/invoice_month
            p_res = self.client.post(
                "/api/v1/purchase-invoices/desktop_print/",
                {"invoice_ids": [pur_inv.id], "action": "view"},
                format="json",
            )
            self.assertEqual(p_res.status_code, status.HTTP_200_OK)
            self.assertIn("٢٠٢٦/٠٢", captured_html[-1])

            # 3. ReportDesktopPrintView auto-fetches areas & purchases with empty rows/kpis/columns
            rep_areas = self.client.post(
                "/api/v1/reports/desktop_print/",
                {
                    "report_type": "areas",
                    "branch_id": self.branch.id,
                    "year": 2026,
                    "month": 2,
                    "action": "view",
                },
                format="json",
            )
            self.assertEqual(rep_areas.status_code, status.HTTP_200_OK)
            self.assertIn("الدقي", captured_html[-1])
            self.assertIn("المنطقة", captured_html[-1])

            rep_purch = self.client.post(
                "/api/v1/reports/desktop_print/",
                {
                    "report_type": "purchases",
                    "branch_id": self.branch.id,
                    "year": 2026,
                    "month": 2,
                    "action": "view",
                },
                format="json",
            )
            self.assertEqual(rep_purch.status_code, status.HTTP_200_OK)
            self.assertIn("شاشة ٥٠ بوصة", captured_html[-1])
            self.assertIn("مورد أجهزة", captured_html[-1])

    def test_collections_single_month_installment_slip_printing_by_ids_and_month_year(self):
        receipt = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.sp,
            receipt_number=88,
            customer_name="طارق محمود",
            area="مدينة نصر",
            total_amount=6000,
            down_payment=0,
            is_cash_sale=False,
            installment_system="6 شهور",
            sale_month=12,
            sale_year=2025,
            products_text="ثلاجة عرض",
        )
        SaleItem.objects.create(receipt=receipt, inventory_item=self.item, quantity=1, unit_price=6000)
        inst_list = []
        for m in range(1, 7):
            inst_list.append(
                InstallmentPayment.objects.create(
                    receipt=receipt,
                    amount=1000,
                    payment_date=date(2026, m, 25),
                )
            )

        captured_html = []

        def _capture_pdf(html_str, full_path, configuration=None, options=None):
            captured_html.append(html_str)
            return True

        with tempfile.TemporaryDirectory() as tmpdir, \
             unittest.mock.patch("api.print_utils.pdfkit.from_string", side_effect=_capture_pdf), \
             unittest.mock.patch("api.print_utils.get_wkhtmltopdf_config", return_value=None), \
             unittest.mock.patch("api.print_utils.os.startfile", create=True), \
             unittest.mock.patch("time.sleep"), \
             unittest.mock.patch("api.print_utils.get_save_directory", return_value=tmpdir):

            # 1. Print single installment slip by installment_ids ONLY (receipt_ids derived automatically)
            inst_3 = inst_list[2]  # Month 3 (installment 3 of 6), remaining should be 6000 - 3000 = 3000 (٣٠٠٠)
            res_single = self.client.post(
                "/api/v1/receipts/desktop_print/",
                {"installment_ids": [inst_3.id], "action": "view"},
                format="json",
            )
            self.assertEqual(res_single.status_code, status.HTTP_200_OK)
            html_single = captured_html[-1]
            self.assertEqual(html_single.count('<div class="evl">'), 1)
            self.assertIn("٢٠٢٦/٠٣/٢٥", html_single)
            self.assertNotIn("٢٠٢٦/٠١/٢٥", html_single)
            self.assertNotIn("٢٠٢٦/٠٢/٢٥", html_single)
            self.assertIn(">٣<", html_single)
            self.assertIn(">٦<", html_single)
            self.assertIn(">٣٠٠٠<", html_single)

            # 2. Print single installment slip by receipt_ids + month/year (Month 6 -> installment 6 of 6 -> خالص)
            res_month = self.client.post(
                "/api/v1/receipts/desktop_print/",
                {"receipt_ids": [receipt.id], "month": 6, "year": 2026, "action": "view"},
                format="json",
            )
            self.assertEqual(res_month.status_code, status.HTTP_200_OK)
            html_month = captured_html[-1]
            self.assertEqual(html_month.count('<div class="evl">'), 1)
            self.assertIn("٢٠٢٦/٠٦/٢٥", html_month)
            self.assertNotIn("٢٠٢٦/٠٥/٢٥", html_month)
            self.assertIn("خالص", html_month)

            # 3. Full schedule print when neither installment_ids nor month/year is passed
            res_all = self.client.post(
                "/api/v1/receipts/desktop_print/",
                {"receipt_ids": [receipt.id], "action": "view"},
                format="json",
            )
            self.assertEqual(res_all.status_code, status.HTTP_200_OK)
            html_all = captured_html[-1]
            self.assertEqual(html_all.count('<div class="evl">'), 6)

    def test_printers_utf8_arabic_names_msft_status_8_and_win32_printer_offline_and_default(self):
        import json as _json
        mock_payload = [
            {
                "Name": "طابعة المكتب HP LaserJet",
                "PrinterStatus": 8,  # MSFT_Printer 8 = Offline
                "WorkOffline": False,
                "IsDefault": False,
            },
            {
                "Name": "طابعة كاشير رئيسية",
                "PrinterStatus": 3,  # Win32_Printer 3 = Idle, but WorkOffline=True
                "WorkOffline": True,
                "Default": True,
            },
            {
                "Name": "EPSON USB Disconnected",
                "CimPrinterStatus": 3,
                "ExtendedPrinterStatus": 7,  # Win32_Printer ExtendedPrinterStatus 7 = Offline
                "PrinterStatus": 0,
                "WorkOffline": False,
                "IsDefault": False,
            },
            {
                "Name": "Canon Ready Printer",
                "CimPrinterStatus": 3,
                "ExtendedPrinterStatus": 2,
                "PrinterState": 0,
                "PrinterStatus": 0,
                "WorkOffline": False,
                "IsDefault": False,
            },
        ]
        mock_proc = unittest.mock.MagicMock()
        mock_proc.stdout = _json.dumps(mock_payload, ensure_ascii=False)

        with unittest.mock.patch("subprocess.run", return_value=mock_proc) as spy_run:
            res = self.client.get("/api/v1/receipts/printers/")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            _, run_kwargs = spy_run.call_args
            self.assertEqual(run_kwargs.get("encoding"), "utf-8")
            self.assertEqual(run_kwargs.get("timeout"), 10)

            printers = res.json()["printers"]
            self.assertEqual(len(printers), 4)
            self.assertEqual(printers[0], {"name": "طابعة المكتب HP LaserJet", "status": "offline", "is_default": False})
            self.assertEqual(printers[1], {"name": "طابعة كاشير رئيسية", "status": "offline", "is_default": True})
            self.assertEqual(printers[2], {"name": "EPSON USB Disconnected", "status": "offline", "is_default": False})
            self.assertEqual(printers[3], {"name": "Canon Ready Printer", "status": "ready", "is_default": False})

    def test_init_demo_db_creates_short_realistic_company_setting(self):
        from django.core.management import call_command
        from dateutil.relativedelta import relativedelta as real_relativedelta

        ClientLicense.all_objects.all().delete()
        with unittest.mock.patch(
            "api.management.commands.init_demo_db.relativedelta",
            side_effect=lambda *args, **kwargs: (
                real_relativedelta(months=-1) if kwargs.get("months") == 25 else real_relativedelta(*args, **kwargs)
            ),
        ):
            call_command("init_demo_db")

        cs = CompanySetting.objects.first()
        self.assertIsNotNone(cs)
        self.assertEqual(cs.name, "شركة النور للتجارة")
        self.assertEqual(cs.description, "مفروشات - أدوات منزلية - أجهزة كهربائية")
        self.assertEqual(cs.footer_text, "رجاء الاحتفاظ بهذا الإيصال")
        self.assertEqual(cs.phone1, "01012345678")
        self.assertEqual(cs.phone2, "01112345678")

    def test_init_demo_db_clamps_start_date_to_2025(self):
        from django.core.management import call_command
        from api.models import InventoryItem, CommissionHistory

        ClientLicense.all_objects.all().delete()

        class Early2025Date(date):
            @classmethod
            def today(cls):
                return date(2025, 1, 20)

        with unittest.mock.patch("api.management.commands.init_demo_db.date", Early2025Date):
            call_command("init_demo_db")

        items = InventoryItem.objects.all()
        self.assertGreater(items.count(), 0)
        self.assertTrue(all(it.initial_year >= 2025 for it in items))
        self.assertTrue(all(ch.activation_year >= 2025 for ch in CommissionHistory.objects.all()))

        first_item = items.first()
        res_patch = self.client.patch(
            f"/api/v1/inventory-items/{first_item.id}/",
            {"initial_quantity": first_item.initial_quantity + 1},
            format="json",
        )
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)

    def test_generate_and_open_pdf_prunes_old_pdfs_to_50(self):
        import os
        import tempfile
        from pathlib import Path
        from api.print_utils import generate_and_open_pdf, MAX_STORED_PDFS

        self.assertEqual(MAX_STORED_PDFS, 50)
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_ts = 1700000000
            for idx in range(55):
                p = Path(tmp_dir) / f"old_{idx:03d}.pdf"
                p.write_bytes(b"%PDF-1.4\n")
                os.utime(p, (base_ts + idx * 10, base_ts + idx * 10))

            def fake_from_string(html, output_path, configuration=None, options=None):
                Path(output_path).write_bytes(b"%PDF-1.4\nnew")

            with unittest.mock.patch("api.print_utils.get_save_directory", return_value=tmp_dir), \
                 unittest.mock.patch("api.print_utils.get_wkhtmltopdf_config", return_value=None), \
                 unittest.mock.patch("api.print_utils.pdfkit.from_string", side_effect=fake_from_string), \
                 unittest.mock.patch("time.sleep"), \
                 unittest.mock.patch("platform.system", return_value="Windows"), \
                 unittest.mock.patch("os.startfile", create=True):
                ok, msg = generate_and_open_pdf("<html></html>", filename_prefix="RetentionTest", action="view")

            self.assertTrue(ok, msg)
            remaining = sorted(p.name for p in Path(tmp_dir).glob("*.pdf"))
            self.assertEqual(len(remaining), 50)
            for deleted_idx in range(6):
                self.assertNotIn(f"old_{deleted_idx:03d}.pdf", remaining)
            self.assertIn("old_006.pdf", remaining)
            self.assertTrue(any(name.startswith("RetentionTest_") for name in remaining))

