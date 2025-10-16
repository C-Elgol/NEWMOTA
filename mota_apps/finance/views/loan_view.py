from django.views.generic import ListView, CreateView, UpdateView, TemplateView, View
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db.models import Max
from mota_apps.finance.models import Loan, LoanPayment
from mota_apps.users.models import User
from mota_apps.finance.forms.loan_form import LoanForm, LoanPaymentForm
from mota_apps.finance.views.record_finance_view import FinanceBaseView
from datetime import datetime
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class LoanListView(FinanceBaseView, ListView):
    template_name = "publics/dashboard/admin/pages/loans/loan_list.html"
    model = Loan
    context_object_name = 'loans'
    paginate_by = 100

    def get_queryset(self):
        selected_season = self.request.session.get('selected_season')
        if not selected_season:
            return Loan.objects.none()
        year = selected_season['year']
        month = selected_season['month']
        season_date = datetime(year, month, 1)
        return Loan.objects.filter(
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
        latest_season = Loan.objects.aggregate(latest_date=Max('season_date'))['latest_date']
        context['is_current_season'] = (season_date.date() == latest_season) if latest_season else True

        # Get members without loans for the season
        members_with_loans = Loan.objects.filter(
            season_date=season_date
        ).values_list('member_id', flat=True)
        context['members'] = User.objects.filter(
            is_active=True,
            is_deleted=False
        ).exclude(id__in=members_with_loans)

        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor

        logger.debug(f"Rendering loan list for season: {context['season']}, user: {self.request.user}")
        return context

class NewLoanView(FinanceBaseView, CreateView):
    template_name = "publics/dashboard/admin/pages/loans/includes/create_loan.html"
    form_class = LoanForm
    success_url = reverse_lazy('finance:loan_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        season_date = datetime(selected_season['year'], selected_season['month'], 1)
        context['season'] = season_date.strftime('%B %Y')
        # Get members without loans for the season
        members_with_loans = Loan.objects.filter(
            season_date=season_date
        ).values_list('member_id', flat=True)
        context['members'] = User.objects.filter(
            is_active=True,
            is_deleted=False
        ).exclude(id__in=members_with_loans)
        logger.debug(f"Rendering create loan form for user {self.request.user.id}")
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
            loan = form.save(commit=False)
            loan.season_date = season_date
            loan.interest_to_be_paid = loan.amount_borrowed * Decimal('0.015')  # 1.5% interest
            loan.save()

            logger.info(f'Loan created by user {request.user.id}: {loan.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(loan.id)},
                'message': _('Loan created successfully.'),
                'redirect': reverse_lazy('finance:loan_list')
            }, status=201)
        except Exception as e:
            logger.error(f'Unexpected error during loan creation: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while creating the loan. Please try again.')
            }, status=500)

class UpdateLoanView(FinanceBaseView, UpdateView):
    template_name = "publics/dashboard/admin/pages/loans/includes/update_loan.html"
    model = Loan
    form_class = LoanForm
    success_url = reverse_lazy('finance:loan_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        season_date = datetime(selected_season['year'], selected_season['month'], 1)
        context['season'] = season_date.strftime('%B %Y')
        context['members'] = User.objects.filter(is_active=True, is_deleted=False)
        context['is_admin'] = self.request.user.is_admin
        context['signature_data'] = self.object.signature if getattr(self.object, "signature", None) else ""

        latest_season = Loan.objects.aggregate(latest_date=Max('season_date'))['latest_date']
        context['is_current_season'] = (
            season_date.date() == latest_season
        ) if latest_season else True

        logger.debug(f"Rendering update loan form for user {self.request.user.id}, Loan ID {self.kwargs['pk']}")
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
            latest_season = Loan.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            is_current_season = (season_date.date() == latest_season) if latest_season else True

            if not request.user.is_admin and not is_current_season:
                return JsonResponse({
                    'success': False,
                    'message': _('Only admins can modify previous season data.')
                }, status=403)

            loan = form.save(commit=False)

            # Save signature (Base64)
            signature_data = request.POST.get('signature')
            if signature_data:
                loan.signature = signature_data

            # Recalculate interest
            loan.interest_to_be_paid = loan.amount_borrowed * Decimal('0.015')
            loan.save()

            logger.info(f'Loan updated by user {request.user.id}: {loan.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(loan.id)},
                'message': _('Loan updated successfully.'),
                'redirect': reverse_lazy('finance:loan_list')
            }, status=200)

        except Exception as e:
            logger.error(f'Unexpected error during loan update: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while updating the loan. Please try again.')
            }, status=500)
class DeleteLoanView(FinanceBaseView, View):
    def post(self, request, *args, **kwargs):
        try:
            loan = Loan.objects.get(pk=kwargs['pk'])
            selected_season = request.session.get('selected_season')
            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            latest_season = Loan.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            is_current_season = (season_date.date() == latest_season) if latest_season else True

            if not (request.user.is_admin or (request.user.is_staff and is_current_season)):
                logger.warning(f"Unauthorized delete attempt by user {request.user.id} on loan {kwargs['pk']}")
                return JsonResponse({
                    'success': False,
                    'message': _('You do not have permission to delete this loan.')
                }, status=403)

            loan_id = loan.id
            loan.delete()
            logger.info(f'Loan {loan_id} deleted by user {request.user.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(loan_id)},
                'message': _('Loan deleted successfully.')
            }, status=200)
        except Loan.DoesNotExist:
            logger.warning(f"Loan {kwargs['pk']} not found for deletion by user {request.user.id}")
            return JsonResponse({
                'success': False,
                'message': _('Loan not found.')
            }, status=404)
        except Exception as e:
            logger.error(f'Unexpected error during loan deletion: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while deleting the loan. Please try again.')
            }, status=500)

class PayLoanView(FinanceBaseView, TemplateView):
    template_name = "publics/dashboard/admin/pages/loans/includes/pay_loan.html"
    form_class = LoanPaymentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_season = self.request.session.get('selected_season')
        if not selected_season:
            logger.warning("No season selected in PayLoanView")
            context['season'] = "N/A"
        else:
            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            context['season'] = season_date.strftime('%B %Y')
            context['is_current_season'] = (season_date.date() == Loan.objects.aggregate(latest_date=Max('season_date'))['latest_date']) if Loan.objects.exists() else True
            # Get members with unpaid/partially paid loans
            context['members'] = User.objects.filter(
                is_active=True,
                is_deleted=False,
                loans__season_date=season_date,
                loans__status__in=['UNPAID', 'PARTIAL']
            ).distinct()
        context['form'] = self.form_class()
        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor
        logger.debug(f"Rendering pay loan form for user {self.request.user.id}")
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if not form.is_valid():
            logger.warning(f'Invalid loan payment form submission by user {request.user.id}: {form.errors}')
            return JsonResponse({
                'success': False,
                'message': _('Please fill in all required fields correctly.'),
                'errors': form.errors.as_json()
            }, status=400)

        try:
            selected_season = request.session.get('selected_season')
            if not selected_season:
                return JsonResponse({
                    'success': False,
                    'message': _('No season selected.')
                }, status=400)

            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            latest_season = Loan.objects.aggregate(latest_date=Max('season_date'))['latest_date']
            is_current_season = (season_date.date() == latest_season) if latest_season else True

            if not (request.user.is_admin or (request.user.is_staff and is_current_season)):
                return JsonResponse({
                    'success': False,
                    'message': _('You do not have permission to record loan payments.')
                }, status=403)

            loan = form.cleaned_data['loan']
            amount = form.cleaned_data['amount']
            payment_date = form.cleaned_data['payment_date']
            comment = form.cleaned_data['comment']

            LoanPayment.objects.create(
                loan=loan,
                season_date=season_date,
                amount=amount,
                payment_date=payment_date,
                recorded_by=request.user,
                comment=comment
            )

            loan.amount_paid += amount
            if loan.amount_paid >= loan.total_amount_plus_interest:
                loan.status = 'PAID'
            elif loan.amount_paid > 0:
                loan.status = 'PARTIAL'
            loan.save()

            logger.info(f'Loan payment recorded by user {request.user.id} for loan {loan.id}')
            return JsonResponse({
                'success': True,
                'message': _('Loan payment recorded successfully.'),
                'redirect': reverse_lazy('finance:loan_list')
            }, status=201)
        except Exception as e:
            logger.error(f'Pay loan error: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('Failed to record loan payment.')
            }, status=500)

class GetLoansView(FinanceBaseView, View):
    def get(self, request, member_id, *args, **kwargs):
        try:
            selected_season = request.session.get('selected_season')
            if not selected_season:
                return JsonResponse({'error': 'No season selected'}, status=400)

            season_date = datetime(selected_season['year'], selected_season['month'], 1)
            loans = Loan.objects.filter(
                member_id=member_id,
                season_date=season_date,
                status__in=['UNPAID', 'PARTIAL']
            ).select_related('member')

            loan_data = [
                {
                    'id': loan.id,
                    'amount_left_to_pay': float(loan.amount_left_to_pay),
                    'amount_borrowed': float(loan.amount_borrowed),
                    'borrow_date': loan.borrow_date.strftime('%Y-m-d')
                }
                for loan in loans
            ]

            logger.info(f'Fetched loans for member {member_id} by user {request.user.id}')
            return JsonResponse({'loans': loan_data}, status=200)
        except Exception as e:
            logger.error(f'Get loans error: {str(e)}', exc_info=True)
            return JsonResponse({'error': 'Failed to fetch loans'}, status=500)