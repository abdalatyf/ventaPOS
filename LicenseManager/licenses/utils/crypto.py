import hashlib
import hmac
import struct
from datetime import date

class LicenseGenerator:
    CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    # تأكد أن هذا المفتاح هو نفس المفتاح الذي استخدمته في التوليد
    SECRET_KEY = b"JqxQQAKo0BbI76tknaKlhd0rC9hDcam_bqJywXmaXHqAKkVPRZhzgRjHX-zME11enx2oB8o_ivJCn2pXBX-Pow"
    BASE_YEAR = 2025

    @staticmethod
    def _get_machine_hash(machine_id):
        raw_hash = hashlib.sha256(machine_id.encode()).digest()
        return struct.unpack('>I', raw_hash[:4])[0]

    @staticmethod
    def _get_date_code(start_date):
        year_diff = start_date.year - LicenseGenerator.BASE_YEAR
        if year_diff < 0: year_diff = 0
        months_code = (year_diff * 12) + (start_date.month - 1)
        return min(months_code, 255)

    @staticmethod
    def _int_to_custom_base32(number):
        result = []
        while number > 0:
            number, remainder = divmod(number, 32)
            result.append(LicenseGenerator.CHARSET[remainder])
        while len(result) < 16:
            result.append(LicenseGenerator.CHARSET[0])
        return ''.join(reversed(result))

    @staticmethod
    def _custom_base32_to_int(code_str):
        """
        تحويل النص (16 حرف) إلى رقم ضخم مرة أخرى
        """
        # إزالة الفواصل إن وجدت
        clean_code = code_str.replace('-', '').upper()
        number = 0
        for char in clean_code:
            try:
                val = LicenseGenerator.CHARSET.index(char)
                number = (number * 32) + val
            except ValueError:
                raise ValueError("كود يحتوي على حروف غير صالحة")
        return number

    # ---------------------------------------------------
    # الدالة الجديدة: التحقق وفك التشفير
    # ---------------------------------------------------
    @classmethod
    def validate(cls, license_code, machine_id):
        """
        فحص الكود واستخراج البيانات منه
        """
        try:
            # 1. تحويل الكود لرقم
            full_int = cls._custom_base32_to_int(license_code)

            # 2. فصل التوقيع عن البيانات المشفرة
            # الهيكل: [Signature 36 bits] | [Masked Data 44 bits]
            final_sig = full_int >> 44
            masked_data = full_int & ((1 << 44) - 1)

            # 3. إزالة القناع (Unmasking)
            # نعيد بناء القناع من التوقيع (لأننا نعرف المعادلة)
            mask = (final_sig << 8) | (final_sig >> 28)
            data_block = masked_data ^ mask # XOR يعكس نفسه

            # 4. تفكيك البيانات
            # Data Block: [Machine 32] | [Date 8] | [Product 4]
            extracted_prod = data_block & 0xF
            extracted_date_code = (data_block >> 4) & 0xFF
            extracted_machine_hash = (data_block >> 12) & 0xFFFFFFFF

            # 5. التحقق الأمني (Re-Hashing)
            # نعيد حساب التوقيع بناءً على البيانات المستخرجة
            # لو التوقيع المحسوب != التوقيع الموجود في الكود، يبقى الكود مزور
            payload_bytes = struct.pack('>IBB', extracted_machine_hash, extracted_prod, extracted_date_code)
            recalculated_sig_bytes = hmac.new(cls.SECRET_KEY, payload_bytes, hashlib.sha256).digest()
            
            recalc_sig_int = struct.unpack('>Q', recalculated_sig_bytes[:8])[0]
            recalc_sig_final = recalc_sig_int & ((1 << 36) - 1)

            if recalc_sig_final != final_sig:
                return {"valid": False, "error": "كود مزور (التوقيع غير مطابق)"}

            # 6. التحقق من الجهاز
            # هل بصمة الجهاز الموجودة في الكود تطابق الجهاز الحالي؟
            current_machine_hash = cls._get_machine_hash(machine_id)
            if extracted_machine_hash != current_machine_hash:
                return {"valid": False, "error": "هذا الكود غير مخصص لهذا الجهاز"}

            # 7. استخراج البيانات البشرية (التاريخ والمنتج)
            # استرجاع التاريخ من الكود
            year = cls.BASE_YEAR + (extracted_date_code // 12)
            month = (extracted_date_code % 12) + 1
            
            # (Product ID stored is 0-15, we convert back to 1-16)
            real_product_id = extracted_prod + 1

            return {
                "valid": True,
                "product_id": real_product_id,
                "start_month": month,
                "start_year": year,
                "machine_valid": True
            }

        except Exception as e:
            return {"valid": False, "error": f"كود غير صالح: {str(e)}"}

    # --- دالة التوليد (Generate) القديمة كما هي ---
    @classmethod
    def generate(cls, machine_id, product_id, start_date):
        machine_int = cls._get_machine_hash(machine_id)
        prod_int = (product_id - 1) & 0xF
        date_int = cls._get_date_code(start_date)

        payload_bytes = struct.pack('>IBB', machine_int, prod_int, date_int)
        signature = hmac.new(cls.SECRET_KEY, payload_bytes, hashlib.sha256).digest()
        
        sig_int = struct.unpack('>Q', signature[:8])[0]
        sig_mask = (1 << 36) - 1
        final_sig = sig_int & sig_mask

        data_block = (machine_int << 12) | (date_int << 4) | prod_int
        mask = (final_sig << 8) | (final_sig >> 28) 
        masked_data = data_block ^ mask

        full_code_int = (final_sig << 44) | masked_data
        raw_code = cls._int_to_custom_base32(full_code_int)
        return f"{raw_code[:4]}-{raw_code[4:8]}-{raw_code[8:12]}-{raw_code[12:]}"