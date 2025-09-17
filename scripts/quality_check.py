#!/usr/bin/env python3
"""
Скрипт для проверки качества кода
Запускает все линтеры, тесты и проверки безопасности
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Запустить команду и вывести результат"""
    print(f"\n🔍 {description}")
    print(f"Команда: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - УСПЕШНО")
            return True
        else:
            print(f"❌ {description} - ОШИБКА (код: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ {description} - ИСКЛЮЧЕНИЕ: {e}")
        return False


def check_black():
    """Проверка форматирования кода с Black"""
    return run_command("black --check .", "Проверка форматирования кода (Black)")


def check_isort():
    """Проверка сортировки импортов с isort"""
    return run_command("isort --check-only .", "Проверка сортировки импортов (isort)")


def check_flake8():
    """Проверка стиля кода с flake8"""
    return run_command("flake8 .", "Проверка стиля кода (flake8)")


def check_bandit():
    """Проверка безопасности с bandit"""
    return run_command("bandit -r . -f json", "Проверка безопасности (bandit)")


def run_tests():
    """Запуск тестов"""
    return run_command("pytest --cov=. --cov-report=term-missing", "Запуск тестов (pytest)")


def run_migrations_check():
    """Проверка миграций"""
    return run_command("python manage.py makemigrations --check", "Проверка миграций")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="Проверка качества кода SuperPan")
    parser.add_argument(
        '--fix', 
        action='store_true', 
        help='Автоматически исправить форматирование'
    )
    parser.add_argument(
        '--skip-tests', 
        action='store_true', 
        help='Пропустить тесты'
    )
    parser.add_argument(
        '--only-format', 
        action='store_true', 
        help='Только проверка форматирования'
    )
    
    args = parser.parse_args()
    
    print("🚀 Запуск проверки качества кода SuperPan")
    print("=" * 60)
    
    results = []
    
    if args.fix:
        print("\n🔧 Автоматическое исправление форматирования...")
        run_command("black .", "Исправление форматирования (Black)")
        run_command("isort .", "Исправление импортов (isort)")
    
    # Проверки форматирования
    results.append(check_black())
    results.append(check_isort())
    
    if args.only_format:
        print("\n📊 Результаты проверки форматирования:")
        passed = sum(results)
        total = len(results)
        print(f"✅ Пройдено: {passed}/{total}")
        
        if passed == total:
            print("🎉 Все проверки форматирования пройдены!")
            return 0
        else:
            print("❌ Некоторые проверки форматирования не пройдены!")
            return 1
    
    # Проверки качества кода
    results.append(check_flake8())
    results.append(check_bandit())
    results.append(run_migrations_check())
    
    # Тесты
    if not args.skip_tests:
        results.append(run_tests())
    else:
        print("\n⏭️ Тесты пропущены")
    
    # Итоговый результат
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Не пройдено: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 Все проверки пройдены успешно!")
        print("🚀 Код готов к коммиту и деплою!")
        return 0
    else:
        print("❌ Некоторые проверки не пройдены!")
        print("🔧 Исправьте ошибки перед коммитом")
        return 1


if __name__ == '__main__':
    sys.exit(main())
