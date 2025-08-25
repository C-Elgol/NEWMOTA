from django.db import router
from django.urls import path

from mota_apps.finance.views.admin_dashboard_view import AdminDashboardView


app_name = 'finance'
urlpatterns = [
    path('admin-dashboard', AdminDashboardView.as_view(), name='admin-dashboard'),
]
