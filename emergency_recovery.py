#!/usr/bin/env python
"""
Экстренное восстановление базы данных SuperPan
Автоматически восстанавливает БД из последней рабочей копии
"""

import os
import sys
import shutil
import sqlite3
import datetime
from pathlib import Path

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'superpan.settings')
import django
django.setup()

from django.conf import settings
from backup_manager import DatabaseBackupManager


class EmergencyRecovery:
    """Экстренное восстановление базы данных"""
    
    def __init__(self):
        self.db_path = settings.DATABASES['default']['NAME']
        self.backup_manager = DatabaseBackupManager()
        
    def find_latest_backup(self):
        """Находит последнюю резервную копию"""
        print("🔍 Поиск последней резервной копии...")
        
        backup_dir = Path('backups')
        if not backup_dir.exists():
            print("❌ Папка backups не найдена!")
            return None
            
        # Ищем все файлы .sqlite3
        backup_files = list(backup_dir.glob('*.sqlite3'))
        if not backup_files:
            print("❌ Резервные копии не найдены!")
            return None
            
        # Сортируем по времени модификации
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_backup = backup_files[0]
        
        print(f"✅ Найдена последняя копия: {latest_backup.name}")
        print(f"📅 Создана: {datetime.datetime.fromtimestamp(latest_backup.stat().st_mtime)}")
        print(f"📏 Размер: {latest_backup.stat().st_size:,} байт")
        
        return latest_backup
    
    def verify_backup(self, backup_path):
        """Проверяет целостность резервной копии"""
        print("🔍 Проверка целостности резервной копии...")
        
        try:
            conn = sqlite3.connect(str(backup_path))
            cursor = conn.cursor()
            
            # Проверяем целостность
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            if result[0] == 'ok':
                print("✅ Резервная копия прошла проверку целостности")
                
                # Проверяем критические таблицы
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                critical_tables = ['users_user', 'projects_project', 'kanban_expenseitem']
                missing_tables = [table for table in critical_tables if table not in tables]
                
                if missing_tables:
                    print(f"⚠️  Отсутствуют таблицы: {missing_tables}")
                    conn.close()
                    return False
                else:
                    print("✅ Все критические таблицы присутствуют")
                    conn.close()
                    return True
            else:
                print(f"❌ Ошибка целостности: {result[0]}")
                conn.close()
                return False
                
        except Exception as e:
            print(f"❌ Ошибка проверки резервной копии: {e}")
            return False
    
    def backup_current_db(self):
        """Создает резервную копию текущей БД перед восстановлением"""
        print("💾 Создание резервной копии текущей БД...")
        
        try:
            if os.path.exists(self.db_path):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"broken_db_{timestamp}.sqlite3"
                backup_path = Path('backups') / backup_name
                
                shutil.copy2(self.db_path, backup_path)
                print(f"✅ Текущая БД сохранена как: {backup_name}")
                return True
            else:
                print("ℹ️  Текущая БД не существует, пропускаем резервное копирование")
                return True
                
        except Exception as e:
            print(f"❌ Ошибка создания резервной копии: {e}")
            return False
    
    def restore_database(self, backup_path):
        """Восстанавливает базу данных из резервной копии"""
        print("🔄 Восстановление базы данных...")
        
        try:
            # Создаем папку для БД если её нет
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Копируем резервную копию
            shutil.copy2(backup_path, self.db_path)
            print("✅ База данных восстановлена")
            
            # Проверяем восстановленную БД
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            if result[0] == 'ok':
                print("✅ Восстановленная БД прошла проверку целостности")
                conn.close()
                return True
            else:
                print(f"❌ Ошибка восстановленной БД: {result[0]}")
                conn.close()
                return False
                
        except Exception as e:
            print(f"❌ Ошибка восстановления: {e}")
            return False
    
    def test_django_connection(self):
        """Тестирует подключение Django к восстановленной БД"""
        print("🔍 Тестирование подключения Django...")
        
        try:
            from django.core.management import call_command
            
            # Проверяем состояние БД
            call_command('check', '--database', 'default')
            print("✅ Django проверка пройдена")
            
            # Проверяем миграции
            call_command('migrate', '--check')
            print("✅ Проверка миграций пройдена")
            
            # Проверяем основные модели
            from accounts.models import User
            from projects.models import Project
            
            user_count = User.objects.count()
            project_count = Project.objects.count()
            
            print(f"📊 Пользователей: {user_count}")
            print(f"📊 Проектов: {project_count}")
            
            if user_count > 0 and project_count >= 0:
                print("✅ Основные модели работают корректно")
                return True
            else:
                print("⚠️  Неожиданные данные в БД")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка тестирования Django: {e}")
            return False
    
    def emergency_recovery(self):
        """Выполняет полное экстренное восстановление"""
        print("=" * 70)
        print("🚨 ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ БАЗЫ ДАННЫХ")
        print("=" * 70)
        print(f"📅 Время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🗄️  БД: {self.db_path}")
        print("=" * 70)
        
        # Шаг 1: Найти последнюю резервную копию
        latest_backup = self.find_latest_backup()
        if not latest_backup:
            print("❌ Невозможно найти резервную копию для восстановления")
            return False
        
        # Шаг 2: Проверить целостность резервной копии
        if not self.verify_backup(latest_backup):
            print("❌ Резервная копия повреждена")
            return False
        
        # Шаг 3: Создать резервную копию текущей БД
        if not self.backup_current_db():
            print("⚠️  Не удалось создать резервную копию текущей БД")
            print("Продолжаем восстановление...")
        
        # Шаг 4: Восстановить БД
        if not self.restore_database(latest_backup):
            print("❌ Ошибка восстановления БД")
            return False
        
        # Шаг 5: Тестировать восстановленную БД
        if not self.test_django_connection():
            print("❌ Ошибка тестирования восстановленной БД")
            return False
        
        print("=" * 70)
        print("✅ ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО")
        print("=" * 70)
        print("📋 СЛЕДУЮЩИЕ ШАГИ:")
        print("   1. Запустите сервер: python manage.py runserver")
        print("   2. Проверьте Telegram бота: python run_telegram_bot.py")
        print("   3. Проверьте основные функции системы")
        print("   4. Создайте новую резервную копию")
        print("=" * 70)
        
        return True


def main():
    """Главная функция экстренного восстановления"""
    recovery = EmergencyRecovery()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        # Принудительное восстановление
        recovery.emergency_recovery()
    else:
        # Интерактивное восстановление
        print("⚠️  ВНИМАНИЕ: ЭТО ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ БАЗЫ ДАННЫХ!")
        print("Текущая БД будет заменена последней резервной копией.")
        print()
        
        response = input("Продолжить? (yes/no): ").lower().strip()
        if response in ['yes', 'y', 'да', 'д']:
            recovery.emergency_recovery()
        else:
            print("Восстановление отменено.")


if __name__ == '__main__':
    main()
