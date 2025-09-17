#!/usr/bin/env python
"""
Отдельный скрипт для запуска Telegram бота
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'superpan.settings')
django.setup()

from telegram_bot.bot import ConstructionBot

if __name__ == '__main__':
    print("Запуск Telegram бота...")
    try:
        bot = ConstructionBot()
        bot.run()
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
    except Exception as e:
        print(f"Ошибка запуска бота: {e}")
        import traceback
        traceback.print_exc()
