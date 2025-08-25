from django.views.generic import TemplateView
import logging

logger = logging.getLogger(__name__)

class AdminDashboardView(TemplateView):
    template_name = "publics/dashboard/admin/pages/admin_dashboard.html"