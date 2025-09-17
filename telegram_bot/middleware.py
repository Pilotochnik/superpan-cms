import hmac
import hashlib
import logging
import time
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

logger = logging.getLogger(__name__)


class TelegramWebhookSecurityMiddleware(MiddlewareMixin):
    """
    Middleware для проверки подписи Telegram webhook запросов
    Включает защиту от replay атак и проверку HMAC подписи
    """

    def process_request(self, request):
        # Проверяем только webhook endpoints
        if not request.path.startswith('/telegram/webhook/'):
            return None

        # Получаем тело запроса для проверки HMAC
        request_body = request.body
        
        # Получаем заголовки
        telegram_signature = request.META.get('HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN')
        telegram_init_data = request.META.get('HTTP_X_TELEGRAM_INIT_DATA')
        
        # Проверяем секретный токен
        webhook_secret = getattr(settings, 'TELEGRAM_WEBHOOK_SECRET', None)
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        
        if not webhook_secret or not bot_token:
            logger.error("TELEGRAM_WEBHOOK_SECRET или TELEGRAM_BOT_TOKEN не настроены")
            return HttpResponseForbidden("Webhook not configured")

        # Проверка 1: Secret Token (простая проверка)
        if telegram_signature and telegram_signature != webhook_secret:
            logger.warning(f"Неверный secret token: {telegram_signature}")
            return HttpResponseForbidden("Invalid secret token")

        # Проверка 2: HMAC подпись (более надежная)
        if telegram_init_data:
            if not self._verify_telegram_webhook_data(telegram_init_data, bot_token):
                logger.warning("Неверная HMAC подпись Telegram webhook")
                return HttpResponseForbidden("Invalid HMAC signature")

        # Проверка 3: Защита от replay атак
        if not self._check_replay_protection(request_body, telegram_signature):
            logger.warning("Обнаружена попытка replay атаки")
            return HttpResponseForbidden("Replay attack detected")

        # Проверка 4: Rate limiting
        client_ip = self._get_client_ip(request)
        if not self._check_rate_limit(client_ip):
            logger.warning(f"Rate limit превышен для IP: {client_ip}")
            return HttpResponseForbidden("Rate limit exceeded")

        logger.info("Telegram webhook проверен успешно")
        return None

    def _verify_telegram_webhook_data(self, init_data, bot_token):
        """
        Проверка HMAC подписи Telegram webhook данных
        """
        try:
            # Парсим данные
            data_check_string, received_hash = init_data.rsplit('&hash=', 1)
            
            # Создаем секретный ключ
            secret_key = hmac.new(
                b"WebAppData", 
                bot_token.encode(), 
                hashlib.sha256
            ).digest()
            
            # Вычисляем HMAC
            calculated_hash = hmac.new(
                secret_key, 
                data_check_string.encode(), 
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(calculated_hash, received_hash)
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Ошибка проверки HMAC: {e}")
            return False

    def _check_replay_protection(self, request_body, signature):
        """
        Защита от replay атак
        """
        try:
            # Создаем уникальный ключ для запроса
            request_hash = hashlib.sha256(
                (request_body.decode('utf-8') + str(signature)).encode()
            ).hexdigest()
            
            # Проверяем, не был ли этот запрос уже обработан
            cache_key = f"telegram_webhook_{request_hash}"
            if cache.get(cache_key):
                return False
            
            # Сохраняем запрос на 5 минут
            cache.set(cache_key, True, timeout=300)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка replay защиты: {e}")
            return False

    def _check_rate_limit(self, client_ip):
        """
        Проверка rate limiting
        """
        try:
            cache_key = f"telegram_rate_limit_{client_ip}"
            requests_count = cache.get(cache_key, 0)
            
            # Максимум 10 запросов в минуту
            if requests_count >= 10:
                return False
            
            # Увеличиваем счетчик
            cache.set(cache_key, requests_count + 1, timeout=60)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка rate limiting: {e}")
            return True  # В случае ошибки разрешаем запрос

    def _get_client_ip(self, request):
        """
        Получение IP адреса клиента
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
