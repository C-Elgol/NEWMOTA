from django.views.generic import ListView, CreateView, UpdateView, View
from django.http import JsonResponse, Http404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db.models import Max, Sum
from mota_apps.finance.models import Interest, Loan, FinanceRecord, Collection
from mota_apps.users.models import User
from mota_apps.finance.forms.interest_form import InterestForm
from mota_apps.finance.views.record_finance_view import FinanceBaseView
from datetime import datetime
import logging
from decimal import Decimal
import json
import uuid

logger = logging.getLogger(__name__)

class InterestListView(FinanceBaseView, ListView):
    template_name = "publics/dashboard/admin/pages/interests/interest_list.html"
    model = Interest
    context_object_name = 'interests'
    paginate_by = 100

    def get_queryset(self):
        selected_season = self.request.session.get('selected_season')
        if not selected_season or selected_season['month'] == 6:
            return Interest.objects.none()
        year = selected_season['year']
        month = selected_season['month']
        season_date = datetime(year, month, 1)
        return Interest.objects.filter(
            season_date=season_date
        ).select_related('member').order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        
        if not selected_season or selected_season['month'] == 6:
            logger.warning("No season or June selected")
            context['season'] = 'N/A'
            context['total_loan_interest'] = Decimal('0.00')
            context['total_savings'] = Decimal('0.00')
            context['interests'] = []
            return context

        year = selected_season['year']
        month = selected_season['month']
        season_date = datetime(year, month, 1)
        context['season'] = season_date.strftime('%B %Y')

        # Determine if current season
        latest_season = Interest.objects.aggregate(latest_date=Max('season_date'))['latest_date']
        context['is_current_season'] = (season_date.date() == latest_season) if latest_season else True

        # Get members without interest records for the season
        members_with_interests = Interest.objects.filter(
            season_date=season_date
        ).values_list('member_id', flat=True)
        context['members'] = User.objects.filter(
            is_active=True,
            is_deleted=False
        ).exclude(id__in=members_with_interests)

        # Calculate total interest collected from loans
        total_loan_interest = Loan.objects.filter(
            season_date=season_date
        ).aggregate(total=Sum('interest_to_be_paid'))['total'] or Decimal('0.00')
        context['total_loan_interest'] = total_loan_interest

        # Calculate total savings for the season
        total_savings = FinanceRecord.objects.filter(
            season_date=season_date
        ).aggregate(total=Sum('savings'))['total'] or Decimal('0.00')
        context['total_savings'] = total_savings

        # Get collected amounts and signatures
        collections = Collection.objects.filter(
            season_date=season_date
        ).values('member_id').annotate(
            total_collected=Sum('amount_collected'),
            latest_signature=Max('signature')
        )
        collected_dict = {str(c['member_id']): {
            'total_collected': c['total_collected'] or Decimal('0.00'),
            'signature': c['latest_signature'] or ''
        } for c in collections}

        # Update interests with collected, net interest, and signature
        interests = []
        for interest in self.get_queryset():
            collection_data = collected_dict.get(str(interest.member_id), {
                'total_collected': Decimal('0.00'),
                'signature': ''
            })
            collected = collection_data['total_collected']
            signature = collection_data['signature']
            net_interest = interest.interest_share - collected
            interests.append({
                'interest': interest,
                'collected': collected,
                'net_interest': net_interest,
                'total': interest.total_savings + net_interest,
                'signature': signature
            })
        context['interests'] = interests

        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor

        logger.debug(f"Rendering interest list for season: {context['season']}, user: {self.request.user}")
        return context

class NewInterestView(FinanceBaseView, CreateView):
    template_name = "publics/dashboard/admin/pages/interests/includes/create_interest.html"
    form_class = InterestForm
    success_url = reverse_lazy('finance:interest_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        if not selected_season or selected_season['month'] == 6:
            logger.warning("No season or June selected")
            context['season'] = 'N/A'
            context['total_loan_interest'] = Decimal('0.00')
            context['total_savings'] = Decimal('0.00')
            context['members'] = User.objects.none()
            return context

        season_date = datetime(selected_season['year'], selected_season['month'], 1)
        context['season'] = season_date.strftime('%B %Y')
        # Get members without interest records for the season
        members_with_interests = Interest.objects.filter(
            season_date=season_date
        ).values_list('member_id', flat=True)
        context['members'] = User.objects.filter(
            is_active=True,
            is_deleted=False
        ).exclude(id__in=members_with_interests)
        # Total interest from loans
        total_loan_interest = Loan.objects.filter(
            season_date=season_date
        ).aggregate(total=Sum('interest_to_be_paid'))['total'] or Decimal('0.00')
        context['total_loan_interest'] = total_loan_interest
        # Total savings
        total_savings = FinanceRecord.objects.filter(
            season_date=season_date
        ).aggregate(total=Sum('savings'))['total'] or Decimal('0.00')
        context['total_savings'] = total_savings
        logger.debug(f"Rendering create interest form for user {self.request.user.id}")
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
                    'message': _('Interest records cannot be created for June.')
                }, status=400)

            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            interest = form.save(commit=False)
            interest.season_date = season_date

            # Calculate interest share based on savings proportion
            total_savings = FinanceRecord.objects.filter(
                season_date=season_date
            ).aggregate(total=Sum('savings'))['total'] or Decimal('0.00')
            total_loan_interest = Loan.objects.filter(
                season_date=season_date
            ).aggregate(total=Sum('interest_to_be_paid'))['total'] or Decimal('0.00')

            if total_savings > 0:
                interest_share = (interest.total_savings / total_savings) * total_loan_interest
                interest.interest_share = interest_share.quantize(Decimal('0.01'))

            interest.save()

            logger.info(f'Interest created by user {request.user.id}: {interest.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(interest.id)},
                'message': _('Interest record created successfully.'),
                'redirect': reverse_lazy('finance:interest_list')
            }, status=201)
        except Exception as e:
            logger.error(f'Unexpected error during interest creation: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while creating the interest record. Please try again.')
            }, status=500)

class UpdateInterestView(FinanceBaseView, UpdateView):
    template_name = "publics/dashboard/admin/pages/interests/includes/update_interest.html"
    model = Interest
    form_class = InterestForm
    success_url = reverse_lazy('finance:interest_list')

    def get_object(self, queryset=None):
        try:
            return Interest.objects.get(id=self.kwargs['pk'])
        except Interest.DoesNotExist:
            logger.warning(f"Interest {self.kwargs['pk']} not found for update by user {self.request.user.id}")
            raise Http404(_('Interest record not found.'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        if not selected_season or selected_season['month'] == 6:
            logger.warning("No season or June selected")
            context['season'] = 'N/A'
            context['total_loan_interest'] = Decimal('0.00')
            context['total_savings'] = Decimal('0.00')
            context['members'] = User.objects.none()
            return context

        season_date = datetime(selected_season['year'], selected_season['month'], 1)
        context['season'] = season_date.strftime('%B %Y')
        context['members'] = User.objects.filter(is_active=True, is_deleted=False)
        context['is_admin'] = self.request.user.is_admin

        latest_season = Interest.objects.aggregate(latest_date=Max('season_date'))['latest_date']
        context['is_current_season'] = (
            season_date.date() == latest_season
        ) if latest_season else True

        # Total interest from loans
        total_loan_interest = Loan.objects.filter(
            season_date=season_date
        ).aggregate(total=Sum('interest_to_be_paid'))['total'] or Decimal('0.00')
        context['total_loan_interest'] = total_loan_interest

        # Total savings
        total_savings = FinanceRecord.objects.filter(
            season_date=season_date
        ).aggregate(total=Sum('savings'))['total'] or Decimal('0.00')
        context['total_savings'] = total_savings

        logger.debug(f"Rendering update interest form for user {self.request.user.id}, Interest ID {self.kwargs['pk']}")
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
                    'message': _('Interest records cannot be updated for June.')
                }, status=400)

            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            latest_season = Interest.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            is_current_season = (season_date.date() == latest_season) if latest_season else True

            if not request.user.is_admin and not is_current_season:
                return JsonResponse({
                    'success': False,
                    'message': _('Only admins can modify previous season data.')
                }, status=403)

            interest = form.save(commit=False)

            # Recalculate interest share
            total_savings = FinanceRecord.objects.filter(
                season_date=season_date
            ).aggregate(total=Sum('savings'))['total'] or Decimal('0.00')
            total_loan_interest = Loan.objects.filter(
                season_date=season_date
            ).aggregate(total=Sum('interest_to_be_paid'))['total'] or Decimal('0.00')

            if total_savings > 0:
                interest_share = (interest.total_savings / total_savings) * total_loan_interest
                interest.interest_share = interest_share.quantize(Decimal('0.01'))

            interest.save()

            logger.info(f'Interest updated by user {request.user.id}: {interest.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(interest.id)},
                'message': _('Interest record updated successfully.'),
                'redirect': reverse_lazy('finance:interest_list')
            }, status=200)
        except Exception as e:
            logger.error(f'Unexpected error during interest update: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while updating the interest record. Please try again.')
            }, status=500)

class DeleteInterestView(FinanceBaseView, View):
    def post(self, request, *args, **kwargs):
        try:
            interest = Interest.objects.get(id=self.kwargs['pk'])
            selected_season = request.session.get('selected_season')
            if selected_season['month'] == 6:
                return JsonResponse({
                    'success': False,
                    'message': _('Interest records cannot be deleted for June.')
                }, status=400)

            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            latest_season = Interest.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            is_current_season = (season_date.date() == latest_season) if latest_season else True

            if not (request.user.is_admin or (request.user.is_staff and is_current_season)):
                logger.warning(f"Unauthorized delete attempt by user {request.user.id} on interest {self.kwargs['pk']}")
                return JsonResponse({
                    'success': False,
                    'message': _('You do not have permission to delete this interest record.')
                }, status=403)

            interest_id = str(interest.id)
            interest.delete()
            logger.info(f'Interest {interest_id} deleted by user {request.user.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': interest_id},
                'message': _('Interest record deleted successfully.')
            }, status=200)
        except Interest.DoesNotExist:
            logger.warning(f"Interest {self.kwargs['pk']} not found for deletion by user {self.request.user.id}")
            return JsonResponse({
                'success': False,
                'message': _('Interest record not found.')
            }, status=404)
        except Exception as e:
            logger.error(f'Unexpected error during interest deletion: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while deleting the interest record. Please try again.')
            }, status=500)

class GetMemberSavingsView(FinanceBaseView, View):
    def get(self, request, *args, **kwargs):
        try:
            member_id = kwargs.get('member_id')
            try:
                uuid.UUID(member_id)  # Validate UUID format
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': _('Invalid member ID format.')
                }, status=400)

            selected_season = request.session.get('selected_season')
            if not selected_season:
                return JsonResponse({
                    'success': False,
                    'message': _('No season selected.')
                }, status=400)

            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            if season_date.month == 6:
                return JsonResponse({
                    'success': False,
                    'message': _('No interest calculations for June.')
                }, status=400)

            try:
                User.objects.get(id=member_id)  # Verify member exists
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': _('Member not found.')
                }, status=404)

            total_savings = FinanceRecord.objects.filter(
                season_date=season_date,
                member_id=member_id
            ).aggregate(total=Sum('savings'))['total'] or Decimal('0.00')

            total_loan_interest = Loan.objects.filter(
                season_date=season_date
            ).aggregate(total=Sum('interest_to_be_paid'))['total'] or Decimal('0.00')
            total_system_savings = FinanceRecord.objects.filter(
                season_date=season_date
            ).aggregate(total=Sum('savings'))['total'] or Decimal('0.00')

            interest_share = Decimal('0.00')
            if total_system_savings > 0:
                interest_share = (total_savings / total_system_savings) * total_loan_interest
                interest_share = interest_share.quantize(Decimal('0.01'))

            return JsonResponse({
                'success': True,
                'total_savings': str(total_savings),
                'interest_share': str(interest_share)
            }, status=200)
        except Exception as e:
            logger.error(f'Error fetching member savings: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An error occurred while fetching savings.')
            }, status=500)

class CollectInterestView(FinanceBaseView, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            interest_id = data.get('interest_id')
            member_id = data.get('member_id')
            amount_collected = Decimal(data.get('amount_collected'))
            signature = data.get('signature')

            if not (interest_id and member_id and amount_collected and signature):
                return JsonResponse({
                    'success': False,
                    'message': _('Missing required fields.')
                }, status=400)

            try:
                uuid.UUID(interest_id)
                uuid.UUID(member_id)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': _('Invalid ID format.')
                }, status=400)

            selected_season = request.session.get('selected_season')
            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            if season_date.month == 6:
                return JsonResponse({
                    'success': False,
                    'message': _('Collections not allowed for June.')
                }, status=400)

            interest = Interest.objects.get(id=interest_id, member_id=member_id)
            collection, created = Collection.objects.get_or_create(
                member_id=member_id,
                season_date=season_date,
                defaults={'amount_collected': amount_collected, 'signature': signature}
            )
            if not created:
                collection.amount_collected += amount_collected
                collection.signature = signature
                collection.save()

            logger.info(f'Collection recorded for interest {interest_id} by user {request.user.id}')
            return JsonResponse({
                'success': True,
                'message': _('Collection recorded successfully.')
            }, status=200)
        except Interest.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('Interest record not found.')
            }, status=404)
        except Exception as e:
            logger.error(f'Error recording collection: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An error occurred while recording the collection.')
            }, status=500)