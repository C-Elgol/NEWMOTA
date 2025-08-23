import re
import logging
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)

class LoginView(TemplateView):
    """
    Name: LoginView
    Description: Handles user login via standard form submission.
                 Renders errors in the template and redirects to home on success.
                 Logs errors using try-except.
    Author: @ayemele
    """
    template_name = 'publics/auth/login.html'