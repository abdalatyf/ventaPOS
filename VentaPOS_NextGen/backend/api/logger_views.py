import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings

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
                level = str(log_entry.get('level', 'INFO')).upper()
                message = log_entry.get('message', '')
                timestamp = log_entry.get('timestamp', datetime.now().isoformat())
                logger.info(f"[{timestamp}] [{level}] {message}")
            return Response({"status": "success"})
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)
