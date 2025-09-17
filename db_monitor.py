#!/usr/bin/env python
"""
Мониторинг состояния базы данных SuperPan
Проверяет целостность БД и автоматически создает бэкапы при необходимости
"""

import os
import sys
import sqlite3
import datetime
from pathlib import Path

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'superpan.settings')
import django
django.setup()

from django.conf import settings
from django.core.management import call_command
from backup_manager import DatabaseBackupManager


class DatabaseMonitor:
    """Мониторинг состояния базы данных"""
    
    def __init__(self):
        self.db_path = settings.DATABASES['default']['NAME']
        self.backup_manager = DatabaseBackupManager()
        
    def check_database_integrity(self):
        """Проверяет целостность базы данных"""
        print("🔍 Проверка целостности базы данных...")
        
        try:
            # Проверяем, существует ли файл БД
            if not os.path.exists(self.db_path):
                print("❌ Файл базы данных не найден!")
                return False
                
            # Проверяем размер файла
            db_size = os.path.getsize(self.db_path)
            if db_size == 0:
                print("❌ Файл базы данных пустой!")
                return False
                
            print(f"✅ Размер БД: {db_size:,} байт")
            
            # Проверяем целостность SQLite
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Выполняем PRAGMA integrity_check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            if result[0] == 'ok':
                print("✅ База данных прошла проверку целостности")
                conn.close()
                return True
            else:
                print(f"❌ Ошибка целостности: {result[0]}")
                conn.close()
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при проверке БД: {e}")
            return False
    
    def check_critical_tables(self):
        """Проверяет наличие критически важных таблиц"""
        print("🔍 Проверка критических таблиц...")
        
        critical_tables = [
            'users',
            'projects', 
            'expense_items',
            'telegram_users'
        ]
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = []
            for table in critical_tables:
                if table in existing_tables:
                    # Проверяем количество записей
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"✅ {table}: {count} записей")
                else:
                    missing_tables.append(table)
                    print(f"❌ {table}: таблица отсутствует")
            
            conn.close()
            
            if missing_tables:
                print(f"❌ Отсутствуют критические таблицы: {missing_tables}")
                return False
            else:
                print("✅ Все критические таблицы присутствуют")
                return True
                
        except Exception as e:
            print(f"❌ Ошибка при проверке таблиц: {e}")
            return False
    
    def check_recent_activity(self):
        """Проверяет активность в последние 24 часа"""
        print("🔍 Проверка активности за последние 24 часа...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем последние логины
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE last_login > datetime('now', '-1 day')
            """)
            recent_logins = cursor.fetchone()[0]
            print(f"📊 Активность за 24ч: {recent_logins} входов")
            
            # Проверяем последние изменения в проектах
            cursor.execute("""
                SELECT COUNT(*) FROM projects 
                WHERE updated_at > datetime('now', '-1 day')
            """)
            recent_projects = cursor.fetchone()[0]
            print(f"📊 Изменения проектов: {recent_projects}")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при проверке активности: {e}")
            return False
    
    def emergency_backup(self):
        """Создает экстренную резервную копию"""
        print("🚨 Создание экстренной резервной копии...")
        
        try:
            self.backup_manager.create_backup("emergency_backup")
            print("✅ Экстренная резервная копия создана")
            return True
        except Exception as e:
            print(f"❌ Ошибка создания резервной копии: {e}")
            return False
    
    def full_check(self):
        """Выполняет полную проверку состояния БД"""
        print("=" * 70)
        print("🔍 ПОЛНАЯ ПРОВЕРКА СОСТОЯНИЯ БАЗЫ ДАННЫХ")
        print("=" * 70)
        print(f"📅 Время проверки: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🗄️  Путь к БД: {self.db_path}")
        print("=" * 70)
        
        # Выполняем все проверки
        integrity_ok = self.check_database_integrity()
        tables_ok = self.check_critical_tables()
        activity_ok = self.check_recent_activity()
        
        print("=" * 70)
        print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
        print(f"   Целостность БД: {'✅ OK' if integrity_ok else '❌ ОШИБКА'}")
        print(f"   Критические таблицы: {'✅ OK' if tables_ok else '❌ ОШИБКА'}")
        print(f"   Активность: {'✅ OK' if activity_ok else '❌ ОШИБКА'}")
        
        if not (integrity_ok and tables_ok):
            print("=" * 70)
            print("🚨 ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ОШИБКИ!")
            print("📋 РЕКОМЕНДУЕМЫЕ ДЕЙСТВИЯ:")
            print("   1. Создать экстренную резервную копию")
            print("   2. Восстановить из последней рабочей копии")
            print("   3. Проверить логи системы")
            print("=" * 70)
            
            # Создаем экстренную резервную копию
            self.emergency_backup()
            
            return False
        else:
            print("=" * 70)
            print("✅ БАЗА ДАННЫХ В НОРМАЛЬНОМ СОСТОЯНИИ")
            print("=" * 70)
            return True


def main():
    """Главная функция мониторинга"""
    monitor = DatabaseMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--emergency':
        # Экстренная проверка с созданием бэкапа
        print("🚨 ЭКСТРЕННАЯ ПРОВЕРКА БАЗЫ ДАННЫХ")
        monitor.full_check()
        monitor.emergency_backup()
    else:
        # Обычная проверка
        monitor.full_check()


if __name__ == '__main__':
    main()
