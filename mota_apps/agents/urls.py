from django.urls import path
from mota_apps.agents.views.finance_agent_views import FinanceAgentView

app_name = 'agents'

urlpatterns = [
    path('finance-agent/', FinanceAgentView.as_view(), name='finance_agent'),
]