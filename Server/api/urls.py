from django.urls import path
from .views import BranchViewSet, SalespersonViewSet, DefaultDateView

urlpatterns = [
    # Default Date (used by frontend dashboard)
    path('default-date/', DefaultDateView.as_view(), name='default-date'),

    # Branches
    path('branches/', BranchViewSet.as_view(), name='branch-list-create'),
    path('branches/<int:pk>/', BranchViewSet.as_view(), name='branch-detail'),

    # Salespeople
    path('salespeople/', SalespersonViewSet.as_view(), name='salesperson-list-create'),
    path('salespeople/<int:pk>/', SalespersonViewSet.as_view(), name='salesperson-detail'),
]
