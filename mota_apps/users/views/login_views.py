import logging
import traceback
from typing import Any
from django.views.generic import TemplateView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

logger = logging.getLogger(__name__)

class LoginView(TemplateView):
    """
    Name: LoginView
    Description: Handles user login via standard form submission.
                 Authenticates users and ensures they are active.
                 Uses ToastManager for error/success messages.
                 Logs errors using try-except.
    Author: @ayemele
    """
    template_name = 'publics/auth/login.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(request, self.template_name, {'error': None, 'email': ''})

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        remember_me = request.POST.get("remember_me", "")

        context = {'error': None, 'email': email}

        try:
            if not email or not password:
                messages.error(request, _("Email and password are required."))
                return render(request, self.template_name, context)

            user = authenticate(request, email=email, password=password)
            if user is None:
                messages.error(request, _("Invalid email or password."))
                return render(request, self.template_name, context)

            if not user.is_active:
                messages.error(request, _("Please verify your account with the 2FA code sent to your email."))
                return render(request, self.template_name, context)

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            if remember_me != "on":
                request.session.set_expiry(0)  # Session expires on browser close
            logger.info(f"✅ User {email} logged in successfully (ID: {user.id})")
            messages.success(request, _("Login successful! Welcome back."))
            return redirect('users:home')

        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Unexpected error during login for email {email}: {e}\n{trace}")
            messages.error(request, _("An unexpected error occurred. Please try again later."))
            return render(request, self.template_name, context)