from django import forms
from django.utils.translation import gettext_lazy as _
from mota_apps.finance.models import FinanceRecord
from mota_apps.users.models import User

class FinanceRecordForm(forms.ModelForm):
    class Meta:
        model = FinanceRecord
        fields = ['member', 'entertainment_fees', 'savings', 'njangi', 'project', 'others']
        widgets = {
            'member': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
            'entertainment_fees': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md', 'step': '0.01'}),
            'savings': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md', 'step': '0.01'}),
            'njangi': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md', 'step': '0.01'}),
            'project': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md', 'step': '0.01'}),
            'others': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].queryset = User.objects.filter(is_active=True, is_deleted=False)