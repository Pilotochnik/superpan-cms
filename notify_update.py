#!/usr/bin/env python
"""
Скрипт для отправки уведомлений об обновлениях SuperPan
"""

import os
import sys
import requests
import json
from datetime import datetime

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'superpan.settings')
import django
django.setup()

from django.conf import settings


def send_telegram_notification(message, chat_id=None):
    """Отправляет уведомление в Telegram"""
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not bot_token:
        print("TELEGRAM_BOT_TOKEN не настроен")
        return False
    
    # Используем переданный chat_id или берем из настроек
    if not chat_id:
        chat_id = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', None)
    
    if not chat_id:
        print("TELEGRAM_ADMIN_CHAT_ID не настроен")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print(f"Уведомление отправлено в Telegram (chat_id: {chat_id})")
            return True
        else:
            print(f"Ошибка отправки в Telegram: {response.status_code}")
            return False
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return False


def send_update_notification(update_type, status, details=""):
    """Отправляет уведомление об обновлении"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if status == "started":
        message = f"""
🔄 <b>Начато обновление SuperPan</b>

📅 Время: {timestamp}
🔧 Тип: {update_type}
📋 Детали: {details}

⏳ Система будет недоступна несколько минут.
        """
    elif status == "completed":
        message = f"""
✅ <b>Обновление SuperPan завершено</b>

📅 Время: {timestamp}
🔧 Тип: {update_type}
📋 Детали: {details}

🌐 Система снова доступна.
        """
    elif status == "failed":
        message = f"""
❌ <b>Ошибка обновления SuperPan</b>

📅 Время: {timestamp}
🔧 Тип: {update_type}
📋 Детали: {details}

🚨 Требуется вмешательство администратора.
        """
    else:
        message = f"""
ℹ️ <b>Уведомление SuperPan</b>

📅 Время: {timestamp}
🔧 Тип: {update_type}
📋 Детали: {details}
        """
    
    return send_telegram_notification(message.strip())


def send_maintenance_notification(start_time, end_time, reason=""):
    """Отправляет уведомление о технических работах"""
    message = f"""
🔧 <b>Технические работы SuperPan</b>

📅 Начало: {start_time}
📅 Окончание: {end_time}
📋 Причина: {reason or "Плановое обслуживание"}

⏳ Система будет недоступна в указанное время.
    """
    
    return send_telegram_notification(message.strip())


def send_error_notification(error_type, error_details, severity="medium"):
    """Отправляет уведомление об ошибке"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    severity_emoji = {
        "low": "ℹ️",
        "medium": "⚠️", 
        "high": "🚨",
        "critical": "💥"
    }
    
    emoji = severity_emoji.get(severity, "⚠️")
    
    message = f"""
{emoji} <b>Ошибка SuperPan</b>

📅 Время: {timestamp}
🔧 Тип: {error_type}
📊 Критичность: {severity.upper()}
📋 Детали: {error_details}
    """
    
    return send_telegram_notification(message.strip())


def send_backup_notification(backup_type, status, details=""):
    """Отправляет уведомление о резервном копировании"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if status == "completed":
        message = f"""
💾 <b>Резервное копирование завершено</b>

📅 Время: {timestamp}
🔧 Тип: {backup_type}
📋 Детали: {details}

✅ Данные сохранены.
        """
    elif status == "failed":
        message = f"""
❌ <b>Ошибка резервного копирования</b>

📅 Время: {timestamp}
🔧 Тип: {backup_type}
📋 Детали: {details}

🚨 Требуется проверка системы резервного копирования.
        """
    else:
        message = f"""
💾 <b>Резервное копирование</b>

📅 Время: {timestamp}
🔧 Тип: {backup_type}
📋 Детали: {details}
        """
    
    return send_telegram_notification(message.strip())


def main():
    """Главная функция для CLI использования"""
    if len(sys.argv) < 3:
        print("Использование:")
        print("  python notify_update.py update started manual")
        print("  python notify_update.py update completed manual")
        print("  python notify_update.py update failed 'Ошибка миграций'")
        print("  python notify_update.py maintenance '2024-01-01 02:00' '2024-01-01 03:00' 'Плановое обновление'")
        print("  python notify_update.py error 'DatabaseError' 'Ошибка подключения к БД' high")
        print("  python notify_update.py backup completed 'Автоматический бэкап'")
        sys.exit(1)
    
    notification_type = sys.argv[1]
    
    if notification_type == "update":
        if len(sys.argv) < 4:
            print("Для update нужны: status и details")
            sys.exit(1)
        status = sys.argv[2]
        details = sys.argv[3] if len(sys.argv) > 3 else ""
        send_update_notification("manual", status, details)
    
    elif notification_type == "maintenance":
        if len(sys.argv) < 5:
            print("Для maintenance нужны: start_time, end_time, reason")
            sys.exit(1)
        start_time = sys.argv[2]
        end_time = sys.argv[3]
        reason = sys.argv[4] if len(sys.argv) > 4 else ""
        send_maintenance_notification(start_time, end_time, reason)
    
    elif notification_type == "error":
        if len(sys.argv) < 4:
            print("Для error нужны: error_type, error_details, [severity]")
            sys.exit(1)
        error_type = sys.argv[2]
        error_details = sys.argv[3]
        severity = sys.argv[4] if len(sys.argv) > 4 else "medium"
        send_error_notification(error_type, error_details, severity)
    
    elif notification_type == "backup":
        if len(sys.argv) < 4:
            print("Для backup нужны: status и details")
            sys.exit(1)
        status = sys.argv[2]
        details = sys.argv[3] if len(sys.argv) > 3 else ""
        send_backup_notification("manual", status, details)
    
    else:
        print(f"Неизвестный тип уведомления: {notification_type}")
        sys.exit(1)


if __name__ == '__main__':
    main()
