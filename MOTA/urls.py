from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import JavaScriptCatalog

urlpatterns = [
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript_catalog'),
    path('admin/', admin.site.urls),
    path("", include("mota_apps.users.urls", namespace="users")),
    path("", include("mota_apps.finance.urls", namespace="finance")),
] + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
