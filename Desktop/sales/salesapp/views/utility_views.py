# salesapp/views/utility_views.py
# الأدوات المساعدة (Utility Views)

import os
import signal
from django.http import HttpResponse


def exit_app(request):
    """أمر بإنهاء البرنامج بالكامل"""
    os.kill(os.getpid(), signal.SIGTERM)
    return HttpResponse("Closing...")
