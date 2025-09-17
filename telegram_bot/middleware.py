import hmac
import hashlib
import logging
from django.http import HttpResponseForbidden
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class TelegramWebhookSecurityMiddleware(MiddlewareMixin):
    """
    Middleware для проверки подписи Telegram webhook запросов
    """
    
    def process_request(self, request):
        # Проверяем только webhook endpoints
        if not request.path.startswith('/telegram/webhook/'):
            return None
            
        # Получаем заголовок с подписью
        telegram_signature = request.META.get('HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN')
        
        if not telegram_signature:
            logger.warning("Telegram webhook без подписи")
            return HttpResponseForbidden("Missing signature")
        
        # Получаем секретный токен из настроек
        webhook_secret = getattr(settings, 'TELEGRAM_WEBHOOK_SECRET', None)
        
        if not webhook_secret:
            logger.error("TELEGRAM_WEBHOOK_SECRET не настроен")
            return HttpResponseForbidden("Webhook secret not configured")
        
        # Проверяем подпись
        if telegram_signature != webhook_secret:
            logger.warning(f"Неверная подпись Telegram webhook: {telegram_signature}")
            return HttpResponseForbidden("Invalid signature")
        
        logger.info("Telegram webhook подпись проверена успешно")
        return None
