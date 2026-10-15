import hashlib
import hmac
import struct
from datetime import date

class LicenseValidator:
    # 1. الأبجدية (يجب أن تكون مطابقة تماماً لتطبيق المدير)
    CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    BASE_YEAR = 2025

    @staticmethod
    def _get_key():
        """
        استرجاع المفتاح من الأرقام المبعثرة وقت التشغيل فقط
        """
        encrypted_bytes = [74, 113, 120, 81, 81, 65, 75, 111, 48, 66, 98, 73, 55, 54, 116, 107, 110, 97, 75, 108, 104, 100, 48, 114, 67, 57, 104, 68, 99, 97, 109, 95, 98, 113, 74, 121, 119, 88, 109, 97, 88, 72, 113, 65, 75, 107, 86, 80, 82, 90, 104, 122, 103, 82, 106, 72, 88, 45, 122, 77, 69, 49, 49, 101, 110, 120, 50, 111, 66, 56, 111, 95, 105, 118, 74, 67, 110, 50, 112, 88, 66, 88, 45, 80, 111, 119]
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
        """
        دالة الفحص (Only Validate)
        """
        try:
            full_int = cls._custom_base32_to_int(license_code)

            # 1. فصل التوقيع والبيانات
            final_sig = full_int >> 44
            masked_data = full_int & ((1 << 44) - 1)

            # 2. إزالة القناع (XOR Unmasking)
            mask = (final_sig << 8) | (final_sig >> 28)
            data_block = masked_data ^ mask

            # 3. استخراج البيانات
            extracted_prod = data_block & 0xF
            extracted_date_code = (data_block >> 4) & 0xFF
            extracted_machine_hash = (data_block >> 12) & 0xFFFFFFFF

            # 4. التأكد من صحة التوقيع (باستخدام المفتاح المخفي)
            payload_bytes = struct.pack('>IBB', extracted_machine_hash, extracted_prod, extracted_date_code)
            
            secret = cls._get_key()
            
            recalculated_sig_bytes = hmac.new(secret, payload_bytes, hashlib.sha256).digest()
            recalc_sig_int = struct.unpack('>Q', recalculated_sig_bytes[:8])[0]
            recalc_sig_final = recalc_sig_int & ((1 << 36) - 1)

            if recalc_sig_final != final_sig:
                return {"valid": False, "error": "كود غير صحيح (توقيع غير مطابق)"}

            # 5. مطابقة بصمة الجهاز
            current_machine_hash = cls._get_machine_hash(machine_id)
            if extracted_machine_hash != current_machine_hash:
                return {"valid": False, "error": "هذا الكود غير مخصص لهذا الجهاز"}

            # 6. النتيجة النهائية
            year = cls.BASE_YEAR + (extracted_date_code // 12)
            month = (extracted_date_code % 12) + 1
            real_product_id = extracted_prod + 1

            return {
                "valid": True,
                "product_id": real_product_id,
                "start_month": month,
                "start_year": year
            }

        except Exception:
            return {"valid": False, "error": "كود تالف أو غير صالح"}
