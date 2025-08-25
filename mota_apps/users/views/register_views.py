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

class RegisterView(TemplateView):
    """
    Name: RegisterView
    Description: Handles user registration via standard form submission.
                 Uses transaction.atomic() to ensure all operations (user creation,
                 2FA code generation, email sending) are atomic. Sends a 2FA code
                 via email using Gmail SMTP with credentials from .env. Redirects to
                 2FA verification page on success. Uses ToastManager for error/success
                 messages. Logs errors with context.
    Author: @ayemele
    """
    template_name = 'publics/auth/register.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(request, self.template_name, {'error': None})

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        password2 = request.POST.get("password2", "").strip()
        terms_accepted = request.POST.get("terms_accepted", "")

        # Context to repopulate form on error
        context = {
            'error': None,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'terms_accepted': terms_accepted == "on"
        }

        try:
            # ===== VALIDATIONS =====
            if not all([first_name, last_name, email, password, password2]):
                messages.error(request, _("All fields are required."))
                return render(request, self.template_name, context)

            if terms_accepted != "on":
                messages.error(request, _("You must agree to the Terms of Service and Privacy Policy."))
                return render(request, self.template_name, context)

            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                messages.error(request, _("Invalid email format."))
                return render(request, self.template_name, context)

            if len(password) < 8 or not re.search(r'\d', password) or not re.search(r'[A-Za-z]', password):
                messages.error(request, _("Password must be at least 8 characters and contain at least one letter and one number."))
                return render(request, self.template_name, context)

            if password != password2:
                messages.error(request, _("Passwords do not match."))
                return render(request, self.template_name, context)

            if User.objects.filter(email=email).exists():
                messages.error(request, _("A user with this email already exists."))
                return render(request, self.template_name, context)

            # ===== ATOMIC TRANSACTION =====
            with transaction.atomic():
                # Create the user
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=False,  # User is inactive until 2FA verification
                    is_client=True,
                    has_accepted_terms=True
                )

                # Ensure metadata is a dictionary
                if not isinstance(user.metadata, dict):
                    user.metadata = {}

                # Generate and store 2FA code
                two_factor_code = get_random_string(6, allowed_chars='0123456789')
                user.metadata["two_factor_code"] = two_factor_code
                user.metadata["two_factor_code_created_at"] = timezone.now().isoformat()
                user.save()

                # Build 2FA email
                html_content = render_to_string(
                    template_name="publics/emails/two_factor_email.html",
                    context={
                        "user": user,
                        "two_factor_code": two_factor_code,
                        "site_name": "Mota Solutions"
                    }
                )

                email_message = EmailMessage(
                    subject="Your 2-Factor Authentication Code",
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

                # Send email (if this fails, transaction rolls back)
                email_message.send()

            logger.info(f"✅ User registered and 2FA code sent to {email} (ID: {user.id})")
            messages.success(request, _("Registration successful! Please check your email for the 2FA code."))
            return redirect('users:verify_2fa', email=email)

        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Unexpected error during registration for email {email}: {e}\n{trace}")
            messages.error(request, _("An unexpected error occurred. Please try again later."))
            return render(request, self.template_name, context)


class Verify2FAView(TemplateView):
    """
    Name: Verify2FAView
    Description: Handles 2FA code verification after registration.
                 Activates user account and logs them in on success.
                 Uses ToastManager for error/success messages.
    Author: @ayemele
    """
    template_name = 'publics/auth/verify_2fa.html'

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

            if not isinstance(user.metadata, dict) or "two_factor_code" not in user.metadata:
                messages.error(request, _("Invalid or expired 2FA code. Please register again."))
                return render(request, self.template_name, context)

            stored_code = user.metadata.get("two_factor_code")
            code_created_at = user.metadata.get("two_factor_code_created_at")
            if not stored_code or not code_created_at:
                messages.error(request, _("Invalid or expired 2FA code. Please register again."))
                return render(request, self.template_name, context)

            # Check if code is expired (e.g., 10 minutes)
            from datetime import datetime
            created_at = datetime.fromisoformat(code_created_at)
            if (timezone.now() - created_at).total_seconds() > 600:
                messages.error(request, _("2FA code has expired. Please register again."))
                return render(request, self.template_name, context)

            if code != stored_code:
                messages.error(request, _("Invalid 2FA code."))
                return render(request, self.template_name, context)

            # Activate user and clear 2FA code
            with transaction.atomic():
                user.is_active = True
                user.metadata.pop("two_factor_code", None)
                user.metadata.pop("two_factor_code_created_at", None)
                user.save()

            from django.contrib.auth import login
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            logger.info(f"✅ User {email} verified 2FA and logged in (ID: {user.id})")
            messages.success(request, _("2FA verification successful! You are now logged in."))
            return redirect('users:home')

        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Unexpected error during 2FA verification for email {email}: {e}\n{trace}")
            messages.error(request, _("An unexpected error occurred. Please try again later."))
            return render(request, self.template_name, context)