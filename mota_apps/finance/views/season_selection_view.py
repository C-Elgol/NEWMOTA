from django.views.generic import TemplateView
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from mota_apps.finance.models import FinanceRecord
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SeasonSelectionView(TemplateView):
    """
    Handles season selection or creation via a modal interface.
    GET: Renders the season selection/creation form.
    POST: Processes AJAX requests to select or create a season, storing it in the session.
    """
    template_name = 'publics/dashboard/admin/pages/season_selection.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch distinct seasons from FinanceRecord
        seasons = FinanceRecord.objects.values('season_date').distinct()
        season_list = []
        for season in seasons:
            season_date = season['season_date']
            season_list.append({
                'year': season_date.year,
                'month': season_date.month,
                'display': season_date.strftime('%B %Y')
            })

        # Sort seasons by year and month (newest first)
        season_list.sort(key=lambda x: (x['year'], x['month']), reverse=True)

        # If no seasons exist, provide default options for current and next year
        if not season_list:
            current_year = timezone.now().year
            for year in [current_year, current_year + 1]:
                for month in range(1, 13):
                    season_list.append({
                        'year': year,
                        'month': month,
                        'display': datetime(year, month, 1).strftime('%B %Y')
                    })

        context['seasons'] = season_list
        return context

    def post(self, request):
        try:
            data = json.loads(request.body)
            action = data.get('action')
            year = int(data.get('year'))
            month = int(data.get('month'))

            # Validate year and month
            if not (1 <= month <= 12 and year >= 2000):
                return JsonResponse({'success': False, 'message': _('Invalid season selected')}, status=400)

            if action == 'create':
                season_date = datetime(year, month, 1).date()
                if FinanceRecord.objects.filter(season_date=season_date).exists():
                    return JsonResponse({'success': False, 'message': _('Season already exists')}, status=400)

            # Store selected season in session
            request.session['selected_season'] = {'year': year, 'month': month}

            return JsonResponse({
                'success': True,
                'message': _('Season selected successfully'),
                'redirect': reverse('finance:admin-dashboard')
            }, status=200)
        except Exception as e:
            logger.error(f"Season selection error: {str(e)}")
            return JsonResponse({'success': False, 'message': _('Failed to select or create season')}, status=500)