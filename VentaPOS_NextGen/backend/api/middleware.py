import sys
import time
from django.utils import timezone
from django.http import JsonResponse
from api.models import ClientLicense, Receipt
from api.utils.security_utils import generate_record_signature, get_machine_id

def safe_console_print(msg):
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        try:
            if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer:
                sys.stdout.buffer.write((msg + '\n').encode('utf-8', errors='replace'))
                sys.stdout.buffer.flush()
            else:
                encoded = msg.encode('ascii', errors='replace').decode('ascii')
                print(encoded, flush=True)
        except Exception:
            pass
    except Exception:
        pass

class ConsoleRequestLoggingMiddleware:
    """
    Measures request duration and streams live [BACKEND] HTTP request/response
    and error logs directly to the cmd console window.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Exclude frontend log uploads to prevent duplicate/recursive logging
        if request.path.startswith('/api/v1/frontend-logs/'):
            return self.get_response(request)

        start_time = time.time()
        try:
            response = self.get_response(request)
        except Exception as exc:
            duration_ms = int((time.time() - start_time) * 1000)
            safe_console_print(f"[BACKEND][ERROR] {request.method} {request.get_full_path()} -> EXCEPTION: {exc} ({duration_ms}ms)")
            raise

        duration_ms = int((time.time() - start_time) * 1000)
        status = response.status_code

        if status >= 400:
            err_detail = ""
            try:
                if hasattr(response, 'data') and response.data:
                    err_detail = f" | {response.data}"
                elif hasattr(response, 'content') and response.content:
                    raw = response.content.decode('utf-8', errors='ignore').strip()
                    if raw:
                        err_detail = f" | {raw[:200]}"
            except Exception:
                pass
            safe_console_print(f"[BACKEND][ERROR] {request.method} {request.get_full_path()} -> {status} ({duration_ms}ms){err_detail}")
        else:
            safe_console_print(f"[BACKEND] {request.method} {request.get_full_path()} -> {status} ({duration_ms}ms)")

        return response


WHITELIST_PREFIXES = [
    '/admin/',
    '/static/',
    '/api/v1/license/',
    '/api/v1/tools/backup/',
    '/api/v1/auth/',
    '/api/v1/frontend-logs/',
    '/api/v1/system/',
]

class LicenseEnforcementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(request.path.startswith(prefix) for prefix in WHITELIST_PREFIXES):
            return self.get_response(request)

        try:
            # Monotonic clock-rollback detection against latest license and receipt
            latest_lic = ClientLicense.all_objects.exclude(machine_id="DEMO_MACHINE").order_by('-created_at').first()
            if not latest_lic:
                # Demo Mode: permit operations, database is ephemeral
                return self.get_response(request)

            if latest_lic.created_at and timezone.now() < latest_lic.created_at - timezone.timedelta(minutes=5):
                return JsonResponse({
                    "error": "clock_rollback",
                    "message": "تم اكتشاف تلاعب في وقت النظام. يرجى ضبط الساعة والتاريخ الحالي بشكل صحيح."
                }, status=403)

            latest_receipt = Receipt.all_objects.order_by('-created_at').first()
            if latest_receipt and latest_receipt.created_at:
                if timezone.now() < latest_receipt.created_at - timezone.timedelta(minutes=5):
                    return JsonResponse({
                        "error": "clock_rollback",
                        "message": "تم اكتشاف تلاعب في وقت النظام. يرجى ضبط الساعة والتاريخ الحالي بشكل صحيح."
                    }, status=403)

            from django.core.cache import cache
            machine_id = cache.get('machine_id')
            if not machine_id:
                machine_id = get_machine_id()
                cache.set('machine_id', machine_id, 3600 * 24)

            today = timezone.localdate()
            all_active_licenses = ClientLicense.objects.filter(is_active=True).exclude(machine_id="DEMO_MACHINE")
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

            from api.services.receipt_service import get_license_date_bounds
            start_date, last_allowed_month, grace_end = get_license_date_bounds(valid_time_license)

            if valid_time_license and valid_time_license.product_id in (2, 3):
                RESTRICTED_PREFIXES = [
                    '/api/v1/reports/',
                    '/api/v1/inventory-items/',
                    '/api/v1/purchase-invoices/',
                    '/api/v1/purchase-invoice-items/',
                    '/api/v1/expenses/',
                    '/api/v1/suppliers/',
                    '/api/v1/commission-histories/',
                    '/api/v1/inventory-adjustments/',
                ]
                if any(request.path.startswith(prefix) for prefix in RESTRICTED_PREFIXES):
                    return JsonResponse({
                        "error": "print_only_restricted",
                        "detail": "هذه الميزة غير متاحة في باقة الطباعة فقط."
                    }, status=403)

            is_expired = (not valid_time_license) or (grace_end and today > grace_end)
            if is_expired:
                if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                    return JsonResponse({
                        "error": "license_expired",
                        "message": "انتهى الاشتراك. التطبيق الآن في وضع القراءة فقط."
                    }, status=403)

            is_saving_receipt = (request.path.startswith('/api/v1/receipts/') and request.method == 'POST')
            if is_saving_receipt and total_invoices_balance <= 0 and valid_time_license:
                return JsonResponse({
                    "error": "license_expired",
                    "message": "Invoice balance exhausted. Please add invoice balance."
                }, status=403)

            return self.get_response(request)

        except Exception as e:
            print(f"License Middleware Error: {e}")
            if request.path.startswith('/api/'):
                return JsonResponse({"error": "server_error", "message": "An error occurred during license validation."}, status=500)
            return self.get_response(request)
