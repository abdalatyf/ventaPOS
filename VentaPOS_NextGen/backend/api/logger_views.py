import os
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings

class FrontendLogView(APIView):
    """
    Receives batched console logs from the React frontend and appends them
    to a local file (frontend_console.log) in the project root.
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

        # Write to VentaPOS_NextGen/frontend_console.log
        log_file_path = os.path.join(settings.BASE_DIR.parent, 'frontend_console.log')
        
        try:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                for log_entry in logs:
                    level = str(log_entry.get('level', 'INFO')).upper()
                    message = log_entry.get('message', '')
                    timestamp = log_entry.get('timestamp', datetime.now().isoformat())
                    
                    f.write(f"[{timestamp}] [{level}] {message}\n")
            return Response({"status": "success"})
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)
