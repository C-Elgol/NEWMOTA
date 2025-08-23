from django.db import router
from django.urls import path

from mota_apps.users.views.home_views import HomeView




app_name = 'users'
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
]
