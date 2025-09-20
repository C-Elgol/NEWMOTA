from django import forms
from django.utils.translation import gettext_lazy as _
from mota_apps.finance.models import Loan, LoanPayment
from mota_apps.users.models import User

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = [
            'member',
            'amount_borrowed',
            'borrow_date',
            'id_card_number',
            'signature',
            'comment'
        ]
        widgets = {
            'member': forms.Select(
                attrs={
                    'class': 'select2 w-full border-gray-300 rounded-md shadow-sm focus:ring focus:ring-primary focus:border-primary',
                    'placeholder': _('Select a member'),
                }
            ),
            'amount_borrowed': forms.NumberInput(
                attrs={
                    'step': '0.01',
                    'min': '0',
                    'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring focus:ring-primary focus:border-primary',
                    'placeholder': _('Enter loan amount'),
                }
            ),
            'borrow_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring focus:ring-primary focus:border-primary',
                }
            ),
            'id_card_number': forms.TextInput(
                attrs={
                    'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring focus:ring-primary focus:border-primary',
                    'placeholder': _('Enter ID card number'),
                }
            ),
            'signature': forms.Textarea(
                attrs={
                    'rows': 3,
                    'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring focus:ring-primary focus:border-primary resize-none',
                    'placeholder': _('Enter signature details'),
                }
            ),
            'comment': forms.Textarea(
                attrs={
                    'rows': 3,
                    'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring focus:ring-primary focus:border-primary resize-none',
                    'placeholder': _('Add comment (optional)'),
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        member = cleaned_data.get('member')
        if member and not member.is_active:
            raise forms.ValidationError(_('Selected member is not active.'))

        amount_borrowed = cleaned_data.get('amount_borrowed')
        if amount_borrowed and amount_borrowed <= 0:
            raise forms.ValidationError(_('Loan amount must be greater than zero.'))
        return cleaned_data


class LoanPaymentForm(forms.ModelForm):
    class Meta:
        model = LoanPayment
        fields = [
            'loan',
            'amount',
            'payment_date',
            'comment'
        ]
        widgets = {
            'loan': forms.Select(
                attrs={
                    'class': 'select2 w-full border-gray-300 rounded-md shadow-sm focus:ring focus:ring-green-500 focus:border-green-500',
                    'placeholder': _('Select a loan'),
                }
            ),
            'amount': forms.NumberInput(
                attrs={
                    'step': '0.01',
                    'min': '0',
                    'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring focus:ring-green-500 focus:border-green-500',
                    'placeholder': _('Enter payment amount'),
                }
            ),
            'payment_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring focus:ring-green-500 focus:border-green-500',
                }
            ),
            'comment': forms.Textarea(
                attrs={
                    'rows': 3,
                    'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring focus:ring-green-500 focus:border-green-500 resize-none',
                    'placeholder': _('Add comment (optional)'),
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        loan = cleaned_data.get('loan')
        amount = cleaned_data.get('amount')
        if loan and amount:
            if amount <= 0:
                raise forms.ValidationError(_('Payment amount must be greater than zero.'))
            if amount > loan.amount_left_to_pay:
                raise forms.ValidationError(_('Payment amount exceeds the remaining loan balance.'))
        return cleaned_data
