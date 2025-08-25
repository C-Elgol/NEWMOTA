from django.db import router
from django.urls import path
from mota_apps.users.views.home_views import HomeView
from mota_apps.users.views.login_views import LoginView
from mota_apps.users.views.register_views import RegisterView, Verify2FAView


app_name = 'users'
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-2fa/<str:email>/', Verify2FAView.as_view(), name='verify_2fa'),
]
