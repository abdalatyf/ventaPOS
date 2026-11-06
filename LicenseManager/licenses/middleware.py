import sys
import time

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
    and error logs directly to the cmd console window for LicenseManager.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
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
            safe_console_print(f"[BACKEND][ERROR] {request.method} {request.get_full_path()} -> {status} ({duration_ms}ms)")
        else:
            safe_console_print(f"[BACKEND] {request.method} {request.get_full_path()} -> {status} ({duration_ms}ms)")

        return response
