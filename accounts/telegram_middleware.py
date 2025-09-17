
from django.shortcuts import redirect
from django.contrib.auth import logout
import logging

logger = logging.getLogger(__name__)


class TelegramAuthMiddleware:
    """
    Middleware для проверки авторизации через Telegram
    Отключает стандартную авторизацию Django
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URL, которые доступны без авторизации
        self.exempt_urls = [
            '/admin/',
            '/management/',
            '/accounts/telegram-login/',
            '/accounts/telegram-auth/',
            '/accounts/telegram-connect/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/robots.txt',
            '/accounts/telegram-setup/',
            '/accounts/telegram-qr/',
            '/accounts/telegram-auth-status/',
        ]
    
    def __call__(self, request):
        # Проверяем, нужно ли проверять авторизацию
        if self.should_check_auth(request):
            # Проверяем, авторизован ли пользователь
            if not request.user.is_authenticated:
                # Если это AJAX запрос, возвращаем JSON ошибку
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({
                        'error': 'Требуется авторизация через Telegram',
                        'redirect': '/accounts/telegram-login/'
                    }, status=401)
                
                # Обычный запрос - редиректим на авторизацию
                return redirect('/accounts/telegram-login/')
            
            # Проверяем, есть ли у пользователя Telegram ID
            # Исключаем проверку для URL авторизации
            if (not request.path.startswith('/accounts/telegram-login/') and 
                not request.path.startswith('/accounts/telegram-auth/') and
                not request.path.startswith('/admin/') and
                not request.path.startswith('/management/') and
                not request.user.get_telegram_id()):
                telegram_id = request.user.get_telegram_id()
                logger.warning(f"Пользователь {request.user.email} не имеет Telegram ID. Полученный ID: {telegram_id}")
                logout(request)
                return redirect('/accounts/telegram-login/?error=no_telegram_id')
            
            # Проверяем привязку устройства для авторизованных пользователей
            if (not request.path.startswith('/accounts/telegram-login/') and 
                not request.path.startswith('/accounts/telegram-auth/') and
                not request.path.startswith('/admin/') and
                not request.path.startswith('/management/') and
                request.user.is_authenticated):
                
                # Получаем информацию об устройстве
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                ip_address = self.get_client_ip(request)
                
                # Проверяем, разрешено ли устройство
                if not request.user.is_device_allowed(user_agent, ip_address):
                    logger.warning(f"Попытка входа с неразрешенного устройства для пользователя {request.user.email}. IP: {ip_address}")
                    logout(request)
                    return redirect('/accounts/telegram-login/?error=device_not_allowed')
        
        response = self.get_response(request)
        return response
    
    def should_check_auth(self, request):
        """Определяет, нужно ли проверять авторизацию для данного запроса"""
        path = request.path
        
        # Проверяем exempt URLs
        for exempt_url in self.exempt_urls:
            if path.startswith(exempt_url):
                return False
        
        # Проверяем, не является ли это API запросом для Telegram
        if path.startswith('/accounts/telegram-auth/'):
            return False
        
        return True
    
    def get_client_ip(self, request):
        """Получает IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TelegramBotMiddleware:
    """
    Middleware для интеграции с Telegram ботом
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Добавляем информацию о Telegram в request
        if hasattr(request, 'user') and request.user.is_authenticated:
            telegram_id = request.user.get_telegram_id()
            request.telegram_id = telegram_id
            request.is_telegram_user = telegram_id is not None
        
        response = self.get_response(request)
        return response
