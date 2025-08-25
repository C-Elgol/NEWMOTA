import re
import logging
import traceback
from typing import Any
from django.http import HttpRequest, HttpResponse
from django.views.generic import TemplateView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.core.mail import EmailMessage, get_connection
from django.db import transaction
from django.contrib import messages
from decouple import config

from mota_apps.users.models import User

logger = logging.getLogger(__name__)

class PasswordResetRequestView(TemplateView):
    """
    Name: PasswordResetRequestView
    Description: Handles password reset requests by sending a reset code via email.
                 Uses transaction.atomic() to ensure atomic operations.
                 Uses ToastManager for error/success messages.
    Author: @ayemele
    """
    template_name = 'publics/auth/password_reset_request.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(request, self.template_name, {'error': None, 'email': ''})

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        email = request.POST.get("email", "").strip()
        context = {'error': None, 'email': email}

        try:
            # Validate email
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                messages.error(request, _("Invalid email format."))
                return render(request, self.template_name, context)

            user = User.objects.filter(email=email).first()
            if not user:
                messages.error(request, _("No user found with this email."))
                return render(request, self.template_name, context)

            # Generate and store reset code
            with transaction.atomic():
                if not isinstance(user.metadata, dict):
                    user.metadata = {}
                reset_code = get_random_string(6, allowed_chars='0123456789')
                user.metadata["password_reset_code"] = reset_code
                user.metadata["password_reset_code_created_at"] = timezone.now().isoformat()
                user.save()

                # Build reset email
                html_content = render_to_string(
                    template_name="publics/emails/password_reset_email.html",
                    context={
                        "user": user,
                        "reset_code": reset_code,
                        "site_name": "Mota Solutions"
                    }
                )

                email_message = EmailMessage(
                    subject="Your Password Reset Code",
                    body=html_content,
                    from_email=f"Mota Solutions <{config('EMAIL_HOST_USER')}>",
                    to=[email],
                )
                email_message.content_subtype = "html"

                # Gmail SMTP settings from .env
                connection = get_connection(
                    backend="django.core.mail.backends.smtp.EmailBackend",
                    host="smtp.gmail.com",
                    port=587,
                    username=config('EMAIL_HOST_USER'),
                    password=config('EMAIL_HOST_PASSWORD'),
                    use_tls=True
                )
                email_message.connection = connection

                # Send email
                email_message.send()

            logger.info(f"✅ Password reset code sent to {email} (ID: {user.id})")
            messages.success(request, _("A password reset code has been sent to your email."))
            return redirect('users:password_reset_verify', email=email)

        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Unexpected error during password reset request for email {email}: {e}\n{trace}")
            messages.error(request, _("An unexpected error occurred. Please try again later."))
            return render(request, self.template_name, context)


class PasswordResetVerifyView(TemplateView):
    """
    Name: PasswordResetVerifyView
    Description: Verifies the password reset code and redirects to password reset form.
                 Uses ToastManager for error/success messages.
    Author: @ayemele
    """
    template_name = 'publics/auth/password_reset_verify.html'

    def get(self, request: HttpRequest, email: str, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(request, self.template_name, {'email': email, 'error': None})

    def post(self, request: HttpRequest, email: str, *args: Any, **kwargs: Any) -> HttpResponse:
        code = request.POST.get("code", "").strip()
        context = {'email': email, 'error': None}

        try:
            user = User.objects.filter(email=email).first()
            if not user:
                messages.error(request, _("No user found with this email."))
                return render(request, self.template_name, context)

            if not isinstance(user.metadata, dict) or "password_reset_code" not in user.metadata:
                messages.error(request, _("Invalid or expired reset code. Please request a new one."))
                return render(request, self.template_name, context)

            stored_code = user.metadata.get("password_reset_code")
            code_created_at = user.metadata.get("password_reset_code_created_at")
            if not stored_code or not code_created_at:
                messages.error(request, _("Invalid or expired reset code. Please request a new one."))
                return render(request, self.template_name, context)

            # Check if code is expired (10 minutes)
            from datetime import datetime
            created_at = datetime.fromisoformat(code_created_at)
            if (timezone.now() - created_at).total_seconds() > 600:
                messages.error(request, _("Reset code has expired. Please request a new one."))
                return render(request, self.template_name, context)

            if code != stored_code:
                messages.error(request, _("Invalid reset code."))
                return render(request, self.template_name, context)

            logger.info(f"✅ Password reset code verified for {email} (ID: {user.id})")
            messages.success(request, _("Code verified! Please set your new password."))
            return redirect('users:password_reset', email=email)

        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Unexpected error during password reset verification for email {email}: {e}\n{trace}")
            messages.error(request, _("An unexpected error occurred. Please try again later."))
            return render(request, self.template_name, context)


class PasswordResetView(TemplateView):
    """
    Name: PasswordResetView
    Description: Handles the new password submission after code verification.
                 Updates the user's password and logs them in.
                 Uses ToastManager for error/success messages.
    Author: @ayemele
    """
    template_name = 'publics/auth/password_reset.html'

    def get(self, request: HttpRequest, email: str, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(request, self.template_name, {'email': email, 'error': None})

    def post(self, request: HttpRequest, email: str, *args: Any, **kwargs: Any) -> HttpResponse:
        password = request.POST.get("password", "").strip()
        password2 = request.POST.get("password2", "").strip()
        context = {'email': email, 'error': None}

        try:
            user = User.objects.filter(email=email).first()
            if not user:
                messages.error(request, _("No user found with this email."))
                return render(request, self.template_name, context)

            # Validate password
            if len(password) < 8 or not re.search(r'\d', password) or not re.search(r'[A-Za-z]', password):
                messages.error(request, _("Password must be at least 8 characters and contain at least one letter and one number."))
                return render(request, self.template_name, context)

            if password != password2:
                messages.error(request, _("Passwords do not match."))
                return render(request, self.template_name, context)

            # Update password and clear reset code
            with transaction.atomic():
                user.set_password(password)
                user.metadata.pop("password_reset_code", None)
                user.metadata.pop("password_reset_code_created_at", None)
                user.save()

                # Log the user in
                from django.contrib.auth import login
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            logger.info(f"✅ Password reset successful for {email} (ID: {user.id})")
            messages.success(request, _("Password reset successful! You are now logged in."))
            return redirect('users:home')

        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Unexpected error during password reset for email {email}: {e}\n{trace}")
            messages.error(request, _("An unexpected error occurred. Please try again later."))
            return render(request, self.template_name, context)