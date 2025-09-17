from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import path
from django.http import HttpResponseRedirect
from django.utils.html import format_html

from .models import User, TelegramUser, UserSession, ProjectAccessKey, LoginAttempt


class TelegramUserInline(admin.TabularInline):
    """Инлайн для Telegram пользователя"""
    model = TelegramUser
    extra = 0
    readonly_fields = ('telegram_id', 'username', 'first_name', 'last_name', 'created_at')
    fields = ('telegram_id', 'username', 'first_name', 'last_name', 'is_bot', 'language_code', 'created_at')


class UserAdmin(BaseUserAdmin):
    """Админка для пользователей с поддержкой Telegram"""
    inlines = [TelegramUserInline]
    
    list_display = ('get_full_name', 'telegram_id_display', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('first_name', 'last_name', 'telegramuser__telegram_id', 'telegramuser__username')
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Персональная информация'), {'fields': ('first_name', 'last_name', 'phone')}),
        (_('Telegram'), {'fields': ('telegram_id_display', 'telegram_link')}),
        (_('Роли и права'), {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        (_('Важные даты'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'role'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'telegram_id_display', 'telegram_link')
    
    def telegram_id_display(self, obj):
        """Отображает Telegram ID"""
        telegram_id = obj.get_telegram_id()
        if telegram_id:
            return format_html('<span style="color: #0066cc; font-weight: bold;">{}</span>', telegram_id)
        return format_html('<span style="color: #999;">Не привязан</span>')
    telegram_id_display.short_description = 'Telegram ID'
    
    def telegram_link(self, obj):
        """Кнопка для привязки Telegram"""
        telegram_id = obj.get_telegram_id()
        if telegram_id:
            return format_html(
                '<span style="color: #28a745;">✅ Привязан</span> | '
                '<a href="/admin/accounts/user/{}/telegram-unlink/" style="color: #dc3545;">Отвязать</a>',
                obj.id
            )
        else:
            return format_html(
                '<a href="/admin/accounts/user/{}/telegram-link/" style="background: #007cba; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">📱 Привязать Telegram</a>',
                obj.id
            )
    telegram_link.short_description = 'Telegram'
    
    def get_urls(self):
        """Добавляет дополнительные URL для админки"""
        urls = super().get_urls()
        custom_urls = [
            path('register-telegram-user/', self.register_telegram_user_view, name='register_telegram_user'),
            path('<int:user_id>/telegram-link/', self.telegram_link_view, name='telegram_link'),
            path('<int:user_id>/telegram-unlink/', self.telegram_unlink_view, name='telegram_unlink'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        """Добавляет кнопку регистрации Telegram пользователя"""
        extra_context = extra_context or {}
        extra_context['show_telegram_registration'] = True
        return super().changelist_view(request, extra_context)
    
    def register_telegram_user_view(self, request):
        """Представление для регистрации пользователя через Telegram"""
        if request.method == 'POST':
            try:
                # Получаем данные из формы
                telegram_id = request.POST.get('telegram_id')
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                role = request.POST.get('role')
                username = request.POST.get('username', '')
                
                # Проверяем, не существует ли уже пользователь с таким Telegram ID
                if TelegramUser.objects.filter(telegram_id=telegram_id).exists():
                    messages.error(request, f'Пользователь с Telegram ID {telegram_id} уже существует!')
                    return HttpResponseRedirect(request.path)
                
                # Создаем пользователя
                user = User.objects.create_user(
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    is_active=True
                )
                
                # Создаем связанную запись TelegramUser
                TelegramUser.objects.create(
                    user=user,
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    is_bot=False,
                    language_code='ru'
                )
                
                messages.success(request, f'Пользователь {user.get_full_name()} успешно зарегистрирован!')
                return redirect(f'/admin/accounts/user/{user.id}/change/')
                
            except Exception as e:
                messages.error(request, f'Ошибка при создании пользователя: {str(e)}')
        
        # Отображаем форму
        from django.shortcuts import render
        context = {
            'title': 'Регистрация пользователя через Telegram',
            'roles': User.Role.choices,
        }
        return render(request, 'admin/accounts/user/register_telegram_user.html', context)
    
    def telegram_link_view(self, request, user_id):
        """Представление для привязки Telegram к существующему пользователю"""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, 'Пользователь не найден!')
            return redirect('/admin/accounts/user/')
        
        if request.method == 'POST':
            try:
                telegram_id = request.POST.get('telegram_id')
                username = request.POST.get('username', '')
                
                # Проверяем, не привязан ли уже этот Telegram ID
                if TelegramUser.objects.filter(telegram_id=telegram_id).exists():
                    messages.error(request, f'Telegram ID {telegram_id} уже привязан к другому пользователю!')
                    return HttpResponseRedirect(request.path)
                
                # Проверяем, не привязан ли уже Telegram к этому пользователю
                if TelegramUser.objects.filter(user=user).exists():
                    messages.error(request, 'У этого пользователя уже есть привязанный Telegram аккаунт!')
                    return HttpResponseRedirect(request.path)
                
                # Создаем связь с Telegram
                TelegramUser.objects.create(
                    user=user,
                    telegram_id=telegram_id,
                    username=username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    is_bot=False,
                    language_code='ru'
                )
                
                messages.success(request, f'Telegram аккаунт успешно привязан к пользователю {user.get_full_name()}!')
                return redirect(f'/admin/accounts/user/{user.id}/change/')
                
            except Exception as e:
                messages.error(request, f'Ошибка при привязке Telegram: {str(e)}')
        
        # Отображаем форму
        from django.shortcuts import render
        context = {
            'title': f'Привязка Telegram к пользователю {user.get_full_name()}',
            'user': user,
        }
        return render(request, 'admin/accounts/user/telegram_link.html', context)
    
    def telegram_unlink_view(self, request, user_id):
        """Представление для отвязки Telegram от пользователя"""
        try:
            user = User.objects.get(id=user_id)
            telegram_user = TelegramUser.objects.get(user=user)
            telegram_user.delete()
            messages.success(request, f'Telegram аккаунт отвязан от пользователя {user.get_full_name()}!')
        except User.DoesNotExist:
            messages.error(request, 'Пользователь не найден!')
        except TelegramUser.DoesNotExist:
            messages.error(request, 'У пользователя нет привязанного Telegram аккаунта!')
        except Exception as e:
            messages.error(request, f'Ошибка при отвязке Telegram: {str(e)}')
        
        return redirect(f'/admin/accounts/user/{user_id}/change/')


class TelegramUserAdmin(admin.ModelAdmin):
    """Админка для Telegram пользователей"""
    list_display = ('telegram_id', 'user_link', 'username', 'full_name', 'is_bot', 'created_at')
    list_filter = ('is_bot', 'language_code', 'created_at')
    search_fields = ('telegram_id', 'username', 'first_name', 'last_name', 'user__email')
    readonly_fields = ('telegram_id', 'created_at')
    
    def user_link(self, obj):
        """Ссылка на пользователя"""
        if obj.user:
            url = f'/admin/accounts/user/{obj.user.id}/change/'
            return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
        return '-'
    user_link.short_description = 'Пользователь'
    
    def full_name(self, obj):
        """Полное имя"""
        return f"{obj.first_name} {obj.last_name}".strip() or '-'
    full_name.short_description = 'Полное имя'


class ProjectAccessKeyAdmin(admin.ModelAdmin):
    """Админка для ключей доступа к проектам"""
    list_display = ('key', 'project_id', 'created_by', 'is_active', 'expires_at', 'created_at')
    list_filter = ('is_active', 'expires_at', 'created_at')
    search_fields = ('key', 'project_id', 'created_by__email')
    readonly_fields = ('key', 'created_at')


class UserSessionAdmin(admin.ModelAdmin):
    """Админка для сессий пользователей"""
    list_display = ('user', 'session_key', 'device_info', 'ip_address', 'created_at', 'last_activity')
    list_filter = ('created_at', 'last_activity')
    search_fields = ('user__email', 'device_info', 'ip_address')
    readonly_fields = ('session_key', 'created_at', 'last_activity')


class LoginAttemptAdmin(admin.ModelAdmin):
    """Админка для попыток входа"""
    list_display = ('ip_address', 'user_agent', 'success', 'created_at')
    list_filter = ('success', 'created_at')
    search_fields = ('ip_address', 'user_agent')
    readonly_fields = ('created_at',)


# Регистрируем модели
admin.site.register(User, UserAdmin)
admin.site.register(TelegramUser, TelegramUserAdmin)
admin.site.register(ProjectAccessKey, ProjectAccessKeyAdmin)
admin.site.register(UserSession, UserSessionAdmin)
admin.site.register(LoginAttempt, LoginAttemptAdmin)
