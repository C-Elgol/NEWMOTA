from django.views.generic import TemplateView
import logging

logger = logging.getLogger(__name__)

class HomeView(TemplateView):
    template_name = "publics/home/home.html"