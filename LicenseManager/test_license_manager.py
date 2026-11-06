"""
Automated Test Suite for VentaPOS License Manager & NextGen Cryptographic Compatibility.
Tests key generation, bi-directional verification, machine binding, date bounds, tamper rejection,
and password recovery identification.
"""
import sys
import unittest
from datetime import date
from pathlib import Path

# Setup paths to import both LicenseManager and VentaPOS_NextGen
LICENSE_MGR_DIR = Path(__file__).resolve().parent
NEXTGEN_DIR = LICENSE_MGR_DIR.parent / "VentaPOS_NextGen" / "backend"

sys.path.insert(0, str(LICENSE_MGR_DIR))
sys.path.insert(0, str(NEXTGEN_DIR))

from licenses.utils.crypto import LicenseGenerator
from VALIDATOR import LicenseValidator as LocalValidator
from api.utils.license_validator import LicenseValidator as NextGenValidator


class LicenseManagerCompatibilityTests(unittest.TestCase):
    """
    Verifies 100% cryptographic parity and business logic binding between
    LicenseManager and VentaPOS NextGen.
    """

    def setUp(self):
        self.sample_machine_id = "5410972688ec8bb4e16d99723ecdbf7a"
        self.different_machine_id = "a1b2c3d4e5f60718293a4b5c6d7e8f90"
        self.start_date = date(2026, 1, 1)

    def test_bi_directional_verification_all_products(self):
        """
        Verify that keys generated for all product tiers (1..16) in LicenseManager
        are 100% valid in both the local validator and NextGen validator.
        """
        for prod_id in range(1, 17):
            with self.subTest(product_id=prod_id):
                code = LicenseGenerator.generate(
                    self.sample_machine_id,
                    prod_id,
                    self.start_date
                )
                self.assertIsNotNone(code)
                self.assertEqual(len(code), 19)  # XXXX-XXXX-XXXX-XXXX (16 chars + 3 hyphens)

                # 1. LicenseGenerator self-validation
                res_self = LicenseGenerator.validate(code, self.sample_machine_id)
                self.assertTrue(res_self["valid"], f"Self validation failed for prod {prod_id}: {res_self.get('error')}")
                self.assertEqual(res_self["product_id"], prod_id)
                self.assertEqual(res_self["start_year"], 2026)
                self.assertEqual(res_self["start_month"], 1)

                # 2. Local standalone VALIDATOR.py
                res_local = LocalValidator.validate(code, self.sample_machine_id)
                self.assertTrue(res_local["valid"], f"Local validation failed for prod {prod_id}: {res_local.get('error')}")
                self.assertEqual(res_local["product_id"], prod_id)
                self.assertEqual(res_local["start_year"], 2026)
                self.assertEqual(res_local["start_month"], 1)

                # 3. NextGen production LicenseValidator
                res_nextgen = NextGenValidator.validate(code, self.sample_machine_id)
                self.assertTrue(res_nextgen["valid"], f"NextGen validation failed for prod {prod_id}: {res_nextgen.get('error')}")
                self.assertEqual(res_nextgen["product_id"], prod_id)
                self.assertEqual(res_nextgen["start_year"], 2026)
                self.assertEqual(res_nextgen["start_month"], 1)

    def test_machine_id_hardware_binding(self):
        """
        Verify that a code generated for one hardware machine ID is strictly rejected
        when presented to a different machine ID.
        """
        code = LicenseGenerator.generate(
            self.sample_machine_id,
            product_id=4,  # Standard 1-Year License
            start_date=self.start_date
        )

        # Presentation on correct machine -> Valid
        res_correct = NextGenValidator.validate(code, self.sample_machine_id)
        self.assertTrue(res_correct["valid"])

        # Presentation on different machine -> Rejected
        res_wrong = NextGenValidator.validate(code, self.different_machine_id)
        self.assertFalse(res_wrong["valid"])
        self.assertIn("غير مخصص لهذا الجهاز", res_wrong.get("error", ""))

        # Also rejected in LicenseGenerator.validate
        res_wrong_gen = LicenseGenerator.validate(code, self.different_machine_id)
        self.assertFalse(res_wrong_gen["valid"])

    def test_date_encoding_and_chronology(self):
        """
        Verify accurate month and year encoding across multiple years from BASE_YEAR (2025).
        """
        test_dates = [
            (date(2025, 1, 1), 2025, 1),
            (date(2025, 12, 15), 2025, 12),
            (date(2026, 6, 20), 2026, 6),
            (date(2027, 8, 1), 2027, 8),
            (date(2028, 3, 10), 2028, 3),
            (date(2030, 11, 28), 2030, 11),
        ]

        for input_date, expected_year, expected_month in test_dates:
            with self.subTest(date=input_date):
                code = LicenseGenerator.generate(self.sample_machine_id, 4, input_date)
                res = NextGenValidator.validate(code, self.sample_machine_id)
                self.assertTrue(res["valid"])
                self.assertEqual(res["start_year"], expected_year)
                self.assertEqual(res["start_month"], expected_month)

    def test_emergency_password_recovery_identification(self):
        """
        Verify that emergency password recovery keys (product_id=16 and product_id=15)
        are specifically flagged as recovery codes by NextGen.
        """
        # product_id=16 (Official Emergency Code in LicenseManager)
        recovery_code_16 = LicenseGenerator.generate(self.sample_machine_id, 16, self.start_date)
        res_16 = NextGenValidator.validate(recovery_code_16, self.sample_machine_id)
        self.assertTrue(res_16["valid"])
        self.assertTrue(res_16.get("is_recovery"), "product_id=16 must be flagged as recovery")
        self.assertEqual(res_16["product_id"], 16)

        # product_id=15 (Dual support for top-up / legacy recovery)
        recovery_code_15 = LicenseGenerator.generate(self.sample_machine_id, 15, self.start_date)
        res_15 = NextGenValidator.validate(recovery_code_15, self.sample_machine_id)
        self.assertTrue(res_15["valid"])
        self.assertTrue(res_15.get("is_recovery"), "product_id=15 must be recognized as recovery")

        # Standard subscription (product_id=4) must NOT be flagged as recovery
        std_code = LicenseGenerator.generate(self.sample_machine_id, 4, self.start_date)
        res_std = NextGenValidator.validate(std_code, self.sample_machine_id)
        self.assertTrue(res_std["valid"])
        self.assertFalse(res_std.get("is_recovery"), "Standard product must not be flagged as recovery")

    def test_tamper_detection_single_character_mutation(self):
        """
        Verify that mutating any single character in a valid 16-character code
        results in immediate rejection due to HMAC signature or checksum mismatch.
        """
        valid_code = LicenseGenerator.generate(self.sample_machine_id, 4, self.start_date)
        clean_code = valid_code.replace("-", "")
        self.assertEqual(len(clean_code), 16)

        charset = LicenseGenerator.CHARSET

        # Test corrupting character at each position
        for pos in range(len(clean_code)):
            orig_char = clean_code[pos]
            # Pick a different character from CHARSET
            corrupted_char = charset[(charset.index(orig_char) + 1) % len(charset)]
            corrupted_clean = clean_code[:pos] + corrupted_char + clean_code[pos + 1:]
            corrupted_code = f"{corrupted_clean[:4]}-{corrupted_clean[4:8]}-{corrupted_clean[8:12]}-{corrupted_clean[12:]}"

            res = NextGenValidator.validate(corrupted_code, self.sample_machine_id)
            self.assertFalse(
                res["valid"],
                f"Tampered code at position {pos} ('{orig_char}' -> '{corrupted_char}') was unexpectedly accepted!"
            )

    def test_deterministic_reproducibility(self):
        """
        Verify that generating two codes with identical parameters yields the
        exact same deterministic 80-bit key.
        """
        code1 = LicenseGenerator.generate(self.sample_machine_id, 4, self.start_date)
        code2 = LicenseGenerator.generate(self.sample_machine_id, 4, self.start_date)
        self.assertEqual(code1, code2)

    def test_case_and_hyphen_insensitivity(self):
        """
        Verify that validation handles lowercase characters and missing hyphens gracefully.
        """
        code = LicenseGenerator.generate(self.sample_machine_id, 4, self.start_date)
        
        # Lowercase
        res_lower = NextGenValidator.validate(code.lower(), self.sample_machine_id)
        self.assertTrue(res_lower["valid"])

        # No hyphens
        res_no_hyphen = NextGenValidator.validate(code.replace("-", ""), self.sample_machine_id)
        self.assertTrue(res_no_hyphen["valid"])


if __name__ == "__main__":
    unittest.main()
