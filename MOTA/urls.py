from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import JavaScriptCatalog

urlpatterns = [
    # Language switching endpoint
    path('i18n/', include('django.conf.urls.i18n')),
    # JavaScript translations
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript_catalog'),
] + i18n_patterns(
    # Admin URLs
    path('admin/', admin.site.urls),
    # App URLs with namespaces
    path('', include('mota_apps.users.urls', namespace='users')),
    path('', include('mota_apps.finance.urls', namespace='finance')),
    path('', include('mota_apps.agents.urls')),
    # Add prefix_untranslated=True if you want these URLs to be accessible without a language prefix
) + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT)