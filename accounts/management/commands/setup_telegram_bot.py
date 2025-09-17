from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json


class Command(BaseCommand):
    help = 'Настройка Telegram бота для авторизации'

    def add_arguments(self, parser):
        parser.add_argument('--token', type=str, help='Telegram Bot Token')
        parser.add_argument('--username', type=str, help='Telegram Bot Username')

    def handle(self, *args, **options):
        token = options.get('token')
        username = options.get('username')
        
        if not token or not username:
            self.stdout.write(
                self.style.ERROR('Необходимо указать --token и --username')
            )
            self.stdout.write('Пример: python manage.py setup_telegram_bot --token YOUR_TOKEN --username YOUR_BOT_USERNAME')
            return
        
        # Проверяем токен
        try:
            response = requests.get(f'https://api.telegram.org/bot{token}/getMe')
            if response.status_code == 200:
                bot_info = response.json()
                self.stdout.write(
                    self.style.SUCCESS(f'Бот найден: {bot_info["result"]["first_name"]} (@{bot_info["result"]["username"]})')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Неверный токен бота')
                )
                return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка проверки бота: {e}')
            )
            return
        
        # Обновляем настройки
        self.stdout.write('Обновите настройки в .env файле:')
        self.stdout.write(f'TELEGRAM_BOT_TOKEN={token}')
        self.stdout.write(f'TELEGRAM_BOT_USERNAME={username}')
        
        # Проверяем webhook
        try:
            webhook_url = f'{settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "localhost:8000"}/accounts/telegram/login/'
            self.stdout.write(f'Webhook URL: {webhook_url}')
            self.stdout.write('Убедитесь, что ваш сервер доступен по HTTPS для работы webhook')
        except Exception as e:
            self.stdout.write(f'Ошибка настройки webhook: {e}')
        
        self.stdout.write(
            self.style.SUCCESS('Настройка завершена! Перезапустите сервер.')
        )
