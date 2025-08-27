from django import forms
from django.utils.translation import gettext_lazy as _
from mota_apps.users.models import User
from phonenumber_field.formfields import PhoneNumberField

class UserForm(forms.ModelForm):
    phone_number = PhoneNumberField(
        label=_("Phone Number"),
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full border border-gray-300 rounded-md p-2 focus:ring focus:ring-indigo-200',
            'placeholder': _('Enter phone number (e.g., +237123456789)')
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'is_staff', 'is_admin', 'is_client', 'is_visitor']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 focus:ring focus:ring-indigo-200',
                'required': 'required'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 focus:ring focus:ring-indigo-200',
                'required': 'required'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 focus:ring focus:ring-indigo-200',
                'required': 'required'
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
            }),
            'is_admin': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
            }),
            'is_client': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
            }),
            'is_visitor': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
            })
        }
        labels = {
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
            'email': _('Email'),
            'is_staff': _('Staff'),
            'is_admin': _('Admin'),
            'is_client': _('Client'),
            'is_visitor': _('Visitor')
        }