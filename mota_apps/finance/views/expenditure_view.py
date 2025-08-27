from django.views.generic import ListView, CreateView, UpdateView, TemplateView, View
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db.models import Max
from mota_apps.finance.models import Expenditure
from mota_apps.users.models import User
from mota_apps.finance.forms.expenditure_form import ExpenditureForm
from mota_apps.finance.views.record_finance_view import FinanceBaseView
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ExpenditureListView(FinanceBaseView, ListView):
    template_name = "publics/dashboard/admin/pages/expenditures/expenditure_list.html"
    model = Expenditure
    context_object_name = 'expenditures'
    paginate_by = 10

    def get_queryset(self):
        selected_season = self.request.session.get('selected_season')
        if not selected_season:
            logger.warning("No season selected in ExpenditureListView")
            return Expenditure.objects.none()
        year = selected_season['year']
        month = selected_season['month']
        season_date = datetime(year, month, 1)
        return Expenditure.objects.filter(
            season_date=season_date
        ).select_related('recorded_by').order_by('-created')

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

        latest_season = Expenditure.objects.aggregate(latest_date=Max('season_date'))['latest_date']
        context['is_current_season'] = (season_date.date() == latest_season) if latest_season else True
        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor
        logger.debug(f"Rendering expenditure list for season: {context['season']}, user: {self.request.user}")
        return context

class NewExpenditureView(FinanceBaseView, CreateView):
    template_name = "publics/dashboard/admin/pages/expenditures/includes/create_expenditure.html"
    form_class = ExpenditureForm
    success_url = reverse_lazy('finance:expenditure_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        season_date = datetime(selected_season['year'], selected_season['month'], 1)
        context['season'] = season_date.strftime('%B %Y')
        context['is_current_season'] = (season_date.date() == Expenditure.objects.aggregate(latest_date=Max('season_date'))['latest_date']) if Expenditure.objects.exists() else True
        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor
        logger.debug(f"Rendering create expenditure form for user {self.request.user.id}")
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
            if not selected_season:
                return JsonResponse({'success': False, 'message': _('No season selected.')}, status=400)

            year = selected_season['year']
            month = selected_season['month']
            season_date = datetime(year, month, 1)
            latest_season = Expenditure.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            is_current_season = (season_date.date() == latest_season) if latest_season else True

            if not (request.user.is_admin or (request.user.is_staff and is_current_season)):
                return JsonResponse({
                    'success': False,
                    'message': _('You do not have permission to record expenditures.')
                }, status=403)

            expenditure = form.save(commit=False)
            expenditure.season_date = season_date
            expenditure.recorded_by = request.user
            expenditure.save()

            logger.info(f'Expenditure created by user {request.user.id}: {expenditure.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(expenditure.id)},
                'message': _('Expenditure recorded successfully.'),
                'redirect': reverse_lazy('finance:expenditure_list')
            }, status=201)
        except Exception as e:
            logger.error(f'Unexpected error during expenditure creation: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while creating the expenditure. Please try again.')
            }, status=500)

class UpdateExpenditureView(FinanceBaseView, UpdateView):
    template_name = "publics/dashboard/admin/pages/expenditures/includes/update_expenditure.html"
    model = Expenditure
    form_class = ExpenditureForm
    success_url = reverse_lazy('finance:expenditure_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        season_date = datetime(selected_season['year'], selected_season['month'], 1)
        context['season'] = season_date.strftime('%B %Y')
        context['is_current_season'] = (season_date.date() == Expenditure.objects.aggregate(latest_date=Max('season_date'))['latest_date']) if Expenditure.objects.exists() else True
        context['is_admin'] = self.request.user.is_admin
        logger.debug(f"Rendering update expenditure form for user {self.request.user.id}, Expenditure ID {self.kwargs['pk']}")
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
            selected_season = request.session.get('selected_season')
            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            latest_season = Expenditure.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            is_current_season = (season_date.date() == latest_season) if latest_season else True

            if not request.user.is_admin and not is_current_season:
                return JsonResponse({
                    'success': False,
                    'message': _('Only admins can modify previous season data.')
                }, status=403)

            expenditure = form.save(commit=False)
            expenditure.recorded_by = request.user
            expenditure.save()

            logger.info(f'Expenditure updated by user {request.user.id}: {expenditure.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(expenditure.id)},
                'message': _('Expenditure updated successfully.'),
                'redirect': reverse_lazy('finance:expenditure_list')
            }, status=200)
        except Exception as e:
            logger.error(f'Unexpected error during expenditure update: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while updating the expenditure. Please try again.')
            }, status=500)

class DeleteExpenditureView(FinanceBaseView, View):
    def post(self, request, *args, **kwargs):
        try:
            expenditure = Expenditure.objects.get(pk=kwargs['pk'])
            selected_season = request.session.get('selected_season')
            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            latest_season = Expenditure.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            is_current_season = (season_date.date() == latest_season) if latest_season else True

            if not (request.user.is_admin or (request.user.is_staff and is_current_season)):
                logger.warning(f"Unauthorized delete attempt by user {request.user.id} on expenditure {kwargs['pk']}")
                return JsonResponse({
                    'success': False,
                    'message': _('You do not have permission to delete this expenditure.')
                }, status=403)

            expenditure_id = expenditure.id
            expenditure.delete()
            logger.info(f'Expenditure {expenditure_id} deleted by user {request.user.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(expenditure_id)},
                'message': _('Expenditure deleted successfully.')
            }, status=200)
        except Expenditure.DoesNotExist:
            logger.warning(f"Expenditure {kwargs['pk']} not found for deletion by user {request.user.id}")
            return JsonResponse({
                'success': False,
                'message': _('Expenditure not found.')
            }, status=404)
        except Exception as e:
            logger.error(f'Unexpected error during expenditure deletion: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while deleting the expenditure. Please try again.')
            }, status=500)

class ExpenditureDetailView(FinanceBaseView, View):
    def get(self, request, *args, **kwargs):
        try:
            expenditure = Expenditure.objects.get(pk=kwargs['pk'])
            data = {
                'id': str(expenditure.id),
                'entertainment_spent': float(expenditure.entertainment_spent),
                'other_expenditures': float(expenditure.other_expenditures),
                'comment': expenditure.comment,
                'recorded_by': expenditure.recorded_by.get_full_name if expenditure.recorded_by else 'N/A',
                'recorded_at': expenditure.created.strftime('%Y-%m-%d %H:%M:%S'),
                'season_date': expenditure.season_date.strftime('%B %Y')
            }
            logger.info(f'Expenditure details fetched by user {request.user.id}: {expenditure.id}')
            return JsonResponse({'success': True, 'data': data}, status=200)
        except Expenditure.DoesNotExist:
            logger.warning(f"Expenditure {kwargs['pk']} not found for user {request.user.id}")
            return JsonResponse({'success': False, 'message': _('Expenditure not found.')}, status=404)
        except Exception as e:
            logger.error(f'Unexpected error fetching expenditure details: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while fetching expenditure details.')
            }, status=500)