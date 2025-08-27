from django import forms
from django.utils.translation import gettext_lazy as _
from mota_apps.finance.models import Expenditure

class ExpenditureForm(forms.ModelForm):
    class Meta:
        model = Expenditure
        fields = ['entertainment_spent', 'other_expenditures', 'comment']
        widgets = {
            'entertainment_spent': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 focus:ring focus:ring-indigo-200',
                'step': '0.01',
                'min': '0',
                'required': 'required'
            }),
            'other_expenditures': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 focus:ring focus:ring-indigo-200',
                'step': '0.01',
                'min': '0',
                'required': 'required'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 focus:ring focus:ring-indigo-200',
                'rows': 4
            })
        }
        labels = {
            'entertainment_spent': _('Entertainment Spent'),
            'other_expenditures': _('Other Expenditures'),
            'comment': _('Comment')
        }