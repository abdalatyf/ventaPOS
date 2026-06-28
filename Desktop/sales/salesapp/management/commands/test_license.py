"""
===================================================
 اختبارات نظام الترخيص — النسخة النهائية
 شغّل بالأمر: python test_license_system_v2.py
===================================================
المنطق المتفق عليه:
- الحماية الحقيقية = التاريخ (بداية + نهاية)
- عدد الفواتير = سيفتي نت بس
- كروت الشحن تُضاف للرصيد، مش باقة مستقلة
- Pro = [1, 4, 5, 6, 7] (التجريبي Pro عشان يجرب كل حاجة)
- كل فاتورة تخصم من الرصيد دايماً
===================================================
"""
import hashlib
import hmac
import struct
import unittest
from datetime import date, timedelta


# =====================================================
# LicenseValidator (مستقل عن Django)
# =====================================================
class LicenseValidator:
    CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    BASE_YEAR = 2025

    @staticmethod
    def _get_key():
        encrypted_bytes = [74,113,120,81,81,65,75,111,48,66,98,73,55,54,116,107,110,97,75,108,
                           104,100,48,114,67,57,104,68,99,97,109,95,98,113,74,121,119,88,109,97,
                           88,72,113,65,75,107,86,80,82,90,104,122,103,82,106,72,88,45,122,77,
                           69,49,49,101,110,120,50,111,66,56,111,95,105,118,74,67,110,50,112,88,
                           66,88,45,80,111,119]
        return bytes(encrypted_bytes)

    @staticmethod
    def _get_machine_hash(machine_id):
        raw_hash = hashlib.sha256(machine_id.encode()).digest()
        return struct.unpack('>I', raw_hash[:4])[0]

    @staticmethod
    def _custom_base32_to_int(code_str):
        clean_code = code_str.replace('-', '').upper()
        number = 0
        for char in clean_code:
            try:
                val = LicenseValidator.CHARSET.index(char)
                number = (number * 32) + val
            except ValueError:
                raise ValueError("كود غير صالح")
        return number

    @classmethod
    def validate(cls, license_code, machine_id):
        try:
            full_int = cls._custom_base32_to_int(license_code)
            final_sig = full_int >> 44
            masked_data = full_int & ((1 << 44) - 1)
            mask = (final_sig << 8) | (final_sig >> 28)
            data_block = masked_data ^ mask
            extracted_prod       = data_block & 0xF
            extracted_date_code  = (data_block >> 4) & 0xFF
            extracted_machine_hash = (data_block >> 12) & 0xFFFFFFFF
            payload_bytes = struct.pack('>IBB', extracted_machine_hash,
                                        extracted_prod, extracted_date_code)
            secret = cls._get_key()
            recalculated_sig_bytes = hmac.new(secret, msg=payload_bytes,
                                              digestmod=hashlib.sha256).digest()
            recalc_sig_int   = struct.unpack('>Q', recalculated_sig_bytes[:8])[0]
            recalc_sig_final = recalc_sig_int & ((1 << 36) - 1)
            if recalc_sig_final != final_sig:
                return {"valid": False, "error": "توقيع غير مطابق"}
            current_machine_hash = cls._get_machine_hash(machine_id)
            if extracted_machine_hash != current_machine_hash:
                return {"valid": False, "error": "هذا الكود غير مخصص لهذا الجهاز"}
            year  = cls.BASE_YEAR + (extracted_date_code // 12)
            month = (extracted_date_code % 12) + 1
            return {"valid": True, "product_id": extracted_prod + 1,
                    "start_month": month, "start_year": year}
        except Exception:
            return {"valid": False, "error": "كود تالف أو غير صالح"}


# =====================================================
# MockClientLicense
# =====================================================
class MockClientLicense:
    # المتفق عليه نهائياً
    PRO_PRODUCTS          = [1, 4, 5, 6, 7]   # التجريبي + إدارة كاملة
    BASIC_PRODUCTS        = [2, 3]             # طباعة فقط
    LIFETIME_PRODUCTS     = [3, 7]             # لا تنتهي بالوقت
    CHARGE_CARDS          = list(range(10, 16))# 10-15
    BASE_SUBSCRIPTIONS    = list(range(1, 10)) # 1-9 (باقات حقيقية)

    def __init__(self, product_id, start_date, expiry_date=None,
                 invoices_balance=0, is_active=True, pk=1):
        self.product_id       = product_id
        self.start_date       = start_date
        self.expiry_date      = expiry_date
        self.invoices_balance = invoices_balance
        self.is_active        = is_active
        self.pk               = pk

    def is_pro(self):
        return self.product_id in self.PRO_PRODUCTS

    def is_base_subscription(self):
        """هل هو باقة أساسية (مش كارت شحن)؟"""
        return self.product_id in self.BASE_SUBSCRIPTIONS

    def is_active_subscription(self):
        """هل الاشتراك ساري؟ (بيفحص التاريخ)"""
        if not self.is_base_subscription():
            return False
        if self.product_id in self.LIFETIME_PRODUCTS:
            return True
        if self.expiry_date is None:
            return False
        return date.today() <= self.expiry_date


# =====================================================
# محاكاة add_receipt (المنطق الكامل المتفق عليه)
# =====================================================
def simulate_add_receipt(active_license, invoice_date):
    """
    المنطق الكامل المتفق عليه:
    1. لازم يكون في اشتراك أساسي ساري
    2. التاريخ لازم يكون داخل فترة الاشتراك (بداية + نهاية)  ← الحماية الحقيقية
    3. الرصيد > 0  ← سيفتي نت بس
    4. خصم فاتورة واحدة دايماً
    """
    # 1. فحص وجود اشتراك أساسي ساري
    if not active_license or not active_license.is_active_subscription():
        return {"ok": False, "error": "لا يوجد اشتراك ساري"}

    # 2. فحص التاريخ — الطرفين
    lic_start = active_license.start_date.replace(day=1)
    if invoice_date < lic_start:
        return {"ok": False, "error": "التاريخ يسبق بداية الاشتراك"}

    # ✅ الفحص الناقص في الكود الأصلي
    if active_license.expiry_date:
        lic_end = active_license.expiry_date.replace(day=1)
        if invoice_date > lic_end:
            return {"ok": False, "error": "التاريخ بعد انتهاء الاشتراك"}

    # 3. فحص الرصيد (سيفتي نت)
    if active_license.invoices_balance <= 0:
        return {"ok": False, "error": "نفد رصيد الفواتير"}

    # 4. خصم
    active_license.invoices_balance -= 1
    return {"ok": True, "remaining": active_license.invoices_balance}


# =====================================================
# 1. اختبارات LicenseValidator
# =====================================================
class TestLicenseValidator(unittest.TestCase):

    def test_empty_code_rejected(self):
        result = LicenseValidator.validate("", "ANY")
        self.assertFalse(result["valid"])

    def test_corrupted_code_rejected(self):
        result = LicenseValidator.validate("XXXX-YYYY-ZZZZ", "ANY")
        self.assertFalse(result["valid"])

    def test_wrong_machine_rejected(self):
        result = LicenseValidator.validate("AAAA-BBBB-CCCC", "WRONG-MACHINE")
        self.assertFalse(result["valid"])

    def test_charset_no_ambiguous_chars(self):
        for banned in ['0', '1', 'I', 'O']:
            self.assertNotIn(banned, LicenseValidator.CHARSET)

    def test_machine_hash_deterministic(self):
        mid = "DISK-5822-S9J1"
        self.assertEqual(
            LicenseValidator._get_machine_hash(mid),
            LicenseValidator._get_machine_hash(mid)
        )

    def test_different_machines_different_hashes(self):
        h1 = LicenseValidator._get_machine_hash("DISK-0001")
        h2 = LicenseValidator._get_machine_hash("DISK-0002")
        self.assertNotEqual(h1, h2)

    def test_hmac_api_correct(self):
        secret  = LicenseValidator._get_key()
        payload = struct.pack('>IBB', 12345678, 3, 5)
        result  = hmac.new(secret, msg=payload, digestmod=hashlib.sha256).digest()
        self.assertEqual(len(result), 32)

    def test_dashes_ignored(self):
        r1 = LicenseValidator._custom_base32_to_int("AAAA-BBBB")
        r2 = LicenseValidator._custom_base32_to_int("AAAABBBB")
        self.assertEqual(r1, r2)


# =====================================================
# 2. اختبارات Pro / Basic
# =====================================================
class TestProBasicLogic(unittest.TestCase):

    def _lic(self, pid):
        return MockClientLicense(pid, date.today(),
                                 date.today() + timedelta(days=365), 5000)

    def test_trial_IS_pro(self):
        """التجريبي Pro عشان يجرب كل حاجة"""
        self.assertTrue(self._lic(1).is_pro())

    def test_basic_yearly_NOT_pro(self):
        self.assertFalse(self._lic(2).is_pro())

    def test_basic_lifetime_NOT_pro(self):
        self.assertFalse(self._lic(3).is_pro())

    def test_pro_yearly_IS_pro(self):
        for pid in [4, 5, 6]:
            self.assertTrue(self._lic(pid).is_pro(), f"Product {pid} يجب أن يكون Pro")

    def test_pro_lifetime_IS_pro(self):
        self.assertTrue(self._lic(7).is_pro())

    def test_online_NOT_pro(self):
        for pid in [8, 9]:
            self.assertFalse(self._lic(pid).is_pro())

    def test_charge_cards_NOT_pro(self):
        for pid in range(10, 16):
            self.assertFalse(self._lic(pid).is_pro())


# =====================================================
# 3. اختبارات is_active_subscription
# =====================================================
class TestActiveSubscription(unittest.TestCase):

    def test_active_subscription_valid(self):
        lic = MockClientLicense(4, date.today(),
                                date.today() + timedelta(days=365), 5000)
        self.assertTrue(lic.is_active_subscription())

    def test_expired_subscription_invalid(self):
        lic = MockClientLicense(4, date(2023,1,1),
                                date.today() - timedelta(days=1), 5000)
        self.assertFalse(lic.is_active_subscription())

    def test_lifetime_always_active(self):
        for pid in [3, 7]:
            lic = MockClientLicense(pid, date.today(), None, 99999999)
            self.assertTrue(lic.is_active_subscription())

    def test_charge_card_alone_NOT_subscription(self):
        """كارت الشحن لوحده مش اشتراك أساسي"""
        for pid in range(10, 16):
            lic = MockClientLicense(pid, date.today(), None, 500)
            self.assertFalse(lic.is_active_subscription())


# =====================================================
# 4. اختبارات add_receipt (المنطق الكامل)
# =====================================================
class TestAddReceiptLogic(unittest.TestCase):

    def _active_lic(self, pid=4, balance=5000, days=365):
        exp = date.today() + timedelta(days=days) if days else None
        return MockClientLicense(pid, date(2024, 1, 1), exp, balance)

    # --- فحص الاشتراك ---

    def test_no_license_blocked(self):
        result = simulate_add_receipt(None, date(2024, 6, 1))
        self.assertFalse(result["ok"])
        self.assertIn("اشتراك", result["error"])

    def test_expired_subscription_blocked(self):
        lic = MockClientLicense(4, date(2023,1,1),
                                date.today() - timedelta(days=1), 5000)
        result = simulate_add_receipt(lic, date(2023, 6, 1))
        self.assertFalse(result["ok"])

    def test_charge_card_alone_blocked(self):
        """كارت شحن بدون اشتراك أساسي = ممنوع"""
        lic = MockClientLicense(10, date.today(), None, 500)
        result = simulate_add_receipt(lic, date.today().replace(day=1))
        self.assertFalse(result["ok"])
        self.assertIn("اشتراك", result["error"])

    # --- فحص التاريخ (الحماية الحقيقية) ---

    def test_invoice_before_start_blocked(self):
        """🔴 فاتورة قبل بداية الاشتراك = ممنوع"""
        lic = self._active_lic()
        before_start = date(2023, 12, 1)  # قبل start_date (2024-01-01)
        result = simulate_add_receipt(lic, before_start)
        self.assertFalse(result["ok"])
        self.assertIn("يسبق", result["error"])

    def test_invoice_after_expiry_blocked(self):
        """🔴 فاتورة بعد انتهاء الاشتراك = ممنوع (الفحص الناقص في الأصل)"""
        lic = self._active_lic(days=30)  # ينتهي بعد 30 يوم
        after_expiry = date.today() + timedelta(days=60)
        after_expiry = after_expiry.replace(day=1)
        result = simulate_add_receipt(lic, after_expiry)
        self.assertFalse(result["ok"])
        self.assertIn("بعد انتهاء", result["error"])

    def test_invoice_within_range_allowed(self):
        """فاتورة داخل فترة الاشتراك = مسموح"""
        lic = self._active_lic()
        valid_date = date(2024, 6, 1)
        result = simulate_add_receipt(lic, valid_date)
        self.assertTrue(result["ok"])

    def test_lifetime_no_end_date_check(self):
        """Lifetime: مفيش فحص تاريخ انتهاء"""
        lic = MockClientLicense(7, date(2024,1,1), None, 99999999)
        far_future = date(2090, 1, 1)
        result = simulate_add_receipt(lic, far_future)
        self.assertTrue(result["ok"])

    # --- فحص الرصيد (سيفتي نت) ---

    def test_zero_balance_blocked(self):
        """رصيد = 0 → ممنوع حتى لو الاشتراك ساري"""
        lic = self._active_lic(balance=0)
        result = simulate_add_receipt(lic, date(2024, 6, 1))
        self.assertFalse(result["ok"])
        self.assertIn("رصيد", result["error"])

    def test_balance_deducted_after_invoice(self):
        """كل فاتورة تخصم واحدة من الرصيد دايماً"""
        lic = self._active_lic(balance=100)
        simulate_add_receipt(lic, date(2024, 6, 1))
        self.assertEqual(lic.invoices_balance, 99)

    def test_lifetime_balance_also_deducted(self):
        """حتى Lifetime يخصم (السيفتي نت شامل الكل)"""
        lic = MockClientLicense(7, date(2024,1,1), None, 99999999)
        simulate_add_receipt(lic, date(2024, 6, 1))
        self.assertEqual(lic.invoices_balance, 99999998)

    def test_multiple_invoices_deduct_correctly(self):
        """10 فواتير تخصم 10 من الرصيد"""
        lic = self._active_lic(balance=50)
        for i in range(10):
            simulate_add_receipt(lic, date(2024, 6, 1))
        self.assertEqual(lic.invoices_balance, 40)

    # --- سيناريوهات كاملة ---

    def test_scenario_expired_sub_with_charge_card(self):
        """
        سيناريو: اشتراك منتهي + كارت شحن فيه رصيد
        النتيجة المتوقعة: ممنوع (مفيش اشتراك ساري)
        """
        expired_sub = MockClientLicense(4, date(2023,1,1),
                                        date(2023,12,31), 0)
        # العميل حاول يشحن بكارت لكن اشتراكه منتهي
        # get_active_license هيرجع None لأن مفيش اشتراك ساري
        result = simulate_add_receipt(None, date(2024, 6, 1))
        self.assertFalse(result["ok"])

    def test_scenario_active_sub_plus_charge_card(self):
        """
        سيناريو: اشتراك ساري + كارت شحن مضاف للرصيد
        النتيجة: مسموح والرصيد المدمج يُخصم
        """
        # get_active_license بتدمج الرصيدين: 5000 + 300 = 5300
        merged_lic = self._active_lic(pid=2, balance=5300)
        result = simulate_add_receipt(merged_lic, date(2024, 6, 1))
        self.assertTrue(result["ok"])
        self.assertEqual(merged_lic.invoices_balance, 5299)

    def test_scenario_machine_time_manipulation(self):
        """
        سيناريو: العميل غير تاريخ الجهاز للأمام (تحايل)
        الحماية: الفاتورة بتاريخ مستقبلي بعد انتهاء الاشتراك = ممنوع
        """
        lic = self._active_lic(days=30)  # ينتهي بعد 30 يوم
        # العميل غير التاريخ للأمام 6 أشهر
        manipulated_date = date.today() + timedelta(days=180)
        manipulated_date = manipulated_date.replace(day=1)
        result = simulate_add_receipt(lic, manipulated_date)
        self.assertFalse(result["ok"])
        self.assertIn("بعد انتهاء", result["error"])


# =====================================================
# تشغيل
# =====================================================
if __name__ == '__main__':
    test_classes = [
        ("1️⃣  LicenseValidator",         TestLicenseValidator),
        ("2️⃣  Pro / Basic",               TestProBasicLogic),
        ("3️⃣  is_active_subscription",    TestActiveSubscription),
        ("4️⃣  add_receipt (كامل)",        TestAddReceiptLogic),
    ]

    total_ok = total_fail = total_err = 0

    print("=" * 58)
    print("  🔍 اختبارات نظام الترخيص — النسخة النهائية")
    print("=" * 58)

    loader = unittest.TestLoader()
    for label, cls in test_classes:
        print(f"\n{'─'*58}")
        print(f"  {label}")
        print(f"{'─'*58}")
        suite  = loader.loadTestsFromTestCase(cls)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        total_ok   += result.testsRun - len(result.failures) - len(result.errors)
        total_fail += len(result.failures)
        total_err  += len(result.errors)

    print("\n" + "=" * 58)
    print(f"  ✅ ناجح : {total_ok}")
    print(f"  ❌ فاشل : {total_fail}")
    print(f"  💥 خطأ  : {total_err}")
    print("=" * 58)