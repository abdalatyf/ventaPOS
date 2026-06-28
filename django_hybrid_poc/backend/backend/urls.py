from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.http import HttpResponse

def index_view(request):
    try:
        return TemplateView.as_view(template_name='index.html')(request)
    except Exception:
        return HttpResponse("Frontend build not found. Run the build script.", status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', index_view),
]
