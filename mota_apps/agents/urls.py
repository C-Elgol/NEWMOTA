from django.urls import path
from mota_apps.agents.views.finance_agent_views import FinanceAgentView
# from mota_apps.agents.views.loan_notification_views import LoanNotificationView

app_name = 'agents'

urlpatterns = [
    path('finance-agent/', FinanceAgentView.as_view(), name='finance_agent'),
    # path('loan-notification/', LoanNotificationView.as_view(), name='loan_notification'),
]