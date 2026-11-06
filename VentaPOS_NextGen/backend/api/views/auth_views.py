"""
Authentication views for VentaPOS NextGen.
Includes local login, demo login, password recovery, and password changes.
"""
import hashlib
from django.contrib.auth.models import User
from rest_framework import status, views
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.models import ClientLicense, UsedLicense
from api.utils.license_validator import LicenseValidator
from api.utils.security_utils import get_machine_id


class CustomAuthToken(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        password = request.data.get('password')
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            return Response({"error": "النظام غير مهيأ بعد. يرجى إعداد النظام."}, status=status.HTTP_400_BAD_REQUEST)

        has_no_password = (not user.has_usable_password()) or user.check_password("")
        if not password:
            if has_no_password:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user_id': user.pk,
                    'company_name': "VentaPOS",
                    'is_cloud': False
                })
            return Response({"error": "يرجى إدخال كلمة المرور"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"error": "كلمة المرور غير صحيحة"}, status=status.HTTP_401_UNAUTHORIZED)

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'company_name': "VentaPOS",
            'is_cloud': False
        })


class DemoAuthToken(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        if ClientLicense.all_objects.exclude(machine_id="DEMO_MACHINE").exists():
            return Response({"error": "النظام مفعل مسبقاً، الرجاء تسجيل الدخول العادي."}, status=status.HTTP_403_FORBIDDEN)

        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user, _ = User.objects.get_or_create(username='admin', defaults={'is_superuser': True})

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'company_name': 'نسخة تجريبية VentaPOS',
            'is_cloud': False
        })


class PasswordRecoveryView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        recovery_code = request.data.get('recovery_code')
        new_password = request.data.get('new_password')
        if not recovery_code or not new_password:
            return Response({"error": "الرجاء إدخال كود الاسترداد وكلمة المرور الجديدة"}, status=400)

        machine_id = get_machine_id()
        result = LicenseValidator.validate(recovery_code, machine_id)

        if not result.get("valid") or not (result.get("product_id") in (15, 16) or result.get("is_recovery")):
            return Response({"error": "كود الاسترداد غير صحيح أو غير مخصص لهذا الجهاز."}, status=400)

        code_hash = hashlib.sha256(recovery_code.encode()).hexdigest()
        if UsedLicense.objects.filter(code_hash=code_hash, is_deleted=False).exists():
            return Response({"error": "تم استخدام كود الاسترداد هذا من قبل."}, status=400)

        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            return Response({"error": "لا يوجد حساب مدير في النظام."}, status=400)

        admin_user.set_password(new_password)
        admin_user.save()

        UsedLicense.objects.create(code_hash=code_hash)
        return Response({"message": "تم تغيير كلمة المرور بنجاح."})


class HasPasswordView(views.APIView):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "غير مصرح لك"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"has_password": user.has_usable_password() and user.check_password("") is False})


class ChangePasswordView(views.APIView):
    def post(self, request):
        old_password = request.data.get("old_password", "")
        new_password = request.data.get("new_password", "")

        if old_password is None or new_password is None:
            return Response({"error": "بيانات غير صالحة"}, status=400)

        user = request.user
        if not user.is_authenticated:
            return Response({"error": "غير مصرح لك"}, status=status.HTTP_401_UNAUTHORIZED)

        has_password = user.has_usable_password() and user.check_password("") is False

        if has_password and not user.check_password(old_password):
            return Response({"error": "كلمة المرور الحالية غير صحيحة"}, status=400)

        user.set_password(new_password)
        user.save()
        msg = "تم تغيير كلمة المرور بنجاح." if new_password else "تم إلغاء كلمة المرور، ستتمكن من الدخول مباشرة."
        return Response({"message": msg})
