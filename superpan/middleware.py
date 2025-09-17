import logging
import time
import traceback
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)


class ErrorLoggingMiddleware(MiddlewareMixin):
    """
    Middleware для логирования ошибок и мониторинга производительности
    """
    
    def process_request(self, request):
        """Начало обработки запроса"""
        request.start_time = time.time()
        logger.info(f"Request started: {request.method} {request.path}")
        return None
    
    def process_response(self, request, response):
        """Окончание обработки запроса"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(f"Request completed: {request.method} {request.path} - {response.status_code} ({duration:.3f}s)")
        return response
    
    def process_exception(self, request, exception):
        """Обработка исключений"""
        duration = time.time() - getattr(request, 'start_time', time.time())
        
        # Логируем исключение
        logger.error(
            f"Exception in {request.method} {request.path}: {str(exception)} "
            f"({duration:.3f}s)",
            exc_info=True,
            extra={
                'request_path': request.path,
                'request_method': request.method,
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'remote_addr': request.META.get('REMOTE_ADDR', ''),
            }
        )
        
        # В режиме отладки возвращаем подробную ошибку
        if settings.DEBUG:
            return JsonResponse({
                'error': str(exception),
                'traceback': traceback.format_exc(),
                'path': request.path,
                'method': request.method,
            }, status=500)
        
        # В продакшене возвращаем общую ошибку
        return JsonResponse({
            'error': 'Internal server error',
            'path': request.path,
        }, status=500)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware для добавления security headers
    """
    
    def process_response(self, request, response):
        """Добавляем security headers"""
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "accelerometer=(), "
            "gyroscope=()"
        )
        
        return response
