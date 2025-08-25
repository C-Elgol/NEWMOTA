import traceback
from typing import Any
from django.views.generic import View
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

class LogoutView(View):
    """
    Name: LogoutView
    Description: Handles user logout and redirects to the home page.
                 Uses ToastManager for success message.
    Author: @ayemele
    """
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            user_email = request.user.email if request.user.is_authenticated else "anonymous"
            logout(request)
            logger.info(f"✅ User {user_email} logged out successfully")
            messages.success(request, _("You have been logged out successfully."))
            return redirect('users:home')
        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Unexpected error during logout for {user_email}: {e}\n{trace}")
            messages.error(request, _("An unexpected error occurred. Please try again later."))
            return redirect('users:home')