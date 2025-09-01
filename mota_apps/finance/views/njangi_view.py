from django.views.generic import ListView, CreateView, UpdateView, View, FormView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db.models import Max, Exists, OuterRef
from mota_apps.finance.models import Njangi
from mota_apps.finance.views.record_finance_view import FinanceBaseView
from mota_apps.users.models import User
from mota_apps.finance.forms.njangi_form import NjangiForm, NjangiMemberForm
from datetime import datetime
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class NjangiListView(FinanceBaseView, ListView):
    template_name = "publics/dashboard/admin/pages/njangis/njangi_list.html"
    model = Njangi
    context_object_name = 'njangis'
    paginate_by = 100

    def get_queryset(self):
        selected_season = self.request.session.get('selected_season')
        if not selected_season:
            return Njangi.objects.none()
        year = selected_season['year']
        month = selected_season['month']
        season_date = datetime(year, month, 1)
        return Njangi.objects.filter(
            season_date=season_date,
            amount__gt=0  # Only benefited members
        ).select_related('user').order_by('id')

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

        latest_season = Njangi.objects.aggregate(latest_date=Max('season_date'))['latest_date']
        context['is_current_season'] = (season_date.date() == latest_season) if latest_season else True

        benefited_subquery = Njangi.objects.filter(
            season_date=season_date,
            user=OuterRef('pk'),
            amount__gt=0
        )
        context['members'] = User.objects.filter(
            is_active=True,
            is_deleted=False,
            njangi_records__season_date=season_date,
            njangi_records__amount=0
        ).exclude(Exists(benefited_subquery)).distinct()

        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor

        logger.debug(f"Rendering njangi list for season: {context['season']}, user: {self.request.user}")
        return context

class NewNjangiView(FinanceBaseView, CreateView):
    template_name = "publics/dashboard/admin/pages/njangis/includes/create_njangi.html"
    form_class = NjangiForm
    success_url = reverse_lazy('finance:njangi_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        selected_season = self.request.session.get('selected_season')
        if selected_season:
            kwargs['season_date'] = datetime(selected_season['year'], selected_season['month'], 1)
        logger.debug(f"Form kwargs: {kwargs}")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        if not selected_season:
            logger.warning("No season in session during get_context_data")
        else:
            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            context['season'] = season_date.strftime('%B %Y')
            # add is_current_season
            latest_season = Njangi.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            context['is_current_season'] = (season_date.date() == latest_season) if latest_season else True
        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor
        logger.debug(f"Rendering create njangi form for user {self.request.user.id}")
        return context


    def post(self, request, *args, **kwargs):
        logger.info(f"POST request received for new njangi by user {request.user.id}")
        selected_season = request.session.get('selected_season')
        if not selected_season:
            logger.error("No season selected in session")
            return JsonResponse({'success': False, 'message': _('No season selected.')}, status=400)

        season_date = datetime(selected_season['year'], selected_season['month'], 1)
        logger.debug(f"Processing njangi for season: {season_date}")
        form = self.form_class(request.POST, season_date=season_date)
        logger.debug(f"Form data: {request.POST}")
        if not form.is_valid():
            logger.warning(f'Invalid form submission by user {request.user.id}: {form.errors}')
            return JsonResponse({
                'success': False,
                'message': _('Please fill in all required fields correctly.'),
                'errors': form.errors.as_json()
            }, status=400)

        try:
            latest_season = Njangi.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            is_current_season = (season_date.date() == latest_season) if latest_season else True
            logger.debug(f"Current season check: {is_current_season}")

            if not request.user.is_admin and not is_current_season:
                logger.warning(f"Unauthorized attempt to create njangi by user {request.user.id} for past season")
                return JsonResponse({
                    'success': False,
                    'message': _('Only admins can modify previous season data.')
                }, status=403)

            njangi = form.save(commit=False)
            logger.debug(f"Form cleaned data: {form.cleaned_data}")
            existing_njangi = Njangi.objects.filter(
                user=njangi.user,
                season_date=season_date,
                amount=0
            ).first()
            if not existing_njangi:
                logger.error(f"No non-benefited Njangi record found for user {njangi.user.id} in season {season_date}")
                return JsonResponse({
                    'success': False,
                    'message': _('Selected member is not a non-benefited Njangi member for this season.')
                }, status=400)

            existing_njangi.member_id_number = njangi.member_id_number
            existing_njangi.transaction_id = njangi.transaction_id
            existing_njangi.amount = njangi.amount
            existing_njangi.benefited_date = njangi.benefited_date
            existing_njangi.id_card_number = njangi.id_card_number
            existing_njangi.comment = njangi.comment
            existing_njangi.signature = njangi.signature
            existing_njangi.save()

            logger.info(f'Njangi beneficiary created by user {request.user.id}: {existing_njangi.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(existing_njangi.id)},
                'message': _('Njangi beneficiary created successfully.'),
                'redirect': reverse_lazy('finance:njangi_list')
            }, status=201)
        except Exception as e:
            logger.error(f'Unexpected error during njangi creation: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while creating the njangi beneficiary. Please try again.')
            }, status=500)

class UpdateNjangiView(FinanceBaseView, UpdateView):
    template_name = "publics/dashboard/admin/pages/njangis/includes/update_njangi.html"
    model = Njangi
    form_class = NjangiForm
    success_url = reverse_lazy('finance:njangi_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        selected_season = self.request.session.get('selected_season')
        if selected_season:
            kwargs['season_date'] = datetime(selected_season['year'], selected_season['month'], 1)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        season_date = datetime(selected_season['year'], selected_season['month'], 1)
        context['season'] = season_date.strftime('%B %Y')
        context['is_current_season'] = (season_date.date() == Njangi.objects.aggregate(latest_date=Max('season_date'))['latest_date']) if Njangi.objects.exists() else True
        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor
        logger.debug(f"Rendering update njangi form for user {self.request.user.id}, Njangi ID {self.kwargs['pk']}")
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        selected_season = request.session.get('selected_season')
        if not selected_season:
            return JsonResponse({'success': False, 'message': _('No season selected.')}, status=400)

        season_date = datetime(selected_season['year'], selected_season['month'], 1)
        form = self.form_class(request.POST, instance=self.object, season_date=season_date)
        if not form.is_valid():
            logger.warning(f'Invalid form submission by user {request.user.id}: {form.errors}')
            return JsonResponse({
                'success': False,
                'message': _('Please fill in all required fields correctly.'),
                'errors': form.errors.as_json()
            }, status=400)

        try:
            latest_season = Njangi.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            is_current_season = (season_date.date() == latest_season) if latest_season else True

            if not request.user.is_admin and not is_current_season:
                return JsonResponse({
                    'success': False,
                    'message': _('Only admins can modify previous season data.')
                }, status=403)

            njangi = form.save()
            logger.info(f'Njangi updated by user {request.user.id}: {njangi.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(njangi.id)},
                'message': _('Njangi updated successfully.'),
                'redirect': reverse_lazy('finance:njangi_list')
            }, status=200)
        except Exception as e:
            logger.error(f'Unexpected error during njangi update: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while updating the njangi. Please try again.')
            }, status=500)

class AddNjangiMemberView(FinanceBaseView, FormView):
    template_name = "publics/dashboard/admin/pages/njangis/includes/add_njangi_member.html"
    form_class = NjangiMemberForm
    success_url = reverse_lazy('finance:njangi_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        season_date = datetime(selected_season['year'], selected_season['month'], 1)
        context['season'] = season_date.strftime('%B %Y')
        context['is_current_season'] = (season_date.date() == Njangi.objects.aggregate(latest_date=Max('season_date'))['latest_date']) if Njangi.objects.exists() else True
        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor
        logger.debug(f"Rendering add njangi member form for user {self.request.user.id}")
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

            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            latest_season = Njangi.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            is_current_season = (season_date.date() == latest_season) if latest_season else True

            if not request.user.is_admin and not is_current_season:
                return JsonResponse({
                    'success': False,
                    'message': _('Only admins can modify previous season data.')
                }, status=403)

            user = form.cleaned_data['user']
            position = form.cleaned_data['position']

            if Njangi.objects.filter(season_date=season_date, user=user).exists():
                return JsonResponse({
                    'success': False,
                    'message': _('User is already a Njangi member for this season.')
                }, status=400)

            if Njangi.objects.filter(season_date=season_date, position=position).exists():
                return JsonResponse({
                    'success': False,
                    'message': _('This position is already taken in the current season.')
                }, status=400)

            transaction_id = f"NJ-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            member_id_number = f"NJ-{timezone.now().strftime('%Y%m%d')}-{Njangi.objects.filter(season_date=season_date).count() + 1}"

            njangi = Njangi.objects.create(
                user=user,
                position=position,
                season_date=season_date,
                member_id_number=member_id_number,
                transaction_id=transaction_id,
                amount=0,
                benefited_date=season_date,
                comment="Added as Njangi member"
            )

            logger.info(f'Njangi member added by user {request.user.id}: {njangi.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(njangi.id)},
                'message': _('Njangi member added successfully.'),
                'redirect': reverse_lazy('finance:njangi_list')
            }, status=201)
        except Exception as e:
            logger.error(f'Unexpected error during njangi member addition: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while adding the njangi member. Please try again.')
            }, status=500)

class DeleteNjangiView(FinanceBaseView, View):
    def post(self, request, *args, **kwargs):
        try:
            njangi = Njangi.objects.get(pk=kwargs['pk'])
            selected_season = request.session.get('selected_season')
            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            latest_season = Njangi.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            is_current_season = (season_date.date() == latest_season) if latest_season else True

            if not (request.user.is_admin or (request.user.is_staff and is_current_season)):
                logger.warning(f"Unauthorized delete attempt by user {request.user.id} on njangi {kwargs['pk']}")
                return JsonResponse({
                    'success': False,
                    'message': _('You do not have permission to delete this njangi.')
                }, status=403)

            njangi_id = njangi.id
            njangi.delete()
            logger.info(f'Njangi {njangi_id} deleted by user {request.user.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(njangi_id)},
                'message': _('Njangi deleted successfully.')
            }, status=200)
        except Njangi.DoesNotExist:
            logger.warning(f"Njangi {kwargs['pk']} not found for deletion by user {request.user.id}")
            return JsonResponse({
                'success': False,
                'message': _('Njangi not found.')
            }, status=404)
        except Exception as e:
            logger.error(f'Unexpected error during njangi deletion: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while deleting the njangi. Please try again.')
            }, status=500)

class GetNjangiView(FinanceBaseView, View):
    def get(self, request, user_id, *args, **kwargs):
        try:
            selected_season = request.session.get('selected_season')
            if not selected_season:
                return JsonResponse({'error': 'No season selected'}, status=400)

            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            njangis = Njangi.objects.filter(
                user_id=user_id,
                season_date=season_date,
                amount=0  # Only non-benefited members
            ).select_related('user')

            njangi_data = [
                {
                    'id': njangi.id,
                    'position': njangi.position,
                    'member_id_number': njangi.member_id_number,
                    'transaction_id': njangi.transaction_id,
                    'benefited_date': njangi.benefited_date.strftime('%Y-%m-%d')
                }
                for njangi in njangis
            ]

            logger.info(f'Fetched njangis for user {user_id} by user {request.user.id}')
            return JsonResponse({'njangis': njangi_data}, status=200)
        except Exception as e:
            logger.error(f'Get njangis error: {str(e)}', exc_info=True)
            return JsonResponse({'error': 'Failed to fetch njangis'}, status=500)

class GetNjangiDetailsView(FinanceBaseView, View):
    def get(self, request, pk, *args, **kwargs):
        try:
            njangi = Njangi.objects.get(pk=pk)
            data = {
                'position': njangi.position,
                # 'name': njangi.user.get_full_name() if njangi.user else 'Unknown User',
                'member_id_number': njangi.member_id_number,
                'transaction_id': njangi.transaction_id,
                'amount': str(njangi.amount),
                'benefited_date': njangi.benefited_date.strftime('%Y-%m-%d'),
                'id_card_number': njangi.id_card_number,
                'comment': njangi.comment,
                'signature': njangi.signature,
            }
            logger.info(f'Fetched njangi details for ID {pk} by user {request.user.id}')
            return JsonResponse({'success': True, 'data': data}, status=200)
        except Njangi.DoesNotExist:
            logger.warning(f"Njangi {pk} not found for details by user {request.user.id}")
            return JsonResponse({'success': False, 'message': _('Njangi not found.')}, status=404)
        except Exception as e:
            logger.error(f'Error fetching njangi details: {str(e)}', exc_info=True)
            return JsonResponse({'success': False, 'message': _('Failed to fetch njangi details.')}, status=500)