from django.views.generic import ListView, CreateView, UpdateView, View
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Max
from mota_apps.finance.models import FinanceRecord
from mota_apps.users.models import User
from mota_apps.finance.forms.forms import FinanceRecordForm
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FinanceBaseView:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_admin or request.user.is_visitor):
            logger.warning(f"Unauthorized access attempt by user {request.user.id}")
            return JsonResponse({
                'success': False,
                'message': _('You do not have permission to access this page.')
            }, status=403)
        selected_season = request.session.get('selected_season')
        if not selected_season:
            logger.info("No season selected, redirecting to season selection")
            return JsonResponse({
                'success': False,
                'message': _('No season selected.'),
                'redirect': reverse_lazy('finance:season_selection')
            }, status=400)
        return super().dispatch(request, *args, **kwargs)

class FinanceListView(FinanceBaseView, ListView):
    template_name = "publics/dashboard/admin/pages/finance/finance_list.html"
    model = FinanceRecord
    context_object_name = 'finance_records'
    paginate_by = 100

    def get_queryset(self):
        selected_season = self.request.session.get('selected_season')
        if not selected_season:
            return FinanceRecord.objects.none()
        year = selected_season['year']
        month = selected_season['month']
        season_date = datetime(year, month, 1)
        return FinanceRecord.objects.filter(
            season_date=season_date
        ).select_related('member').order_by('id')

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

        # Determine if current season
        latest_season = FinanceRecord.objects.aggregate(latest_date=Max('season_date'))['latest_date']
        context['is_current_season'] = (season_date.date() == latest_season) if latest_season else True

        # Get members without finance records for the season
        members_with_records = FinanceRecord.objects.filter(
            season_date=season_date
        ).values_list('member_id', flat=True)
        context['members'] = User.objects.filter(
            is_active=True,
            is_deleted=False
        ).exclude(id__in=members_with_records)

        # Aggregates for summary
        aggregates = FinanceRecord.objects.filter(
            season_date=season_date
        ).aggregate(
            total_savings=Sum('savings'),
            total_entertainment=Sum('entertainment_fees'),
            total_njangi=Sum('njangi'),
            total_project=Sum('project'),
            total_others=Sum('others')
        )
        context['total_savings'] = aggregates['total_savings'] or 0.00
        context['total_entertainment'] = aggregates['total_entertainment'] or 0.00
        context['total_njangi'] = aggregates['total_njangi'] or 0.00
        context['total_project'] = aggregates['total_project'] or 0.00
        context['total_others'] = aggregates['total_others'] or 0.00

        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor

        logger.debug(f"Rendering finance list for season: {context['season']}, user: {self.request.user}")
        return context

class NewFinanceView(FinanceBaseView, CreateView):
    template_name = "publics/dashboard/admin/pages/finance/includes/create_finance.html"
    form_class = FinanceRecordForm
    success_url = reverse_lazy('finance:finance_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        season_date = datetime(selected_season['year'], selected_season['month'], 1)
        context['season'] = season_date.strftime('%B %Y')
        # Get members without finance records for the season
        members_with_records = FinanceRecord.objects.filter(
            season_date=season_date
        ).values_list('member_id', flat=True)
        context['members'] = User.objects.filter(
            is_active=True,
            is_deleted=False
        ).exclude(id__in=members_with_records)
        logger.debug(f"Rendering create finance form for user {self.request.user.id}")
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if not form.is_valid():
            logger.warning(f'Invalid form submission by user {request.user.id}: {form.errors}')
            return JsonResponse({
                'success': False,
                'message': _('Please fill in all required fields correctly.'),
                'errors': form.errors.as_json()
            }, status=400)

        try:
            selected_season = request.session.get('selected_season')
            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            finance_record = form.save(commit=False)
            finance_record.season_date = season_date
            finance_record.recorded_by = request.user
            finance_record.save()

            logger.info(f'Finance record created by user {request.user.id}: {finance_record.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(finance_record.id)},
                'message': _('Finance record created successfully.'),
                'redirect': reverse_lazy('finance:finance_list')
            }, status=201)
        except Exception as e:
            logger.error(f'Unexpected error during finance creation: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while creating the finance record. Please try again.')
            }, status=500)

class UpdateFinanceView(FinanceBaseView, UpdateView):
    template_name = "publics/dashboard/admin/pages/finance/includes/update_finance.html"
    model = FinanceRecord
    form_class = FinanceRecordForm
    success_url = reverse_lazy('finance:finance_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        season_date = datetime(selected_season['year'], selected_season['month'], 1)
        context['season'] = season_date.strftime('%B %Y')
        context['members'] = User.objects.filter(is_active=True, is_deleted=False)
        context['is_current_season'] = (season_date.date() == FinanceRecord.objects.aggregate(latest_date=Max('season_date'))['latest_date']) if FinanceRecord.objects.exists() else True
        context['is_admin'] = self.request.user.is_admin
        logger.debug(f"Rendering update finance form for user {self.request.user.id}, Finance ID {self.kwargs['pk']}")
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(request.POST, instance=self.object)
        if not form.is_valid():
            logger.warning(f'Invalid form submission by user {request.user.id}: {form.errors}')
            return JsonResponse({
                'success': False,
                'message': _('Please fill in all required fields correctly.'),
                'errors': form.errors.as_json()
            }, status=400)

        try:
            finance_record = form.save(commit=False)
            finance_record.recorded_by = request.user
            finance_record.save()

            logger.info(f'Finance record updated by user {request.user.id}: {finance_record.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(finance_record.id)},
                'message': _('Finance record updated successfully.'),
                'redirect': reverse_lazy('finance:finance_list')
            }, status=200)
        except Exception as e:
            logger.error(f'Unexpected error during finance update: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while updating the finance record. Please try again.')
            }, status=500)

class DeleteFinanceView(FinanceBaseView, View):
    def post(self, request, *args, **kwargs):
        try:
            finance_record = FinanceRecord.objects.get(pk=kwargs['pk'])
            if not (request.user.is_admin or (request.user.is_staff and FinanceRecord.objects.filter(pk=kwargs['pk']).aggregate(latest_date=Max('season_date'))['latest_date'] == finance_record.season_date)):
                logger.warning(f"Unauthorized delete attempt by user {request.user.id} on finance record {kwargs['pk']}")
                return JsonResponse({
                    'success': False,
                    'message': _('You do not have permission to delete this finance record.')
                }, status=403)

            finance_id = finance_record.id
            finance_record.delete()
            logger.info(f'Finance record {finance_id} deleted by user {request.user.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(finance_id)},
                'message': _('Finance record deleted successfully.')
            }, status=200)
        except FinanceRecord.DoesNotExist:
            logger.warning(f"Finance record {kwargs['pk']} not found for deletion by user {request.user.id}")
            return JsonResponse({
                'success': False,
                'message': _('Finance record not found.')
            }, status=404)
        except Exception as e:
            logger.error(f'Unexpected error during finance deletion: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while deleting the finance record. Please try again.')
            }, status=500)