import hashlib
import hmac
import struct
import unittest
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from api.models import (
    Branch,
    Salesperson,
    InventoryItem,
    Receipt,
    SaleItem,
    ClientLicense,
    UsedLicense,
    LicenseHistory,
    CompanySetting,
)
from api.utils.license_validator import LicenseValidator
from api.utils.security_utils import (
    get_machine_id,
    generate_record_signature,
)


def mint_test_license_code(machine_id: str, product_id: int, year: int = 2026, month: int = 1) -> str:
    """
    Synthesizes a valid 80-bit Base32 license code matching LicenseValidator.validate.
    product_id: 1 for standard subscription, 15 for emergency admin password recovery.
    """
    extracted_prod = (product_id - 1) & 0xF
    extracted_date_code = ((year - LicenseValidator.BASE_YEAR) * 12 + (month - 1)) & 0xFF
    raw_hash = hashlib.sha256(machine_id.encode()).digest()
    extracted_machine_hash = struct.unpack(">I", raw_hash[:4])[0]

    payload_bytes = struct.pack(">IBB", extracted_machine_hash, extracted_prod, extracted_date_code)
    secret = LicenseValidator._get_key()
    recalculated_sig_bytes = hmac.new(secret, payload_bytes, hashlib.sha256).digest()
    recalc_sig_int = struct.unpack(">Q", recalculated_sig_bytes[:8])[0]
    final_sig = recalc_sig_int & ((1 << 36) - 1)

    mask = (final_sig << 8) | (final_sig >> 28)
    data_block = (extracted_machine_hash << 12) | (extracted_date_code << 4) | extracted_prod
    masked_data = data_block ^ mask

    full_int = (final_sig << 44) | masked_data

    chars = []
    num = full_int
    for _ in range(16):
        chars.append(LicenseValidator.CHARSET[num % 32])
        num //= 32
    clean_code = "".join(reversed(chars))
    return f"{clean_code[0:4]}-{clean_code[4:8]}-{clean_code[8:12]}-{clean_code[12:16]}"


class LicensingAndSecurityTests(TestCase):
    """
    Automated test suite for Licensing, Password Recovery, and Security Integrity:
    1. Validator roundtrip of minted 80-bit license codes.
    2. First activation wipes Demo data; subsequent Production renewals preserve data without wiping.
    3. LicenseEnforcementMiddleware enforces read-only lock (403 on writes, 200 on GET and backup download).
    4. Monotonic clock-rollback detection blocks operations if future records exist.
    5. Valid product_id=15 password recovery code resets admin credentials, records UsedLicense,
       and rejects replay attacks or misuse as an activation code.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin_user, _ = User.objects.get_or_create(
            username="admin", defaults={"is_superuser": True}
        )
        self.client.force_authenticate(user=self.admin_user)

        self.branch = Branch.objects.create(name="الفرع الرئيسي للأمان")
        self.salesperson = Salesperson.objects.create(
            branch=self.branch, name="مندوب معتمد"
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
            license_code_hash=sig,
        )
        self.client.credentials(HTTP_X_COMPANY_CODE="TESTSEC")

    def test_license_minting_and_validator_roundtrip(self):
        """Verify that the test minting helper produces 100% valid codes for LicenseValidator."""
        # Standard subscription code (product_id=1)
        sub_code = mint_test_license_code(self.mach_id, product_id=1, year=2026, month=5)
        res_sub = LicenseValidator.validate(sub_code, self.mach_id)
        self.assertTrue(res_sub["valid"])
        self.assertEqual(res_sub["product_id"], 1)
        self.assertEqual(res_sub["year"], 2026)
        self.assertEqual(res_sub["month"], 5)
        self.assertFalse(res_sub["is_recovery"])

        # Recovery code (product_id=15)
        rec_code = mint_test_license_code(self.mach_id, product_id=15, year=2026, month=8)
        res_rec = LicenseValidator.validate(rec_code, self.mach_id)
        self.assertTrue(res_rec["valid"])
        self.assertEqual(res_rec["product_id"], 15)
        self.assertTrue(res_rec["is_recovery"])

        # Machine ID mismatch rejection
        res_mismatch = LicenseValidator.validate(sub_code, "OTHERMAC")
        self.assertFalse(res_mismatch["valid"])
        self.assertIn("غير مخصص لهذا الجهاز", res_mismatch["error"])

    def test_demo_mode_to_first_activation_wipe(self):
        """
        Verify that first license activation from Demo Mode completely wipes
        all demo branches, salespersons, and receipts before initializing production.
        """
        # Configure Demo Mode state
        ClientLicense.all_objects.all().delete()
        ClientLicense.objects.create(
            company_code=1001,
            product_id=1,
            start_date=date(2026, 1, 1),
            expiry_date=date(2027, 1, 1),
            invoices_balance=1000,
            is_active=True,
            machine_id="DEMO_MACHINE",
            license_code_hash="demo_hash",
        )

        demo_branch = Branch.objects.create(name="فرع تجريبي للعرض")
        demo_sp = Salesperson.objects.create(branch=demo_branch, name="مندوب تجريبي")
        Receipt.objects.create(
            branch=demo_branch,
            salesperson=demo_sp,
            receipt_number=999,
            customer_name="عميل ديمو",
            total_amount=5000,
            down_payment=5000,
            is_cash_sale=True,
            sale_month=1,
            sale_year=2026,
        )

        self.assertGreater(Branch.objects.count(), 0)
        self.assertGreater(Receipt.objects.count(), 0)

        # Mint valid code for the real hardware machine ID
        code = mint_test_license_code(self.mach_id, product_id=1, year=2026, month=1)
        res = self.client.post("/api/v1/license/activate/", {"license_code": code})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Verify demo data was completely wiped
        self.assertEqual(Branch.objects.count(), 0)
        self.assertEqual(Receipt.objects.count(), 0)
        self.assertEqual(Salesperson.objects.count(), 0)

        # Verify newly active production license
        new_lic = ClientLicense.objects.filter(is_active=True).first()
        self.assertIsNotNone(new_lic)
        self.assertEqual(new_lic.machine_id, self.mach_id)

    def test_production_renewal_preserves_existing_data(self):
        """
        Verify that renewing an existing production license preserves all branches,
        items, and receipts without wiping the database.
        """
        prod_branch = Branch.objects.create(name="فرع روكسي الدائم")
        prod_sp = Salesperson.objects.create(branch=prod_branch, name="مندوب روكسي")
        prod_item = InventoryItem.objects.create(
            branch=prod_branch,
            name="شاشة 65 بوصة",
            initial_quantity=5,
            initial_purchase_price=8000,
            initial_commission_amount=250,
            initial_month=1,
            initial_year=2026,
        )
        prod_receipt = Receipt.objects.create(
            branch=prod_branch,
            salesperson=prod_sp,
            receipt_number=101,
            customer_name="عميل حقيقي",
            total_amount=10000,
            down_payment=10000,
            is_cash_sale=True,
            sale_month=1,
            sale_year=2026,
        )

        # Renew with next year's license code
        renewal_code = mint_test_license_code(self.mach_id, product_id=1, year=2027, month=1)
        res = self.client.post("/api/v1/license/activate/", {"license_code": renewal_code})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # CRITICAL ASSERTION: Production data MUST NOT be wiped on renewal!
        self.assertTrue(Branch.objects.filter(id=prod_branch.id).exists())
        self.assertTrue(Salesperson.objects.filter(id=prod_sp.id).exists())
        self.assertTrue(InventoryItem.objects.filter(id=prod_item.id).exists())
        self.assertTrue(Receipt.objects.filter(id=prod_receipt.id).exists())

    def test_license_enforcement_middleware_read_only_mode(self):
        """
        Verify that an expired production license locks write requests with 403 Forbidden,
        while permitting GET queries and the backup download endpoint.
        """
        # Expire license
        self.license.expiry_date = timezone.localdate() - timezone.timedelta(days=40)
        self.license.license_code_hash = generate_record_signature(
            str(self.license.expiry_date), 1000, self.mach_id, 1, True
        )
        self.license.save()

        # 1. Write request to create branch -> Blocked with 403
        write_res = self.client.post("/api/v1/branches/", {"name": "فرع جديد ممنوع"})
        self.assertEqual(write_res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(write_res.json()["error"], "license_expired")

        # 2. Read-only request -> Permitted
        read_res = self.client.get("/api/v1/branches/")
        self.assertEqual(read_res.status_code, status.HTTP_200_OK)

        # 3. Whitelisted backup download -> Permitted
        with unittest.mock.patch("api.tools_views.BackupDownloadView.get") as mock_backup_get:
            from django.http import HttpResponse
            mock_backup_get.return_value = HttpResponse(b"dummy backup stream", content_type="application/x-sqlite3")
            backup_res = self.client.get("/api/v1/tools/backup/download/")
            self.assertEqual(backup_res.status_code, status.HTTP_200_OK)

    def test_monotonic_clock_rollback_detection(self):
        """
        Verify that future-dated records trigger 403 clock rollback lock.
        """
        future_receipt = Receipt.objects.create(
            branch=self.branch,
            receipt_number=888,
            customer_name="عميل زمني",
            total_amount=500,
            sale_month=1,
            sale_year=2026,
        )
        Receipt.all_objects.filter(id=future_receipt.id).update(
            created_at=timezone.now() + timezone.timedelta(days=10)
        )

        res = self.client.get(f"/api/v1/receipts-next-number/?branch_id={self.branch.id}")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res.json()["error"], "clock_rollback")

    def test_password_recovery_full_flow(self):
        """
        Verify emergency password recovery using product_id=15 code:
        - Changes admin password.
        - Records UsedLicense entry to prevent replay attacks.
        - Replay attempt returns 400 Bad Request.
        - Attempting to use recovery code as an activation code returns 400 Bad Request.
        """
        rec_code = mint_test_license_code(self.mach_id, product_id=15, year=2026, month=3)

        # 1. Recover password
        rec_res = self.client.post("/api/v1/auth/recover/", {
            "recovery_code": rec_code,
            "new_password": "NewSecurePassword2026!",
        })
        self.assertEqual(rec_res.status_code, status.HTTP_200_OK)
        self.assertIn("تم تغيير كلمة المرور بنجاح", rec_res.json()["message"])

        # Verify password changed
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.check_password("NewSecurePassword2026!"))

        # 2. Replay rejection
        replay_res = self.client.post("/api/v1/auth/recover/", {
            "recovery_code": rec_code,
            "new_password": "AnotherPassword!",
        })
        self.assertEqual(replay_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("تم استخدام كود الاسترداد", replay_res.json()["error"])

        # 3. Misuse recovery code on activation endpoint
        rec_code_2 = mint_test_license_code(self.mach_id, product_id=15, year=2026, month=4)
        act_res = self.client.post("/api/v1/license/activate/", {
            "license_code": rec_code_2,
        })
        self.assertEqual(act_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("هذا كود استرداد وليس كود تفعيل", act_res.json()["error"])

    def test_license_status_is_last_month_detection(self):
        """
        Verify LicenseStatusView accurately flags is_last_month:
        - License from 2026-01-01 to 2027-01-01.
        - Month 1-11 (e.g. 2026-06-15) -> is_last_month is False.
        - Month 12 (last allowed business month, 2026-12-10) -> is_last_month is True.
        - Grace window (2027-01-15) -> is_last_month is True.
        - Post-grace (2027-02-01) -> is_last_month is False.
        """
        import unittest.mock
        ClientLicense.objects.all().delete()
        ClientLicense.objects.create(
            machine_id=self.mach_id,
            product_id=1,
            start_date=date(2026, 1, 1),
            expiry_date=date(2027, 1, 1),
            invoices_balance=1000,
            is_active=True,
            license_code_hash="valid_hash",
        )

        # 1. Normal month (June 2026) -> False
        with unittest.mock.patch("django.utils.timezone.localdate", return_value=date(2026, 6, 15)):
            res = self.client.get("/api/v1/license/status/")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertFalse(res.json()["is_last_month"])

        # 2. 12th business month (December 2026) -> True
        with unittest.mock.patch("django.utils.timezone.localdate", return_value=date(2026, 12, 10)):
            res = self.client.get("/api/v1/license/status/")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertTrue(res.json()["is_last_month"])

        # 3. Grace window (January 2027 before 25th) -> True
        with unittest.mock.patch("django.utils.timezone.localdate", return_value=date(2027, 1, 15)):
            res = self.client.get("/api/v1/license/status/")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertTrue(res.json()["is_last_month"])

        # 4. Post-grace window (February 2027) -> False
        with unittest.mock.patch("django.utils.timezone.localdate", return_value=date(2027, 2, 1)):
            res = self.client.get("/api/v1/license/status/")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertFalse(res.json()["is_last_month"])

