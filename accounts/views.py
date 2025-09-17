from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
import logging

from .models import User, UserSession, ProjectAccessKey, LoginAttempt
from .forms import LoginForm, UserRegistrationForm, ProfileForm

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Получает реальный IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='post')
class LoginView(View):
    """Представление для входа в систему с rate limiting"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('projects:dashboard')
        
        form = LoginForm()
        return render(request, 'accounts/login.html', {'form': form})
    
    def post(self, request):
        form = LoginForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Проверяем блокировку по IP
            recent_failures = LoginAttempt.objects.filter(
                ip_address=ip_address,
                success=False,
                created_at__gte=timezone.now() - timedelta(minutes=15)
            ).count()
            
            if recent_failures >= 5:
                messages.error(request, 'Слишком много неудачных попыток. Попробуйте позже.')
                return render(request, 'accounts/login.html', {'form': form})
            
            # Аутентификация
            logger.info(f"Attempting authentication for email: {email}")
            user = authenticate(request, username=email, password=password)
            logger.info(f"Authentication result: {user}")
            
            if user is not None:
                if user.is_active:
                    # Привязываем устройство при первом входе (если еще не привязано)
                    if not user.device_fingerprint:
                        user.bind_device(user_agent, ip_address)
                        logger.info(f"Device bound for user {user.email}")
                    
                    # Аутентифицируем пользователя
                    login(request, user)
                    
                    # Создаем или обновляем сессию после логина
                    UserSession.objects.filter(user=user).delete()  # Удаляем старые сессии
                    
                    # Теперь session_key точно существует после login()
                    if request.session.session_key:
                        try:
                            UserSession.objects.create(
                                user=user,
                                session_key=request.session.session_key,
                                device_info=user_agent,
                                ip_address=ip_address
                            )
                        except Exception as e:
                            # Если все равно ошибка, просто логируем
                            logger.error(f"Error creating UserSession: {e}")
                    
                    # Логируем успешный вход
                    LoginAttempt.objects.create(
                        email=email,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=True
                    )
                    
                    messages.success(request, f'Добро пожаловать, {user.get_full_name()}!')
                    return redirect('projects:dashboard')
                else:
                    messages.error(request, 'Ваш аккаунт деактивирован.')
            else:
                # Логируем неудачную попытку
                LoginAttempt.objects.create(
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    failure_reason='invalid_credentials'
                )
                messages.error(request, 'Неверный email или пароль.')
        
        return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Выход из системы"""
    # Удаляем сессию пользователя
    UserSession.objects.filter(user=request.user).delete()
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('accounts:telegram_login')


@login_required
def profile_view(request):
    """Профиль пользователя"""
    if request.method == 'POST':
        form_type = request.POST.get('form_type', '')
        
        # Проверяем, не является ли это запросом на использование ключа доступа
        if form_type == 'access_key' or ('access_key' in request.POST and form_type != 'profile'):
            # Перенаправляем на обработку ключа доступа
            return use_access_key(request)
        
        # Обрабатываем форму профиля
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    
    # Статистика пользователя
    user_stats = {
        'created_projects': request.user.created_projects.count(),
        'managed_projects': request.user.managed_projects.count() if hasattr(request.user, 'managed_projects') else 0,
        'created_expenses': request.user.created_expense_items.count(),
        'project_memberships': request.user.assigned_access_keys.filter(is_active=True).count(),
        'last_login': request.user.last_login,
        'date_joined': request.user.created_at,
    }
    
    return render(request, 'accounts/profile.html', {
        'form': form,
        'user_stats': user_stats
    })


def register_view(request):
    """Регистрация нового пользователя (только для суперпользователей)"""
    if not (request.user.is_authenticated and request.user.is_admin_role()):
        messages.error(request, 'У вас нет прав для регистрации новых пользователей.')
        return redirect('accounts:telegram_login')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Пользователь "{user.get_full_name()}" успешно зарегистрирован.')
            return redirect('admin_panel:users_list')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@login_required
@ratelimit(key='ip', rate='20/h', method='POST', block=True)
def use_access_key(request):
    """Использование ключа доступа к проекту"""
    if request.method == 'POST':
        # Логируем только безопасную информацию
        logger.info(f"User {request.user.email} attempting to use access key")
        logger.debug(f"Request method: {request.method}, Content type: {request.content_type}")
        
        # Дополнительное логирование для отладки
        logger.info(f"POST data: {dict(request.POST)}")
        logger.info(f"POST keys: {list(request.POST.keys())}")
        logger.info(f"Raw POST body: {request.body}")
        
        # Обрабатываем JSON запросы
        if request.content_type == 'application/json':
            try:
                import json
                data = json.loads(request.body)
                key = data.get('key', '').strip()
                form_type = 'access_key'  # JSON запросы всегда для ключей доступа
                logger.info(f"JSON request - key: {key}, form_type: {form_type}")
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"Error parsing JSON: {e}")
                messages.error(request, 'Ошибка в данных запроса.')
                return redirect('accounts:profile')
        else:
            # Обрабатываем обычные формы
            form_type = request.POST.get('form_type', '')
            key = request.POST.get('access_key', '').strip()
            logger.info(f"Form request - form_type: '{form_type}', key: {key}")
            
            # Если form_type пустой, но есть access_key, считаем это валидным запросом
            if not form_type and key:
                logger.info("Form type is empty but access_key present, treating as valid access key request")
                form_type = 'access_key'
        
        if form_type != 'access_key':
            logger.warning(f"Invalid form type: '{form_type}'")
            messages.error(request, 'Неверный тип формы.')
            return redirect('accounts:profile')
        
        logger.info(f"User {request.user.email} attempting to use access key (length: {len(key)})")
        
        if not key:
            messages.error(request, 'Введите ключ доступа.')
            return redirect('accounts:profile')
        
        # Валидация UUID формата
        import uuid
        try:
            uuid.UUID(key)
        except ValueError:
            messages.error(request, 'Неверный формат ключа доступа. Ключ должен быть в формате UUID.')
            return redirect('accounts:profile')
        
        try:
            access_key = ProjectAccessKey.objects.get(key=key)
            logger.info(f"Access key found: {access_key.key}, is_valid: {access_key.is_valid()}")
            
            # Проверяем валидность ключа
            if not access_key.is_valid():
                logger.info(f"Access key is invalid: is_active={access_key.is_active}, expires_at={access_key.expires_at}")
                messages.error(request, 'Ключ доступа недействителен или истек.')
                return redirect('accounts:profile')
            
            # Проверяем, не назначен ли уже ключ другому пользователю
            if access_key.assigned_to and access_key.assigned_to != request.user:
                messages.error(request, 'Этот ключ доступа уже используется другим пользователем.')
                return redirect('accounts:profile')
            
            # Назначаем ключ пользователю
            if not access_key.assigned_to:
                access_key.assigned_to = request.user
                access_key.used_at = timezone.now()
                access_key.save()
                logger.info(f"Access key {access_key.key} assigned to user {request.user.email}")
            else:
                logger.info(f"Access key {access_key.key} already assigned to user {request.user.email}")
            
            # Получаем проект по project_id
            from projects.models import Project
            try:
                project = Project.objects.get(id=access_key.project_id)
                logger.info(f"Project found: {project.name}, redirecting to detail page")
                messages.success(request, f'Доступ к проекту "{project.name}" успешно получен!')
                return redirect('projects:detail', pk=project.pk)
            except Project.DoesNotExist:
                messages.error(request, 'Проект не найден.')
                return redirect('accounts:profile')
                
        except ProjectAccessKey.DoesNotExist:
            logger.warning(f"Access key not found: {key}")
            messages.error(request, 'Ключ доступа не найден.')
            return redirect('accounts:profile')
        except Project.DoesNotExist:
            logger.error(f"Project not found for key: {key}")
            messages.error(request, 'Проект не найден.')
            return redirect('accounts:profile')
        except Exception as e:
            logger.error(f"Unexpected error in use_access_key: {e}", exc_info=True)
            messages.error(request, 'Произошла внутренняя ошибка. Попробуйте позже.')
            return redirect('accounts:profile')
    
    return redirect('accounts:profile')


@login_required
@ratelimit(key='ip', rate='10/h', method='POST', block=True)
@require_http_methods(["POST"])
def reset_device_binding(request):
    """Сброс привязки к устройству (только для суперпользователей)"""
    if not request.user.is_admin_role():
        return JsonResponse({'error': 'Недостаточно прав'}, status=403)
    
    user_id = request.POST.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'ID пользователя не указан'}, status=400)
    
    try:
        user = User.objects.get(pk=user_id)
        user.device_fingerprint = ''
        user.save(update_fields=['device_fingerprint'])
        
        # Удаляем все активные сессии пользователя
        UserSession.objects.filter(user=user).delete()
        
        return JsonResponse({'success': True, 'message': 'Привязка к устройству сброшена'})
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден'}, status=404)
    except Exception as e:
        logger.error(f"Ошибка при сбросе привязки устройства: {e}", exc_info=True)
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)


@login_required
def user_activity(request):
    """Активность пользователя"""
    # Последние входы пользователя
    recent_logins = LoginAttempt.objects.filter(
        email=request.user.email
    ).order_by('-created_at')[:10]
    
    # Активные сессии
    active_sessions = UserSession.objects.filter(
        user=request.user
    ).order_by('-last_activity')
    
    # Статистика по проектам
    from projects.models import ProjectActivity
    recent_activities = ProjectActivity.objects.filter(
        user=request.user
    ).select_related('project').order_by('-created_at')[:20]
    
    context = {
        'recent_logins': recent_logins,
        'active_sessions': active_sessions,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'accounts/activity.html', context)


@login_required
def role_info_view(request):
    """Страница с информацией о ролях и правах доступа"""
    # Доступ только для суперпользователей
    if not request.user.is_superuser:
        messages.error(request, 'Доступ запрещен. Только суперпользователи могут просматривать информацию о ролях.')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/role_info.html')