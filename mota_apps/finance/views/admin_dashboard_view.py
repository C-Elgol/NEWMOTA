from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AdminDashboardView(TemplateView):
    template_name = "publics/dashboard/admin/pages/admin_dashboard.html"

    def get(self, request, *args, **kwargs):
        # Check authentication and permissions
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_admin or request.user.is_visitor):
            logger.info(f"Unauthorized access attempt to admin dashboard by user: {request.user}")
            return redirect('users:login')

        # Check if a season is selected
        selected_season = request.session.get('selected_season')
        if not selected_season:
            logger.info("No season selected, redirecting to season selection")
            return redirect('finance:season_selection')

        # Proceed to render the template with context
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        
        # This should never happen due to the get() method check, but included for safety
        if not selected_season:
            logger.warning("Unexpected: No season in session during get_context_data")
            return context

        year = selected_season['year']
        month = selected_season['month']
        season_date = datetime(year, month, 1)
        context['season'] = season_date.strftime('%B %Y')
        
        logger.debug(f"Rendering admin dashboard for season: {context['season']}, user: {self.request.user}")
        return context