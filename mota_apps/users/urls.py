from django.db import router
from django.urls import path
from mota_apps.users.views import user_view
from mota_apps.users.views.home_views import HomeView
from mota_apps.users.views.login_views import LoginView
from mota_apps.users.views.logout_views import LogoutView
from mota_apps.users.views.password_reset_views import PasswordResetRequestView, PasswordResetVerifyView, PasswordResetView
from mota_apps.users.views.register_views import RegisterView, Verify2FAView


app_name = 'users'
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-2fa/<str:email>/', Verify2FAView.as_view(), name='verify_2fa'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/verify/<str:email>/', PasswordResetVerifyView.as_view(), name='password_reset_verify'),
    path('password-reset/reset/<str:email>/', PasswordResetView.as_view(), name='password_reset'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('users', user_view.UserListView.as_view(), name='user_list'),
    path('new/', user_view.NewUserView.as_view(), name='new_user'),
    path('update/<uuid:pk>/', user_view.UpdateUserView.as_view(), name='update_user'),
    path('delete/<uuid:pk>/', user_view.DeleteUserView.as_view(), name='delete_user'),
    path('detail/<uuid:pk>/', user_view.UserDetailView.as_view(), name='user_detail'),
]
