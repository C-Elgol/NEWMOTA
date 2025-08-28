from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.utils import timezone
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from decimal import Decimal
from mota_apps.users.models import User
from mota_apps.finance.models import FinanceRecord, Expenditure, Njangi, Loan, ProjectRecord
from django.db.models import Sum, Max
import logging

logger = logging.getLogger(__name__)

class AdminDashboardView(TemplateView):
    template_name = "publics/dashboard/admin/pages/admin_dashboard.html"

    def get(self, request, *args, **kwargs):
        # Check authentication and permissions
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_admin or request.user.is_visitor):
            logger.info(f"Unauthorized access attempt to admin dashboard by user: {request.user}")
            return JsonResponse({'success': False, 'message': _('Unauthorized')}, status=403)

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
        
        if not selected_season:
            logger.warning("Unexpected: No season in session during get_context_data")
            return context

        year = selected_season['year']
        month = selected_season['month']
        season_date = datetime(year, month, 1)
        context['season'] = season_date.strftime('%B %Y')

        # Determine if it's the current season
        latest_season = FinanceRecord.objects.aggregate(latest_date=Max('season_date'))['latest_date']
        context['is_current_season'] = (season_date.date() == latest_season) if latest_season else True

        # Stats card calculations
        context['total_revenue'] = FinanceRecord.objects.filter(
            season_date__year=year,
            season_date__month=month
        ).aggregate(total=Sum('net_income'))['total'] or Decimal('0.00')

        context['total_users'] = User.objects.filter(is_active=True, is_deleted=False).count()

        aggregates = FinanceRecord.objects.filter(
            season_date__year=year,
            season_date__month=month
        ).aggregate(
            total_savings=Sum('savings'),
            total_entertainment=Sum('entertainment_fees'),
            total_njangi=Sum('njangi'),
            total_projects=Sum('project'),
            total_others=Sum('others')
        )

        context['total_savings'] = aggregates['total_savings'] or Decimal('0.00')
        context['total_entertainment'] = aggregates['total_entertainment'] or Decimal('0.00')
        context['total_njangi'] = aggregates['total_njangi'] or Decimal('0.00')
        context['total_projects'] = aggregates['total_projects'] or Decimal('0.00')
        context['total_others'] = aggregates['total_others'] or Decimal('0.00')

        # Total finance (sum of all contributions)
        context['total_finance'] = (
            context['total_savings'] +
            context['total_entertainment'] +
            context['total_njangi'] +
            context['total_projects'] +
            context['total_others']
        )

        # Previous season net income
        previous_season = FinanceRecord.objects.filter(
            season_date__lt=season_date
        ).aggregate(previous_date=Max('season_date'))['previous_date']
        
        context['previous_season_net_income'] = Decimal('0.00')
        if previous_season:
            previous_record = FinanceRecord.objects.filter(
                season_date=previous_season
            ).first()
            if previous_record:
                context['previous_season_net_income'] = previous_record.net_income

        # Outcome calculations
        context['total_entertainment_spent'] = Expenditure.objects.filter(
            season_date__year=year,
            season_date__month=month
        ).aggregate(total=Sum('entertainment_spent'))['total'] or Decimal('0.00')
        
        context['total_other_expenditures'] = Expenditure.objects.filter(
            season_date__year=year,
            season_date__month=month
        ).aggregate(total=Sum('other_expenditures'))['total'] or Decimal('0.00')
        
        context['total_njangi_benefited'] = Njangi.objects.filter(
            season_date=season_date,
            amount__gt=0
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        context['total_loan_out'] = Loan.objects.filter(
            season_date__year=year,
            season_date__month=month
        ).aggregate(total=Sum('amount_borrowed'))['total'] or Decimal('0.00')

        # Income summary data for table
        context['income_summary'] = [
            {'category': _('Amount from the previous season'), 'total': context['previous_season_net_income']},
            {'category': _('Savings'), 'total': context['total_savings']},
            {'category': _('Entertainment'), 'total': context['total_entertainment']},
            {'category': _('Njangi'), 'total': context['total_njangi']},
            {'category': _('Project'), 'total': context['total_projects']},
            {'category': _('Other'), 'total': context['total_others']},
            {
                'category': _('Total Income'),
                'total': (
                    context['total_savings'] +
                    context['total_entertainment'] +
                    context['total_njangi'] +
                    context['total_projects'] +
                    context['total_others'] +
                    context['previous_season_net_income']
                )
            }
        ]

        # Outcome summary data for table
        context['outcome_summary'] = [
            {'category': _('Entertainment Spent'), 'total': context['total_entertainment_spent']},
            {'category': _('Other Expenditures'), 'total': context['total_other_expenditures']},
            {'category': _('Njangi Benefited'), 'total': context['total_njangi_benefited']},
            {'category': _('Loan Out'), 'total': context['total_loan_out']},
            {
                'category': _('Total Outcome'),
                'total': (
                    context['total_entertainment_spent'] +
                    context['total_other_expenditures'] +
                    context['total_njangi_benefited'] +
                    context['total_loan_out']
                )
            }
        ]

        # Net income calculation
        total_income = context['income_summary'][-1]['total']
        total_outcome = context['outcome_summary'][-1]['total']
        context['net_income'] = total_income - total_outcome

        # Update net_income in FinanceRecord
        FinanceRecord.objects.filter(
            season_date__year=year,
            season_date__month=month
        ).update(net_income=context['net_income'])

        # User permissions
        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor

        logger.debug(f"Rendering admin dashboard for season: {context['season']}, user: {self.request.user}, "
                     f"is_staff={context['is_staff']}, is_admin={context['is_admin']}, "
                     f"is_visitor={context['is_visitor']}, is_current_season={context['is_current_season']}")
        return context