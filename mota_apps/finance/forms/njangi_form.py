from django import forms
from django.utils.translation import gettext_lazy as _
from mota_apps.finance.models import Njangi
from mota_apps.users.models import User

class NjangiForm(forms.ModelForm):
    class Meta:
        model = Njangi
        fields = ['user', 'member_id_number', 'transaction_id', 'amount', 'benefited_date', 'id_card_number', 'comment', 'signature']
        widgets = {
            'user': forms.Select(attrs={'class': 'select2 w-full'}),
            'benefited_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border border-gray-300 rounded-md p-2'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'w-full border border-gray-300 rounded-md p-2'}),
            'member_id_number': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded-md p-2'}),
            'transaction_id': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded-md p-2'}),
            'id_card_number': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded-md p-2'}),
            'comment': forms.Textarea(attrs={'class': 'w-full border border-gray-300 rounded-md p-2', 'rows': 4}),
            'signature': forms.Textarea(attrs={'class': 'w-full border border-gray-300 rounded-md p-2', 'rows': 4}),
        }
        labels = {
            'user': _('Select Member'),
            'member_id_number': _('Member ID'),
            'transaction_id': _('Transaction ID'),
            'amount': _('Njangi Amount'),
            'benefited_date': _('Benefited Date'),
            'id_card_number': _('ID Card Number'),
            'comment': _('Comment'),
            'signature': _('Signature'),
        }

    def __init__(self, *args, **kwargs):
        season_date = kwargs.pop('season_date', None)
        super().__init__(*args, **kwargs)
        if season_date:
            # Filter users who are non-benefited Njangi members for this season
            self.fields['user'].queryset = User.objects.filter(
                is_active=True,
                is_deleted=False,
                njangi_records__season_date=season_date,
                njangi_records__amount=0
            ).distinct()

class NjangiMemberForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True, is_deleted=False),
        label=_('Select User'),
        widget=forms.Select(attrs={'class': 'select2 w-full'}),
        required=True
    )
    position = forms.CharField(
        label=_('Position'),
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded-md p-2'}),
        required=True
    )