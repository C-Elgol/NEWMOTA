from django import forms
from django.utils.translation import gettext_lazy as _
from mota_apps.finance.models import ProjectRecord
from datetime import date

class ProjectForm(forms.ModelForm):
    file_path = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm',
            'accept': '.pdf,.jpg,.jpeg,.png',
            'placeholder': _('Upload project form (PDF, JPG, PNG)')
        })
    )
    signature = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={
            'id': 'signature-input',
            'class': 'w-full'
        })
    )

    class Meta:
        model = ProjectRecord
        fields = ['amount_collected', 'interest_collected', 'date_collected', 'comment', 'file_path', 'signature']
        widgets = {
            'amount_collected': forms.NumberInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm',
                'step': '0.01',
                'min': '0',
                'placeholder': _('Enter amount collected')
            }),
            'interest_collected': forms.NumberInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm',
                'step': '0.01',
                'min': '0',
                'placeholder': _('Enter interest collected')
            }),
            'date_collected': forms.DateInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm',
                'type': 'date',
                'placeholder': _('Select date')
            }),
            'comment': forms.Textarea(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm',
                'rows': 4,
                'placeholder': _('Enter any comments')
            }),
        }

    def clean_date_collected(self):
        date_collected = self.cleaned_data.get('date_collected')
        if date_collected and date_collected > date.today():
            raise forms.ValidationError(_('Date collected cannot be in the future.'))
        return date_collected

    def clean_file_path(self):
        file = self.cleaned_data.get('file_path')
        if file:
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
            if file.content_type not in allowed_types:
                raise forms.ValidationError(_('Invalid file type. Only PDF, JPG, and PNG are allowed.'))
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError(_('File size exceeds 5MB limit.'))
        return file