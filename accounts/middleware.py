from django.utils.deprecation import MiddlewareMixin
from .models import UserSession
import logging

logger = logging.getLogger(__name__)


class DeviceTrackingMiddleware(MiddlewareMixin):
    """Middleware для отслеживания устройств и сессий"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Исключаем эти URL из проверки
        self.excluded_paths = [
            '/accounts/login/',
            '/accounts/logout/',
            '/admin/',
            '/static/',
            '/media/',
        ]
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        # Пропускаем неавторизованных пользователей и исключенные пути
        if not request.user.is_authenticated:
            return None
            
        # Проверяем исключенные пути
        for path in self.excluded_paths:
            if request.path.startswith(path):
                return None
        
        # Получаем информацию о текущем запросе
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = self.get_client_ip(request)
        
        try:
            # Проверяем привязку к устройству
            if not request.user.is_device_allowed(user_agent, ip_address):
                # Логируем попытку доступа с нового устройства
                logger.info(
                    f"New device access attempt: {request.user.email} "
                    f"from {ip_address} with agent {user_agent[:100]}"
                )
                
                # Если у пользователя нет привязанного устройства, привязываем новое
                if not request.user.device_fingerprint:
                    request.user.bind_device(user_agent, ip_address)
                    logger.info(f"Device bound for user {request.user.email}")
                else:
                    # Устройство не совпадает, но разрешаем доступ с предупреждением
                    logger.warning(f"Device mismatch for user {request.user.email}, but allowing access")
                    messages.warning(
                        request, 
                        'Вход с нового устройства. Если это не вы, обратитесь к администратору.'
                    )
            
            # Обновляем или создаем сессию пользователя
            session_key = request.session.session_key
            if session_key:
                user_session, created = UserSession.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'session_key': session_key,
                        'device_info': user_agent,
                        'ip_address': ip_address,
                    }
                )
                
                if not created:
                    # Обновляем время последней активности
                    user_session.last_activity = timezone.now()
                    user_session.save(update_fields=['last_activity'])
                    
                    # Проверяем, не изменились ли IP или User-Agent
                    if (user_session.ip_address != ip_address or 
                        user_session.device_info != user_agent):
                        
                        logger.warning(
                            f"Device info changed for user {request.user.email}: "
                            f"IP {user_session.ip_address} -> {ip_address}, "
                            f"Agent changed: {user_session.device_info != user_agent}"
                        )
                        
                        # Обновляем информацию об устройстве
                        user_session.ip_address = ip_address
                        user_session.device_info = user_agent
                        user_session.save(update_fields=['ip_address', 'device_info'])
        
        except Exception as e:
            logger.error(f"Error in DeviceTrackingMiddleware: {e}", exc_info=True)
            # В случае ошибки не блокируем доступ, но логируем для отладки
            pass
        
        return None
    
    def get_client_ip(self, request):
        """Получает реальный IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SessionSecurityMiddleware(MiddlewareMixin):
    """Middleware для дополнительной безопасности сессий"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Время неактивности в секундах (30 минут)
        self.session_timeout = 30 * 60
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        if not request.user.is_authenticated:
            return None
        
        # Проверяем время последней активности
        try:
            user_session = UserSession.objects.filter(
                user=request.user,
                session_key=request.session.session_key
            ).first()
            
            if user_session:
                # Проверяем, не истекла ли сессия
                time_since_activity = timezone.now() - user_session.last_activity
                
                if time_since_activity.total_seconds() > self.session_timeout:
                    # Сессия истекла
                    user_session.delete()
                    logout(request)
                    messages.warning(
                        request, 
                        'Ваша сессия истекла из-за длительного бездействия. '
                        'Войдите в систему повторно.'
                    )
                    return redirect('accounts:telegram_login')
        
        except Exception as e:
            logger.error(f"Error in SessionSecurityMiddleware: {e}", exc_info=True)
        
        return None


class SingleSessionMiddleware(MiddlewareMixin):
    """Middleware для обеспечения единственной активной сессии"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        if not request.user.is_authenticated:
            return None
        
        try:
            current_session_key = request.session.session_key
            if not current_session_key:
                return None
            
            # Проверяем, есть ли другие активные сессии этого пользователя
            other_sessions = UserSession.objects.filter(
                user=request.user
            ).exclude(session_key=current_session_key)
            
            if other_sessions.exists():
                # Удаляем все другие сессии
                other_sessions.delete()
                logger.info(f"Removed {other_sessions.count()} other sessions for user {request.user.email}")
        
        except Exception as e:
            logger.error(f"Error in SingleSessionMiddleware: {e}", exc_info=True)
        
        return None