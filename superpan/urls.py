"""superpan URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from accounts.views import LoginView

# Кастомизация админки
admin.site.site_header = "Проектный Офис - Администрирование"
admin.site.site_title = "Проектный Офис - Админка"
admin.site.index_title = "Панель управления строительными проектами"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('management/', include('admin_panel.urls')),
    path('accounts/', include('accounts.urls')),
    path('projects/', include('projects.urls')),
    path('kanban/', include('kanban.urls')),
    path('warehouse/', include('warehouse.urls')),
    path('api/', include('api.urls')),
    
    # API Documentation
    path('api/schema/', include('drf_spectacular.urls')),
    path('api/docs/', TemplateView.as_view(
        template_name='drf_spectacular/swagger_ui.html',
        extra_context={'schema_url': 'api:schema'}
    ), name='swagger-ui'),
    path('api/redoc/', TemplateView.as_view(
        template_name='drf_spectacular/redoc.html',
        extra_context={'schema_url': 'api:schema'}
    ), name='redoc'),
    
    path('app/', TemplateView.as_view(template_name='react_app.html'), name='react_app'),
    path('', LoginView.as_view(), name='login'),  # Root redirects to login
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
