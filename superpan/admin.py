from django.contrib import admin


class SuperPanAdminSite(admin.AdminSite):
    """Кастомная админка SuperPan"""
    
    site_header = "SuperPan - Администрирование"
    site_title = "SuperPan Admin"
    index_title = "Панель управления строительными проектами"
    
    def index(self, request, extra_context=None):
        """Кастомная главная страница админки с статистикой"""
        
        # Собираем статистику
        stats = {
            'users_count': User.objects.count(),
            'projects_count': Project.objects.count(),
            'expenses_count': ExpenseItem.objects.count(),
            'active_sessions': UserSession.objects.count(),
        }
        
        # Последние действия
        recent_logins = LoginAttempt.objects.filter(success=True).order_by('-created_at')[:5]
        recent_projects = Project.objects.order_by('-created_at')[:5]
        
        extra_context = extra_context or {}
        extra_context.update(stats)
        extra_context.update({
            'recent_logins': recent_logins,
            'recent_projects': recent_projects,
        })
        
        return super().index(request, extra_context)


# Создаем экземпляр кастомной админки
admin_site = SuperPanAdminSite(name='superpanadmin')
