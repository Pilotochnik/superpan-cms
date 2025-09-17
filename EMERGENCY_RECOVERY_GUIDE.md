# 🚨 Руководство по экстренному восстановлению SuperPan

## 📋 Обзор

Это руководство содержит пошаговые инструкции для восстановления системы SuperPan в случае падения базы данных или других критических сбоев.

## 🚨 Экстренные ситуации

### Симптомы проблем с БД:
- ❌ Ошибки подключения к базе данных
- ❌ Django выдает ошибки `DatabaseError`
- ❌ Пустые страницы или ошибки 500
- ❌ Telegram бот не отвечает
- ❌ Невозможно войти в систему

## ⚡ Быстрое восстановление (5 минут)

### 1. Автоматическое восстановление
```bash
# Экстренное восстановление из последней копии
python emergency_recovery.py --force

# Проверка состояния БД
python db_monitor.py
```

### 2. Ручное восстановление
```bash
# 1. Найти последнюю резервную копию
python manage.py backup_db list

# 2. Восстановить из последней копии
python restore_db.py --latest

# 3. Проверить восстановление
python manage.py check --database default
```

## 🔍 Диагностика проблем

### Проверка состояния БД
```bash
# Полная диагностика
python db_monitor.py

# Проверка целостности
python manage.py check --database default

# Проверка миграций
python manage.py migrate --check
```

### Проверка резервных копий
```bash
# Список всех копий
python manage.py backup_db list

# Проверка конкретной копии
python manage.py backup_db verify --file backups/имя_файла.sqlite3
```

## 🛠️ Пошаговое восстановление

### Шаг 1: Остановка сервисов
```bash
# Остановить Django сервер (Ctrl+C)
# Остановить Telegram бота (Ctrl+C)

# Если запущено как сервис:
sudo systemctl stop superpan
sudo systemctl stop superpan-telegram-bot
```

### Шаг 2: Диагностика
```bash
# Проверить состояние БД
python db_monitor.py

# Если БД повреждена, переходим к шагу 3
```

### Шаг 3: Восстановление
```bash
# Автоматическое восстановление
python emergency_recovery.py

# Или ручное восстановление
python restore_db.py --latest
```

### Шаг 4: Проверка восстановления
```bash
# Проверить Django
python manage.py check --database default
python manage.py migrate --check

# Проверить основные данные
python manage.py shell -c "
from accounts.models import User
from projects.models import Project
print(f'Пользователей: {User.objects.count()}')
print(f'Проектов: {Project.objects.count()}')
"
```

### Шаг 5: Запуск сервисов
```bash
# Запустить Django сервер
python manage.py runserver

# В другом терминале запустить Telegram бота
python run_telegram_bot.py
```

## 🔧 Продвинутое восстановление

### Восстановление из конкретной копии
```bash
# Список доступных копий
python manage.py backup_db list

# Восстановление конкретной копии
python manage.py backup_db restore --file backups/db_backup_20250911_191123_demo_backup.sqlite3
```

### Восстановление с проверкой
```bash
# Проверить копию перед восстановлением
python manage.py backup_db verify --file backups/имя_файла.sqlite3

# Восстановить только если проверка прошла
python manage.py backup_db restore --file backups/имя_файла.sqlite3 --verify
```

### Восстановление с резервным копированием
```bash
# Создать копию текущей БД перед восстановлением
python backup_manager.py backup "before_recovery"

# Восстановить из резервной копии
python restore_db.py --latest
```

## 📊 Мониторинг после восстановления

### Проверка работоспособности
```bash
# 1. Проверить веб-интерфейс
curl http://localhost:8000/

# 2. Проверить API
curl http://localhost:8000/api/

# 3. Проверить Telegram бота
# Отправить /start в боте

# 4. Проверить логи
tail -f logs/django.log
```

### Создание новой резервной копии
```bash
# Создать резервную копию после восстановления
python backup_manager.py backup "after_recovery"

# Настроить автоматические бэкапы
python setup_auto_backup.py
```

## 🚨 Критические ситуации

### Полная потеря данных
Если все резервные копии потеряны:

1. **Восстановить из Git:**
   ```bash
   git checkout HEAD -- db.sqlite3
   python manage.py migrate
   ```

2. **Пересоздать базу данных:**
   ```bash
   rm db.sqlite3
   python manage.py migrate
   python manage.py createsuperuser
   ```

3. **Восстановить тестовые данные:**
   ```bash
   python create_test_users.py
   ```

### Повреждение файловой системы
Если повреждена файловая система:

1. **Проверить диск:**
   ```bash
   # Windows
   chkdsk C: /f
   
   # Linux
   fsck /dev/sda1
   ```

2. **Восстановить из облачного хранилища** (если настроено)

3. **Восстановить из внешнего носителя**

## 📞 Контакты для экстренных случаев

### Логи и диагностика
```bash
# Собрать информацию для техподдержки
python db_monitor.py > diagnostic_report.txt
python manage.py backup_db list >> diagnostic_report.txt
```

### Файлы для отправки в поддержку:
- `diagnostic_report.txt` - отчет диагностики
- `logs/django.log` - логи Django
- Последняя резервная копия из папки `backups/`

## 🔄 Профилактика

### Регулярные проверки
```bash
# Еженедельная проверка
python db_monitor.py

# Ежемесячная очистка старых копий
python manage.py backup_db cleanup --keep 10 --auto
```

### Мониторинг
```bash
# Настроить автоматические проверки
# Добавить в cron (Linux) или планировщик задач (Windows):
# 0 2 * * * cd /path/to/superpan && python db_monitor.py
```

## 📚 Дополнительные ресурсы

- [BACKUP_README.md](BACKUP_README.md) - Основное руководство по резервному копированию
- [BACKUP_QUICK_START.md](BACKUP_QUICK_START.md) - Быстрый старт
- [AUTO_BACKUP_README.md](AUTO_BACKUP_README.md) - Автоматические бэкапы

---

**⚠️ ВАЖНО:** Всегда тестируйте процедуры восстановления на тестовой среде перед применением в продакшене!
