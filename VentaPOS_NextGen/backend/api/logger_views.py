import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings

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

def get_frontend_logger():
    logger = logging.getLogger('frontend_console')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        log_dir = Path(settings.DB_DIR) / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'frontend_console.log'
        handler = RotatingFileHandler(
            str(log_file),
            maxBytes=5 * 1024 * 1024,
            backupCount=2,
            encoding='utf-8'
        )
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        logger.propagate = False
    return logger

class FrontendLogView(APIView):
    """
    Receives batched console logs from the React frontend and appends them
    to a rotating log file in settings.DB_DIR / 'logs' / 'frontend_console.log'.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data
        if not data:
            return Response({"status": "error", "message": "No data provided"}, status=400)
            
        logs = data.get('logs', [])
        if not isinstance(logs, list):
            # Fallback for single log object
            logs = [data]

        try:
            logger = get_frontend_logger()
            for log_entry in logs:
                if not isinstance(log_entry, dict):
                    continue
                level = str(log_entry.get('level', 'INFO')).upper()
                message = str(log_entry.get('message', ''))
                details = log_entry.get('details', '')
                url = log_entry.get('url', '')
                timestamp = log_entry.get('timestamp', datetime.now().isoformat())

                # Format for file logger
                details_file = f" | {details}" if details else ""
                url_file = f" [{url}]" if url else ""
                logger.info(f"[{timestamp}] [{level}]{url_file} {message}{details_file}")

                # Stream live to stdout/cmd console
                details_cli = f" | {details}" if details else ""
                url_cli = f" [{url}]" if url else ""
                safe_console_print(f"[FRONTEND][{level}]{url_cli} {message}{details_cli}")

            return Response({"status": "success"})
        except Exception as e:
            safe_console_print(f"[FRONTEND][LOGGER_ERROR] Failed to process logs: {e}")
            return Response({"status": "error", "message": str(e)}, status=500)
