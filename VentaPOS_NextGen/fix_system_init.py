import re

with open('backend/api/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace SystemInitializationView
old_view = r'class SystemInitializationView\(views\.APIView\):[\s\S]*?(?=# ===========================================================================\n# Standard ViewSets)'

new_view = '''class ChangePasswordView(views.APIView):
    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        if not old_password or not new_password:
            return Response({"error": "الرجاء إدخال كلمة المرور الحالية والجديدة"}, status=400)
        
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "غير مصرح لك"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(old_password):
            return Response({"error": "كلمة المرور الحالية غير صحيحة"}, status=400)
            
        user.set_password(new_password)
        user.save()
        return Response({"message": "تم تغيير كلمة المرور بنجاح."})


class SystemInitializationView(views.APIView):
    """
    Handles the first-time setup of the system.
    Creates the default Branch, CompanySettings, and the master Admin User.
    """
    permission_classes = [] # Allow unauthenticated access for init

    def get(self, request):
        is_initialized = User.objects.filter(is_superuser=True).exists()
        company = CompanySetting.objects.first()
        return Response({
            "initialized": is_initialized,
            "company_name": company.company_name if company else None
        })

    def post(self, request):
        if User.objects.filter(is_superuser=True).exists():
            return Response({"error": "النظام مهيأ بالفعل."}, status=status.HTTP_400_BAD_REQUEST)
            
        company_name = request.data.get('company_name')
        branch_name = request.data.get('branch_name')
        password = request.data.get('password')
        license_code = request.data.get('license_code')
        phone1 = request.data.get('phone1', '')
        phone2 = request.data.get('phone2', '')
        
        if not all([company_name, branch_name, password, license_code]):
            return Response({"error": "الرجاء إدخال جميع البيانات الإلزامية بما فيها كود التفعيل"}, status=status.HTTP_400_BAD_REQUEST)
            
        from .utils.license_validator import LicenseValidator
        from .utils.security_utils import get_machine_id
        from django.db import transaction
        
        machine_id = get_machine_id()
        validation_result = LicenseValidator.validate(license_code, machine_id)
        
        if not validation_result.get("valid"):
            return Response({"error": validation_result.get("error", "كود تفعيل غير صالح")}, status=status.HTTP_400_BAD_REQUEST)
            
        import random
        import string
        from django.contrib.auth.hashers import make_password
        
        recovery_code = f"VNTA-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
        
        with transaction.atomic():
            # Create master user
            User.objects.filter(is_superuser=True).delete() # clean up any partial state
            user = User.objects.create_superuser('admin', 'admin@ventapos.local', password)
            user.save()
            
            # Create Company Setting
            company = CompanySetting.objects.first()
            if not company:
                company = CompanySetting.objects.create(
                    company_name=company_name,
                    phone1=phone1,
                    phone2=phone2
                )
            else:
                company.company_name = company_name
                company.phone1 = phone1
                company.phone2 = phone2
                company.save()
                
            # Create default branch
            branch = Branch.objects.filter(name=branch_name).first()
            if not branch:
                Branch.objects.create(name=branch_name, local_id=1)
                
            # Store recovery code as special license type
            from .utils.security_utils import generate_record_signature
            import datetime
            from dateutil.relativedelta import relativedelta

            rec_license = ClientLicense.objects.create(
                machine_id=machine_id,
                license_code=make_password(recovery_code),
                plan_type="RECOVERY"
            )
            
            # Save the actual activation license
            ClientLicense.objects.exclude(plan_type="RECOVERY").update(is_active=False)
            start_date = datetime.date(validation_result["start_year"], validation_result["start_month"], 1)
            expiry_date = start_date + relativedelta(years=1)

            new_license = ClientLicense.objects.create(
                license_code=license_code,
                product_id=validation_result.get("product_id", 1),
                invoices_balance=999999,
                is_active=True,
                expiry_date=expiry_date,
                machine_id=machine_id
            )
            
            # Sign it securely
            new_license.license_code_hash = generate_record_signature(
                new_license.expiry_date, 
                new_license.invoices_balance, 
                machine_id, 
                new_license.product_id, 
                True
            )
            new_license.save()
                
        return Response({"message": "تم تهيئة النظام بنجاح", "recovery_code": recovery_code}, status=status.HTTP_201_CREATED)

'''

content = re.sub(old_view, new_view, content, count=1)

with open('backend/api/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SystemInitializationView updated and ChangePasswordView added.")
