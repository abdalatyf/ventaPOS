from django.apps import AppConfig
import sys
import os

_sync_started = False  # Module-level flag to prevent duplicate starts

class SalesappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'salesapp'

    def ready(self):
        global _sync_started
        import salesapp.signals  # <--- أضف هذا السطر
        # الكود هنا بيتنفذ أول ما جانجو يشتغل
        
        # منع التكرار: في runserver، فقط شغّل في العملية الفرعية (RUN_MAIN)
        # في Waitress/الإنتاج، شغّل دائماً (RUN_MAIN لن يكون موجوداً)
        is_runserver = 'runserver' in sys.argv
        if is_runserver and os.environ.get('RUN_MAIN') != 'true':
            return  # Skip the reloader parent process

        if not _sync_started:
            _sync_started = True
            from .sync_agent import start_auto_sync
            
            # نشغل المزامنة الآلية
            start_auto_sync()
            print("Background Sync Started (Silent Mode)...")