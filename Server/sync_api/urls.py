from django.urls import path
from .views import SyncIngestView, MobilePushIngestView, PendingReceiptsView, ConfirmReceiptsView, UploadSetupView, DownloadSetupView, ViewerAuthView, ViewerDownloadSyncView, MobileAuthView, PullSyncView, RegisterOnlineLicenseView, ManagerDashboardView, AdminSyncPushView

urlpatterns = [
    # الرابط سيكون: /api/v1/sync/push/
    path('api/v1/sync/push/', SyncIngestView.as_view(), name='sync_push'),
    path('api/v1/sync/register-online-license/', RegisterOnlineLicenseView.as_view(), name='register_online_license'),
    path('api/v1/sync/mobile-push/', MobilePushIngestView.as_view(), name='sync_mobile_push'),
    path('api/v1/sync/pending-receipts/', PendingReceiptsView.as_view(), name='sync_pending_receipts'),
    path('api/v1/sync/confirm-receipts/', ConfirmReceiptsView.as_view(), name='sync_confirm_receipts'),
    path('api/v1/sync/admin-push/', AdminSyncPushView.as_view(), name='sync_admin_push'),
    
    # Remote Provisioning APIs
    path('api/v1/sync/upload-setup/', UploadSetupView.as_view(), name='sync_upload_setup'),
    path('api/v1/sync/download-setup/', DownloadSetupView.as_view(), name='sync_download_setup'),
    
    # Viewer PC Authentication & Sync
    path('api/v1/auth/viewer/', ViewerAuthView.as_view(), name='viewer_auth'),
    path('api/v1/sync/viewer/download/', ViewerDownloadSyncView.as_view(), name='viewer_sync_download'),
    
    # Mobile Authentication API
    path('api/v1/auth/mobile/', MobileAuthView.as_view(), name='mobile_auth'),
    path('api/v1/sync/pull/', PullSyncView.as_view(), name='sync_pull'),
    path('api/v1/sync/manager-dashboard/', ManagerDashboardView.as_view(), name='manager_dashboard'),
]