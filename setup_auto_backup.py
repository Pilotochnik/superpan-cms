#!/usr/bin/env python
"""
Универсальный скрипт для настройки автоматического резервного копирования
Автоматически определяет операционную систему и настраивает соответствующий планировщик
"""

import os
import sys
import platform
from pathlib import Path


def detect_os():
    """Определяет операционную систему"""
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system in ['linux', 'darwin']:  # Darwin = macOS
        return 'unix'
    else:
        return 'unknown'


def setup_auto_backup():
    """Настраивает автоматическое резервное копирование"""
    print("=" * 70)
    print("🚀 НАСТРОЙКА АВТОМАТИЧЕСКОГО РЕЗЕРВНОГО КОПИРОВАНИЯ")
    print("=" * 70)
    print("Автоматическое создание резервных копий каждые 3 дня")
    print("=" * 70)
    
    # Определяем ОС
    os_type = detect_os()
    print(f"🖥️  Обнаружена ОС: {platform.system()} {platform.release()}")
    
    if os_type == 'windows':
        print("📋 Настройка для Windows (Планировщик задач)")
        setup_windows()
    elif os_type == 'unix':
        print("📋 Настройка для Linux/Mac (Cron)")
        setup_unix()
    else:
        print("❌ Неподдерживаемая операционная система")
        print("Настройте резервное копирование вручную")
        show_manual_instructions()


def setup_windows():
    """Настройка для Windows"""
    try:
        print("\n🔧 Запуск настройки Windows...")
        
        # Импортируем и запускаем настройку Windows
        from setup_windows_scheduler import main as setup_windows_main
        setup_windows_main()
        
    except ImportError:
        print("❌ Не удалось импортировать модуль настройки Windows")
        show_manual_instructions()
    except Exception as e:
        print(f"❌ Ошибка настройки Windows: {e}")
        show_manual_instructions()


def setup_unix():
    """Настройка для Unix-систем"""
    try:
        print("\n🔧 Запуск настройки Linux/Mac...")
        
        # Импортируем и запускаем настройку Unix
        from setup_cron import main as setup_cron_main
        setup_cron_main()
        
    except ImportError:
        print("❌ Не удалось импортировать модуль настройки Unix")
        show_manual_instructions()
    except Exception as e:
        print(f"❌ Ошибка настройки Unix: {e}")
        show_manual_instructions()


def show_manual_instructions():
    """Показывает инструкции для ручной настройки"""
    print("\n📋 РУЧНАЯ НАСТРОЙКА АВТОМАТИЧЕСКОГО РЕЗЕРВНОГО КОПИРОВАНИЯ")
    print("=" * 70)
    
    project_dir = Path.cwd().absolute()
    python_exe = sys.executable
    manage_py = project_dir / "manage.py"
    
    print(f"📁 Директория проекта: {project_dir}")
    print(f"🐍 Python: {python_exe}")
    print(f"📄 manage.py: {manage_py}")
    
    print("\n🕐 Команда для запуска каждые 3 дня:")
    print(f"   {python_exe} {manage_py} auto_backup --days 3")
    
    print("\n🔍 Проверка статуса:")
    print(f"   {python_exe} {manage_py} auto_backup --check-only")
    
    print("\n📋 Доступные команды:")
    print("   python manage.py auto_backup --help")
    print("   python manage.py backup_db --help")
    
    print("\n🛠️  Настройка планировщика:")
    
    if platform.system().lower() == 'windows':
        print("   Windows: Используйте Планировщик задач")
        print("   1. Откройте Планировщик задач")
        print("   2. Создайте базовую задачу")
        print("   3. Настройте запуск каждые 3 дня")
        print(f"   4. Действие: {python_exe} {manage_py} auto_backup --days 3")
        print(f"   5. Начальная папка: {project_dir}")
    else:
        print("   Linux/Mac: Используйте cron")
        print("   1. Откройте crontab: crontab -e")
        print("   2. Добавьте строку: 0 0 */3 * * cd {project_dir} && {python_exe} {manage_py} auto_backup --days 3")
        print("   3. Сохраните и закройте редактор")


def test_backup_system():
    """Тестирует систему резервного копирования"""
    print("\n🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ РЕЗЕРВНОГО КОПИРОВАНИЯ")
    print("=" * 50)
    
    try:
        import subprocess
        
        # Тестируем команду проверки
        print("1. Проверка статуса резервного копирования...")
        result = subprocess.run([
            sys.executable, "manage.py", "auto_backup", "--check-only"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Команда проверки работает")
            print("📋 Вывод:")
            print(result.stdout)
        else:
            print("❌ Ошибка команды проверки:")
            print(result.stderr)
        
        # Тестируем создание резервной копии
        print("\n2. Тестирование создания резервной копии...")
        result = subprocess.run([
            sys.executable, "manage.py", "backup_db", "create", "--description", "test_auto_backup", "--auto"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Создание резервной копии работает")
        else:
            print("❌ Ошибка создания резервной копии:")
            print(result.stderr)
        
        # Показываем список резервных копий
        print("\n3. Список резервных копий...")
        result = subprocess.run([
            sys.executable, "manage.py", "backup_db", "list"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Список резервных копий:")
            print(result.stdout)
        else:
            print("❌ Ошибка получения списка:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")


def main():
    """Главная функция"""
    print("🎯 Выберите действие:")
    print("1. Настроить автоматическое резервное копирование")
    print("2. Протестировать систему резервного копирования")
    print("3. Показать инструкции для ручной настройки")
    print("4. Выход")
    
    choice = input("\nВведите номер (1-4): ").strip()
    
    if choice == '1':
        setup_auto_backup()
    elif choice == '2':
        test_backup_system()
    elif choice == '3':
        show_manual_instructions()
    elif choice == '4':
        print("👋 До свидания!")
    else:
        print("❌ Неверный выбор")
        main()


if __name__ == '__main__':
    main()
