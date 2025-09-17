#!/usr/bin/env python3
"""
Менеджер версий для SuperPan
Позволяет управлять версионированием проекта
"""

import os
import re
from datetime import datetime


def get_current_version():
    """Получить текущую версию из файла VERSION"""
    try:
        with open('VERSION', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"


def set_version(version):
    """Установить новую версию"""
    with open('VERSION', 'w') as f:
        f.write(version)
    print(f"✅ Версия установлена: {version}")


def bump_version(version_type='patch'):
    """
    Увеличить версию
    
    Args:
        version_type: 'major', 'minor', 'patch'
    """
    current = get_current_version()
    parts = current.split('.')
    
    if len(parts) != 3:
        raise ValueError(f"Неверный формат версии: {current}")
    
    major, minor, patch = map(int, parts)
    
    if version_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif version_type == 'minor':
        minor += 1
        patch = 0
    elif version_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Неверный тип версии: {version_type}")
    
    new_version = f"{major}.{minor}.{patch}"
    set_version(new_version)
    return new_version


def update_changelog(version, changelog_type='release'):
    """
    Обновить CHANGELOG.md
    
    Args:
        version: новая версия
        changelog_type: 'release' или 'unreleased'
    """
    date = datetime.now().strftime("%Y-%m-%d")
    
    if changelog_type == 'release':
        entry = f"""## [{version}] - {date}

### Добавлено
- Новые функции и улучшения

### Исправлено
- Исправления ошибок

### Изменено
- Изменения в существующем функционале

---
"""
    else:
        entry = f"""## [{version}] - {date}

### Добавлено
- Новые функции и улучшения

### Исправлено
- Исправления ошибок

### Изменено
- Изменения в существующем функционале

"""
    
    try:
        with open('CHANGELOG.md', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = "# Changelog\n\n"
    
    # Вставляем новую запись после заголовка
    lines = content.split('\n')
    insert_index = 2  # После заголовка и пустой строки
    
    for i, line in enumerate(lines):
        if line.startswith('## ['):
            insert_index = i
            break
    
    lines.insert(insert_index, entry)
    
    with open('CHANGELOG.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ CHANGELOG.md обновлен")


def update_readme_version(version):
    """Обновить версию в README.md"""
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ README.md не найден")
        return
    
    # Заменяем версию в README
    pattern = r'\*\*Версия:\*\* [0-9]+\.[0-9]+\.[0-9]+'
    replacement = f'**Версия:** {version}'
    new_content = re.sub(pattern, replacement, content)
    
    # Заменяем дату последнего обновления
    today = datetime.now().strftime("%B %Y")
    pattern = r'\*\*Последнее обновление:\*\* [A-Za-z]+ [0-9]{4}'
    replacement = f'**Последнее обновление:** {today}'
    new_content = re.sub(pattern, replacement, new_content)
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ README.md обновлен")


def main():
    """Главная функция"""
    import sys
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python version_manager.py current          # Показать текущую версию")
        print("  python version_manager.py bump patch       # Увеличить patch версию")
        print("  python version_manager.py bump minor       # Увеличить minor версию")
        print("  python version_manager.py bump major       # Увеличить major версию")
        print("  python version_manager.py set 1.2.3        # Установить конкретную версию")
        print("  python version_manager.py release patch    # Создать релиз")
        return
    
    command = sys.argv[1]
    
    if command == 'current':
        version = get_current_version()
        print(f"Текущая версия: {version}")
    
    elif command == 'bump':
        if len(sys.argv) < 3:
            print("❌ Укажите тип версии: patch, minor, major")
            return
        
        version_type = sys.argv[2]
        new_version = bump_version(version_type)
        print(f"🚀 Версия увеличена: {new_version}")
    
    elif command == 'set':
        if len(sys.argv) < 3:
            print("❌ Укажите версию")
            return
        
        version = sys.argv[2]
        set_version(version)
    
    elif command == 'release':
        if len(sys.argv) < 3:
            print("❌ Укажите тип версии: patch, minor, major")
            return
        
        version_type = sys.argv[2]
        new_version = bump_version(version_type)
        update_changelog(new_version, 'release')
        update_readme_version(new_version)
        print(f"🎉 Релиз {new_version} создан!")
        print("📝 Не забудьте:")
        print("  - Проверить CHANGELOG.md")
        print("  - Создать git tag")
        print("  - Запушить изменения")
    
    else:
        print(f"❌ Неизвестная команда: {command}")


if __name__ == '__main__':
    main()
