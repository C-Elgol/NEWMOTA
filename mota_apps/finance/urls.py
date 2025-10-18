from django.db import router
from django.urls import path

from mota_apps.finance.views.admin_dashboard_view import AdminDashboardView
from mota_apps.finance.views.expenditure_view import DeleteExpenditureView, ExpenditureDetailView, ExpenditureListView, NewExpenditureView, UpdateExpenditureView
from mota_apps.finance.views.interest_view import CollectInterestView, DeleteInterestView, GetMemberSavingsView, InterestListView, NewInterestView, UpdateInterestView
from mota_apps.finance.views.loan_view import DeleteLoanView, GetLoansView, LoanListView, NewLoanView, PayLoanView, UpdateLoanView
from mota_apps.finance.views.njangi_view import AddNjangiMemberView, DeleteNjangiView, GetNjangiDetailsView, GetNjangiView, NewNjangiView, NjangiListView, UpdateNjangiView
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
    path('loan-list/', LoanListView.as_view(), name='loan_list'),
    path('new-loan/', NewLoanView.as_view(), name='new_loan'),
    path('loan-update/<str:pk>/', UpdateLoanView.as_view(), name='loan_update'),
    path('loan-delete/<str:pk>/', DeleteLoanView.as_view(), name='loan_delete'),
    path('pay-loan/', PayLoanView.as_view(), name='pay_loan'),
    path('get-loans/<str:member_id>/', GetLoansView.as_view(), name='get_loans'),
    path('njangis/', NjangiListView.as_view(), name='njangi_list'),
    path('njangis/new/', NewNjangiView.as_view(), name='new_njangi'),
    path('njangis/update/<str:pk>/', UpdateNjangiView.as_view(), name='update_njangi'),
    path('njangis/add-member/', AddNjangiMemberView.as_view(), name='add_njangi_member'),
    path('njangis/delete/<str:pk>/', DeleteNjangiView.as_view(), name='delete_njangi'),
    path('njangis/get/<str:user_id>/', GetNjangiView.as_view(), name='get_njangis'),
    path('njangis/details/<str:pk>/', GetNjangiDetailsView.as_view(), name='get_njangi_details'),
    path('expenditures/', ExpenditureListView.as_view(), name='expenditure_list'),
    path('expenditures/new/', NewExpenditureView.as_view(), name='new_expenditure'),
    path('expenditures/update/<str:pk>/', UpdateExpenditureView.as_view(), name='update_expenditure'),
    path('expenditures/delete/<str:pk>/', DeleteExpenditureView.as_view(), name='delete_expenditure'),
    path('expenditures/detail/<str:pk>/', ExpenditureDetailView.as_view(), name='expenditure_detail'),
    
    # Interest URLs
    path('interest-list/', InterestListView.as_view(), name='interest_list'),
    path('new-interest/', NewInterestView.as_view(), name='new_interest'),
    path('interest/<str:pk>/update/', UpdateInterestView.as_view(), name='interest_update'),
    path('interest/<str:pk>/delete/', DeleteInterestView.as_view(), name='interest_delete'),
    path('get-member-savings/<str:member_id>/', GetMemberSavingsView.as_view(), name='get_member_savings'),
    path('collect-interest/', CollectInterestView.as_view(), name='collect_interest'),
]
