import time
from django.utils import timezone
from django.http import JsonResponse
from api.models import ClientLicense
from api.utils.security_utils import generate_record_signature, get_machine_id

class LicenseEnforcementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.conf import settings
        # if getattr(settings, 'DEBUG', False):
        #     return self.get_response(request)
            
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return self.get_response(request)

        # Ignore activation and status checks
        excluded_urls = ['/api/v1/license/activate/', '/api/v1/license/status/']
        if any(request.path.startswith(url) for url in excluded_urls):
            return self.get_response(request)

        is_saving_receipt = False
        if request.path.startswith('/api/v1/receipts/') and request.method == 'POST':
            is_saving_receipt = True

        from django.core.cache import cache
        
        cache_key = 'license_check_status'
        cached_status = cache.get(cache_key)
        
        if cached_status == 'valid' and not is_saving_receipt:
            return self.get_response(request)

        try:
            machine_id = cache.get('machine_id')
            if not machine_id:
                machine_id = get_machine_id()
                cache.set('machine_id', machine_id, 3600 * 24)

            today = timezone.now().date()
            
            all_active_licenses = ClientLicense.objects.filter(is_active=True)
            
            valid_time_license = None
            total_invoices_balance = 0

            for lic in all_active_licenses:
                expected_sig = generate_record_signature(lic.expiry_date, lic.invoices_balance, machine_id, lic.product_id, lic.is_active)
                if lic.license_code_hash != expected_sig:
                    ClientLicense.objects.filter(pk=lic.pk).update(is_active=False)
                    continue

                if lic.product_id < 10:
                    if not valid_time_license or (lic.expiry_date and lic.expiry_date > valid_time_license.expiry_date):
                        valid_time_license = lic
                
                total_invoices_balance += lic.invoices_balance

            if not valid_time_license:
                # No licenses exist AT ALL -> We are in DEMO MODE.
                # Allow everything (the startup script will wipe the DB on next restart).
                pass
            elif valid_time_license.expiry_date and today > valid_time_license.expiry_date:
                # License exists but EXPIRED -> READ-ONLY MODE.
                if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                    if request.path.startswith('/api/'):
                        return JsonResponse({"error": "license_expired", "message": "انتهى الاشتراك. التطبيق الآن في وضع القراءة فقط."}, status=402)
            
            if is_saving_receipt and total_invoices_balance <= 0 and valid_time_license:
                return JsonResponse({"error": "license_expired", "message": "Invoice balance exhausted. Please add invoice balance."}, status=403)

            cache.set(cache_key, 'valid', 300) # 5 minutes cache
            return self.get_response(request)

        except Exception as e:
            print(f"License Middleware Error: {e}")
            if request.path.startswith('/api/'):
                return JsonResponse({"error": "server_error", "message": "An error occurred during license validation."}, status=500)
            return self.get_response(request)
