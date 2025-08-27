from django.db import router
from django.urls import path

from mota_apps.finance.views.admin_dashboard_view import AdminDashboardView
from mota_apps.finance.views.record_finance_view import DeleteFinanceView, FinanceListView, NewFinanceView, UpdateFinanceView
from mota_apps.finance.views.season_selection_view import SeasonSelectionView


app_name = 'finance'
urlpatterns = [
    path('admin-dashboard', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('season-selection/', SeasonSelectionView.as_view(), name='season_selection'),
    path('finance-list/', FinanceListView.as_view(), name='finance_list'),
    path('new-finance/', NewFinanceView.as_view(), name='new_finance'),
    path('finance-update/<str:pk>/', UpdateFinanceView.as_view(), name='finance_update'),
    path('finance-delete/<str:pk>/', DeleteFinanceView.as_view(), name='finance_delete'),
]
