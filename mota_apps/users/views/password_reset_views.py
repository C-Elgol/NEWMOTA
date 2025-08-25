import re
import logging
import traceback
from typing import Any
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
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
    Description: Handles password reset requests via AJAX.
                 Sends a reset code to the user's email.
                 Returns JSON responses for AJAX requests.
    Author: @ayemele
    """
    template_name = 'publics/auth/password_reset_request.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(request, self.template_name, {'error': None, 'email': ''})

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        email = request.POST.get("email", "").strip()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        fields = {'email': email}

        try:
            if not email:
                error_message = _("Email is required.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message, 'fields': fields})
                messages.error(request, error_message)
                return render(request, self.template_name, fields)

            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                error_message = _("Invalid email format.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message, 'fields': fields})
                messages.error(request, error_message)
                return render(request, self.template_name, fields)

            user = User.objects.filter(email=email).first()
            if not user:
                error_message = _("No user found with this email.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message, 'fields': fields})
                messages.error(request, error_message)
                return render(request, self.template_name, fields)

            with transaction.atomic():
                if not isinstance(user.metadata, dict):
                    user.metadata = {}
                reset_code = get_random_string(6, allowed_chars='0123456789')
                user.metadata["reset_code"] = reset_code
                user.metadata["reset_code_created_at"] = timezone.now().isoformat()
                user.save()

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

                connection = get_connection(
                    backend="django.core.mail.backends.smtp.EmailBackend",
                    host="smtp.gmail.com",
                    port=587,
                    username=config('EMAIL_HOST_USER'),
                    password=config('EMAIL_HOST_PASSWORD'),
                    use_tls=True
                )
                email_message.connection = connection
                email_message.send()

            logger.info(f"✅ Password reset code sent to {email} (ID: {user.id})")
            success_message = _("Password reset code sent! Please check your email.")
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': success_message,
                    'redirect_url': reverse('users:password_reset_verify', kwargs={'email': email})
                })
            messages.success(request, success_message)
            return redirect('users:password_reset_verify', email=email)

        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Unexpected error during password reset request for email {email}: {e}\n{trace}")
            error_message = _("An unexpected error occurred. Please try again later.")
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_message, 'fields': fields})
            messages.error(request, error_message)
            return render(request, self.template_name, fields)


class PasswordResetVerifyView(TemplateView):
    """
    Name: PasswordResetVerifyView
    Description: Handles verification of password reset code via AJAX.
                 Returns JSON responses for AJAX requests.
    Author: @ayemele
    """
    template_name = 'publics/auth/password_reset_verify.html'

    def get(self, request: HttpRequest, email: str, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(request, self.template_name, {'email': email, 'error': None})

    def post(self, request: HttpRequest, email: str, *args: Any, **kwargs: Any) -> HttpResponse:
        code = request.POST.get("code", "").strip()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            user = User.objects.filter(email=email).first()
            if not user:
                error_message = _("No user found with this email.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message})
                messages.error(request, error_message)
                return render(request, self.template_name, {'email': email})

            if not isinstance(user.metadata, dict) or "reset_code" not in user.metadata:
                error_message = _("Invalid or expired reset code. Please request a new one.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message})
                messages.error(request, error_message)
                return render(request, self.template_name, {'email': email})

            stored_code = user.metadata.get("reset_code")
            code_created_at = user.metadata.get("reset_code_created_at")
            if not stored_code or not code_created_at:
                error_message = _("Invalid or expired reset code. Please request a new one.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message})
                messages.error(request, error_message)
                return render(request, self.template_name, {'email': email})

            from datetime import datetime
            created_at = datetime.fromisoformat(code_created_at)
            if (timezone.now() - created_at).total_seconds() > 600:
                error_message = _("Reset code has expired. Please request a new one.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message})
                messages.error(request, error_message)
                return render(request, self.template_name, {'email': email})

            if code != stored_code:
                error_message = _("Invalid reset code.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message})
                messages.error(request, error_message)
                return render(request, self.template_name, {'email': email})

            logger.info(f"✅ Password reset code verified for {email} (ID: {user.id})")
            success_message = _("Code verified! Please set your new password.")
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': success_message,
                    'redirect_url': reverse('users:password_reset', kwargs={'email': email})
                })
            messages.success(request, success_message)
            return redirect('users:password_reset', email=email)

        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Unexpected error during password reset verification for email {email}: {e}\n{trace}")
            error_message = _("An unexpected error occurred. Please try again later.")
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_message})
            messages.error(request, error_message)
            return render(request, self.template_name, {'email': email})


class PasswordResetView(TemplateView):
    """
    Name: PasswordResetView
    Description: Handles setting a new password after verification via AJAX.
                 Updates the user's password and logs them in.
                 Returns JSON responses for AJAX requests.
    Author: @ayemele
    """
    template_name = 'publics/auth/password_reset.html'

    def get(self, request: HttpRequest, email: str, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(request, self.template_name, {'email': email, 'error': None})

    def post(self, request: HttpRequest, email: str, *args: Any, **kwargs: Any) -> HttpResponse:
        password = request.POST.get("password", "").strip()
        password2 = request.POST.get("password2", "").strip()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            if not all([password, password2]):
                error_message = _("Both password fields are required.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message})
                messages.error(request, error_message)
                return render(request, self.template_name, {'email': email})

            if password != password2:
                error_message = _("Passwords do not match.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message})
                messages.error(request, error_message)
                return render(request, self.template_name, {'email': email})

            if len(password) < 8 or not re.search(r'\d', password) or not re.search(r'[A-Za-z]', password):
                error_message = _("Password must be at least 8 characters and contain at least one letter and one number.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message})
                messages.error(request, error_message)
                return render(request, self.template_name, {'email': email})

            user = User.objects.filter(email=email).first()
            if not user:
                error_message = _("No user found with this email.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message})
                messages.error(request, error_message)
                return render(request, self.template_name, {'email': email})

            with transaction.atomic():
                user.set_password(password)
                user.metadata.pop("reset_code", None)
                user.metadata.pop("reset_code_created_at", None)
                user.save()
                from django.contrib.auth import login
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            logger.info(f"✅ Password reset successfully for {email} (ID: {user.id})")
            success_message = _("Password reset successful! You are now logged in.")
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': success_message,
                    'redirect_url': reverse('users:home')
                })
            messages.success(request, success_message)
            return redirect('users:home')

        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Unexpected error during password reset for email {email}: {e}\n{trace}")
            error_message = _("An unexpected error occurred. Please try again later.")
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_message})
            messages.error(request, error_message)
            return render(request, self.template_name, {'email': email})