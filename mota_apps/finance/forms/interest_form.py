from django import forms
from django.utils.translation import gettext_lazy as _
from mota_apps.finance.models import Interest
from mota_apps.users.models import User
from django.conf import settings

class InterestForm(forms.ModelForm):
    class Meta:
        model = Interest
        fields = ['member', 'total_savings', 'interest_share']
        widgets = {
            'member': forms.Select(attrs={
                'class': 'select2 w-full',
                'required': True,
            }),
            'total_savings': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'step': '0.01',
                'min': '0',
                'required': True,
            }),
            'interest_share': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'step': '0.01',
                'min': '0',
                'required': True,
                'readonly': True,  # Interest share is calculated, not user-editable
            }),
        }
        labels = {
            'member': _('Member'),
            'total_savings': _('Total Savings'),
            'interest_share': _('Interest Share'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].queryset = User.objects.filter(is_active=True, is_deleted=False)