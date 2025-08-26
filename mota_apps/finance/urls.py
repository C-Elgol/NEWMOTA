from django.db import router
from django.urls import path

from mota_apps.finance.views.admin_dashboard_view import AdminDashboardView
from mota_apps.finance.views.season_selection_view import SeasonSelectionView


app_name = 'finance'
urlpatterns = [
    path('admin-dashboard', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('season-selection/', SeasonSelectionView.as_view(), name='season_selection'),

]
