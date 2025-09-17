"""superpan URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
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
    
    # API Documentation - временно отключено
    # path('api/schema/', include('drf_spectacular.urls')),
    
    path('app/', TemplateView.as_view(template_name='react_app.html'), name='react_app'),
    path('', RedirectView.as_view(url='/accounts/telegram-login/', permanent=False), name='home'),  # Перенаправление на авторизацию
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
