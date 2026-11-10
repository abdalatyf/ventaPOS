"""
Cross-App End-to-End Tests between LicenseManager and VentaPOS NextGen.
Tests key generation for standard and print-only plans, emergency recovery,
and activation in VentaPOS NextGen.
"""
import sys
from pathlib import Path
from datetime import date
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from api.models import ClientLicense, Branch, Receipt, Salesperson
from api.utils.license_validator import LicenseValidator
from api.utils.security_utils import get_machine_id

# Import LicenseGenerator directly if available or use exact algorithm
class CrossAppLicenseE2ETests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.machine_id = get_machine_id()

    def _generate_license_code(self, product_id, start_date=None):
        """Generates a valid license code using the confirmed 80-bit crypto algorithm."""
        if start_date is None:
            start_date = date(2026, 1, 1)

        import hashlib
        import hmac
        import struct

        raw_hash = hashlib.sha256(self.machine_id.encode()).digest()
        extracted_machine_hash = struct.unpack(">I", raw_hash[:4])[0]

        year_diff = max(0, start_date.year - 2025)
        date_code = min((year_diff * 12) + (start_date.month - 1), 255)

        # product_id mapping: extracted_prod = (product_id - 1) & 0xF
        extracted_prod = (product_id - 1) & 0xF

        payload_bytes = struct.pack(">IBB", extracted_machine_hash, extracted_prod, date_code)
        secret = LicenseValidator._get_key()
        sig_bytes = hmac.new(secret, payload_bytes, hashlib.sha256).digest()
        recalc_sig_int = struct.unpack(">Q", sig_bytes[:8])[0]
        final_sig = recalc_sig_int & ((1 << 36) - 1)

        mask = (final_sig << 8) | (final_sig >> 28)
        data_block = (extracted_machine_hash << 12) | (date_code << 4) | extracted_prod
        masked_data = data_block ^ mask

        full_code_int = (final_sig << 44) | masked_data

        charset = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        res = []
        num = full_code_int
        while num > 0:
            num, rem = divmod(num, 32)
            res.append(charset[rem])
        while len(res) < 16:
            res.append(charset[0])
        raw_code = "".join(reversed(res))
        return f"{raw_code[:4]}-{raw_code[4:8]}-{raw_code[8:12]}-{raw_code[12:]}"

    def test_standard_plan_activation_flow(self):
        """
        Verify minting a Standard 1-Year license (product_id=1) and activating it.
        """
        code = self._generate_license_code(product_id=1, start_date=date(2026, 1, 1))
        res = self.client.post("/api/v1/license/activate/", {"license_code": code})
        self.assertEqual(res.status_code, 201, res.data if hasattr(res, 'data') else res.content)
        self.assertEqual(res.data.get("status"), "success")

        # Verify active license in DB
        lic = ClientLicense.objects.filter(is_active=True).first()
        self.assertIsNotNone(lic)
        self.assertEqual(lic.product_id, 1)
        self.assertNotIn(lic.product_id, (2, 3))
        self.assertEqual(lic.invoices_balance, 800)

        # Check /api/v1/license/status/
        res_status = self.client.get("/api/v1/license/status/")
        self.assertEqual(res_status.status_code, 200)
        self.assertFalse(res_status.data.get("is_print_only"))

    def test_print_only_plan_activation_flow(self):
        """
        Verify minting a Print-Only license (product_id=2 or 3) and activating it sets is_print_only=True.
        """
        code = self._generate_license_code(product_id=2, start_date=date(2026, 2, 1))
        res = self.client.post("/api/v1/license/activate/", {"license_code": code})
        self.assertEqual(res.status_code, 201, res.data if hasattr(res, 'data') else res.content)
        self.assertEqual(res.data.get("status"), "success")

        lic = ClientLicense.objects.filter(is_active=True).first()
        self.assertIsNotNone(lic)
        self.assertEqual(lic.product_id, 2)
        self.assertIn(lic.product_id, (2, 3))

        # Check /api/v1/license/status/
        res_status = self.client.get("/api/v1/license/status/")
        self.assertEqual(res_status.status_code, 200)
        self.assertTrue(res_status.data.get("is_print_only"))

    def test_emergency_recovery_code_activation(self):
        """
        Verify product_id=16 acts as an emergency password recovery code.
        """
        code = self._generate_license_code(product_id=16, start_date=date(2026, 1, 1))
        # Validate through LicenseValidator
        validation = LicenseValidator.validate(code, self.machine_id)
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["product_id"], 16)
        self.assertTrue(validation["is_recovery"])
