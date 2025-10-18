from django.views.generic import ListView, CreateView, UpdateView, View
from django.http import JsonResponse, Http404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db.models import Max, Sum
from mota_apps.finance.models import ProjectRecord
from mota_apps.users.models import User
from mota_apps.finance.forms.project_form import ProjectForm
from mota_apps.finance.views.record_finance_view import FinanceBaseView
from datetime import datetime
import logging
from decimal import Decimal
import json
import uuid

logger = logging.getLogger(__name__)

class ProjectListView(FinanceBaseView, ListView):
    template_name = "publics/dashboard/admin/pages/project/project_list.html"
    model = ProjectRecord
    context_object_name = 'projects'
    paginate_by = 100

    def get_queryset(self):
        selected_season = self.request.session.get('selected_season')
        if not selected_season or selected_season['month'] == 6:
            return ProjectRecord.objects.none()
        year = selected_season['year']
        month = selected_season['month']
        season_date = datetime(year, month, 1)
        return ProjectRecord.objects.filter(
            season_date=season_date
        ).select_related('recorded_by').order_by('-date_collected')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        
        if not selected_season or selected_season['month'] == 6:
            logger.warning("No season or June selected")
            context['season'] = 'N/A'
            context['total_amount_collected'] = Decimal('0.00')
            context['total_interest_collected'] = Decimal('0.00')
            context['projects'] = []
            return context

        year = selected_season['year']
        month = selected_season['month']
        season_date = datetime(year, month, 1)
        context['season'] = season_date.strftime('%B %Y')

        # Determine if current season
        latest_season = ProjectRecord.objects.aggregate(latest_date=Max('season_date'))['latest_date']
        context['is_current_season'] = (season_date.date() == latest_season) if latest_season else True

        # Calculate totals
        totals = ProjectRecord.objects.filter(
            season_date=season_date
        ).aggregate(
            total_amount=Sum('amount_collected'),
            total_interest=Sum('interest_collected')
        )
        context['total_amount_collected'] = totals['total_amount'] or Decimal('0.00')
        context['total_interest_collected'] = totals['total_interest'] or Decimal('0.00')

        # Prepare project records with signature
        projects = []
        for project in self.get_queryset():
            projects.append({
                'project': project,
                'signature': project.signature or ''
            })
        context['projects'] = projects

        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor

        logger.debug(f"Rendering project list for season: {context['season']}, user: {self.request.user}")
        return context

class NewProjectView(FinanceBaseView, CreateView):
    template_name = "publics/dashboard/admin/pages/project/includes/create_project.html"
    form_class = ProjectForm
    success_url = reverse_lazy('finance:project_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        if not selected_season or selected_season['month'] == 6:
            logger.warning("No season or June selected")
            context['season'] = 'N/A'
            context['total_amount_collected'] = Decimal('0.00')
            context['total_interest_collected'] = Decimal('0.00')
            return context

        season_date = datetime(selected_season['year'], selected_season['month'], 1)
        context['season'] = season_date.strftime('%B %Y')
        
        # Calculate totals
        totals = ProjectRecord.objects.filter(
            season_date=season_date
        ).aggregate(
            total_amount=Sum('amount_collected'),
            total_interest=Sum('interest_collected')
        )
        context['total_amount_collected'] = totals['total_amount'] or Decimal('0.00')
        context['total_interest_collected'] = totals['total_interest'] or Decimal('0.00')
        
        logger.debug(f"Rendering create project form for user {self.request.user.id}")
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
            if selected_season['month'] == 6:
                return JsonResponse({
                    'success': False,
                    'message': _('Project records cannot be created for June.')
                }, status=400)

            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            project = form.save(commit=False)
            project.season_date = season_date
            project.recorded_by = self.request.user
            project.save()

            logger.info(f'Project created by user {request.user.id}: {project.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(project.id)},
                'message': _('Project record created successfully.'),
                'redirect': reverse_lazy('finance:project_list')
            }, status=201)
        except Exception as e:
            logger.error(f'Unexpected error during project creation: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while creating the project record. Please try again.')
            }, status=500)

class UpdateProjectView(FinanceBaseView, UpdateView):
    template_name = "publics/dashboard/admin/pages/project/includes/update_project.html"
    model = ProjectRecord
    form_class = ProjectForm
    success_url = reverse_lazy('finance:project_list')

    def get_object(self, queryset=None):
        try:
            return ProjectRecord.objects.get(id=self.kwargs['pk'])
        except ProjectRecord.DoesNotExist:
            logger.warning(f"Project {self.kwargs['pk']} not found for update by user {self.request.user.id}")
            raise Http404(_('Project record not found.'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        if not selected_season or selected_season['month'] == 6:
            logger.warning("No season or June selected")
            context['season'] = 'N/A'
            context['total_amount_collected'] = Decimal('0.00')
            context['total_interest_collected'] = Decimal('0.00')
            return context

        season_date = datetime(selected_season['year'], selected_season['month'], 1)
        context['season'] = season_date.strftime('%B %Y')
        context['is_admin'] = self.request.user.is_admin

        latest_season = ProjectRecord.objects.aggregate(latest_date=Max('season_date'))['latest_date']
        context['is_current_season'] = (
            season_date.date() == latest_season
        ) if latest_season else True

        # Calculate totals
        totals = ProjectRecord.objects.filter(
            season_date=season_date
        ).aggregate(
            total_amount=Sum('amount_collected'),
            total_interest=Sum('interest_collected')
        )
        context['total_amount_collected'] = totals['total_amount'] or Decimal('0.00')
        context['total_interest_collected'] = totals['total_interest'] or Decimal('0.00')

        logger.debug(f"Rendering update project form for user {self.request.user.id}, Project ID {self.kwargs['pk']}")
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
            if selected_season['month'] == 6:
                return JsonResponse({
                    'success': False,
                    'message': _('Project records cannot be updated for June.')
                }, status=400)

            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            latest_season = ProjectRecord.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            is_current_season = (season_date.date() == latest_season) if latest_season else True

            if not request.user.is_admin and not is_current_season:
                return JsonResponse({
                    'success': False,
                    'message': _('Only admins can modify previous season data.')
                }, status=403)

            project = form.save(commit=False)
            project.recorded_by = self.request.user
            project.save()

            logger.info(f'Project updated by user {request.user.id}: {project.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(project.id)},
                'message': _('Project record updated successfully.'),
                'redirect': reverse_lazy('finance:project_list')
            }, status=200)
        except Exception as e:
            logger.error(f'Unexpected error during project update: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while updating the project record. Please try again.')
            }, status=500)

class DeleteProjectView(FinanceBaseView, View):
    def post(self, request, *args, **kwargs):
        try:
            project = ProjectRecord.objects.get(id=self.kwargs['pk'])
            selected_season = request.session.get('selected_season')
            if selected_season['month'] == 6:
                return JsonResponse({
                    'success': False,
                    'message': _('Project records cannot be deleted for June.')
                }, status=400)

            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            latest_season = ProjectRecord.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            is_current_season = (season_date.date() == latest_season) if latest_season else True

            if not (request.user.is_admin or (request.user.is_staff and is_current_season)):
                logger.warning(f"Unauthorized delete attempt by user {request.user.id} on project {self.kwargs['pk']}")
                return JsonResponse({
                    'success': False,
                    'message': _('You do not have permission to delete this project record.')
                }, status=403)

            project_id = str(project.id)
            project.delete()
            logger.info(f'Project {project_id} deleted by user {request.user.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': project_id},
                'message': _('Project record deleted successfully.')
            }, status=200)
        except ProjectRecord.DoesNotExist:
            logger.warning(f"Project {self.kwargs['pk']} not found for deletion by user {self.request.user.id}")
            return JsonResponse({
                'success': False,
                'message': _('Project record not found.')
            }, status=404)
        except Exception as e:
            logger.error(f'Unexpected error during project deletion: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while deleting the project record. Please try again.')
            }, status=500)

class CollectProjectView(FinanceBaseView, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            project_id = data.get('project_id')
            amount_collected = Decimal(data.get('amount_collected'))
            interest_collected = Decimal(data.get('interest_collected', '0.00'))
            signature = data.get('signature')

            if not (project_id and amount_collected and signature):
                return JsonResponse({
                    'success': False,
                    'message': _('Missing required fields.')
                }, status=400)

            try:
                uuid.UUID(project_id)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': _('Invalid project ID format.')
                }, status=400)

            selected_season = request.session.get('selected_season')
            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            if season_date.month == 6:
                return JsonResponse({
                    'success': False,
                    'message': _('Collections not allowed for June.')
                }, status=400)

            project = ProjectRecord.objects.get(id=project_id)
            project.amount_collected += amount_collected
            project.interest_collected += interest_collected
            project.signature = signature
            project.recorded_by = self.request.user
            project.save()

            logger.info(f'Collection recorded for project {project_id} by user {request.user.id}')
            return JsonResponse({
                'success': True,
                'message': _('Collection recorded successfully.')
            }, status=200)
        except ProjectRecord.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('Project record not found.')
            }, status=404)
        except Exception as e:
            logger.error(f'Error recording collection: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An error occurred while recording the collection.')
            }, status=500)