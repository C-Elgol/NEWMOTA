import logging
from typing import Any
from django.views.generic import TemplateView
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.urls import reverse

logger = logging.getLogger(__name__)

class LoginView(TemplateView):
    """
    Name: LoginView
    Description: Handles user login via AJAX form submission.
                 Authenticates users and ensures they are active.
                 Returns JSON responses for AJAX requests.
    Author: @ayemele
    """
    template_name = 'publics/auth/login.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(request, self.template_name, {'error': None, 'email': ''})

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        remember_me = request.POST.get("remember_me", "")

        # Fields to return in case of error
        fields = {'email': email}

        # Check if request is AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            if not all([email, password]):
                error_message = _("Email and password are required.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message, 'fields': fields})
                messages.error(request, error_message)
                return render(request, self.template_name, fields)

            user = authenticate(request, email=email, password=password)
            if user is None:
                error_message = _("Invalid email or password.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message, 'fields': fields})
                messages.error(request, error_message)
                return render(request, self.template_name, fields)

            if not user.is_active:
                error_message = _("Your account is not activated. Please verify your email.")
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message, 'fields': fields})
                messages.error(request, error_message)
                return render(request, self.template_name, fields)

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            if remember_me != "on":
                request.session.set_expiry(0)  # Session expires when browser closes

            logger.info(f"✅ User {email} logged in successfully (ID: {user.id})")
            success_message = _("Login successful! Welcome back.")
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': success_message,
                    'redirect_url': reverse('users:home')
                })
            messages.success(request, success_message)
            return redirect('users:home')

        except Exception as e:
            logger.error(f"Unexpected error during login for email {email}: {e}")
            error_message = _("An unexpected error occurred. Please try again later.")
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_message, 'fields': fields})
            messages.error(request, error_message)
            return render(request, self.template_name, fields)