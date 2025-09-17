# Система резервного копирования базы данных

Эта система обеспечивает автоматическое создание и восстановление резервных копий базы данных, чтобы всегда можно было восстановить данные в случае проблем.

## 🚀 Быстрый старт

### Создание резервной копии
```bash
# Создать резервную копию
python manage.py backup_db create --description "before_important_changes"

# Создать резервную копию автоматически (без подтверждений)
python manage.py backup_db create --description "auto_backup" --auto
```

### Восстановление базы данных
```bash
# Показать все резервные копии
python manage.py backup_db list

# Восстановить из конкретной копии
python manage.py backup_db restore --file backups/db_backup_20250911_160000_before_important_changes.sqlite3

# Интерактивное восстановление
python restore_db.py

# Быстрое восстановление последней копии
python restore_db.py --latest
```

## 📋 Команды управления

### 1. Создание резервных копий
```bash
# Ручное создание
python manage.py backup_db create --description "описание"

# Автоматическое создание
python manage.py backup_db create --description "auto" --auto
```

### 2. Просмотр резервных копий
```bash
# Список всех копий
python manage.py backup_db list
```

### 3. Восстановление
```bash
# Восстановление из файла
python manage.py backup_db restore --file путь/к/файлу.sqlite3

# Восстановление с подтверждением
python manage.py backup_db restore --file путь/к/файлу.sqlite3

# Автоматическое восстановление
python manage.py backup_db restore --file путь/к/файлу.sqlite3 --auto
```

### 4. Очистка старых копий
```bash
# Удалить старые копии (оставить 10 последних)
python manage.py backup_db cleanup

# Удалить старые копии (оставить 5 последних)
python manage.py backup_db cleanup --keep 5

# Автоматическая очистка
python manage.py backup_db cleanup --keep 10 --auto
```

### 5. Проверка целостности
```bash
# Проверить резервную копию
python manage.py backup_db verify --file путь/к/файлу.sqlite3
```

## 🛡️ Безопасное тестирование

Тесты теперь автоматически создают резервные копии:

```bash
# Запуск безопасных тестов (автоматически создается резервная копия)
python test_telegram_bot_safe.py
```

## 📁 Структура файлов

```
backups/                          # Папка с резервными копиями
├── db_backup_20250911_160000_before_tests.sqlite3
├── db_backup_20250911_160000_before_tests.json
├── db_backup_20250911_170000_manual.sqlite3
└── db_backup_20250911_170000_manual.json

backup_manager.py                 # Основной менеджер резервного копирования
restore_db.py                     # Скрипт быстрого восстановления
accounts/management/commands/
└── backup_db.py                  # Django команда для управления
```

## 🔧 Настройка автоматического резервного копирования

### 1. Создание резервной копии перед важными операциями
```python
from django.core.management import call_command

# Создать резервную копию перед миграциями
call_command('backup_db', 'create', '--description', 'before_migration', '--auto')
```

### 2. Автоматическая очистка старых копий
```python
# Очистить старые копии (оставить 5 последних)
call_command('backup_db', 'cleanup', '--keep', '5', '--auto')
```

## ⚠️ Важные замечания

1. **Всегда создавайте резервные копии** перед важными изменениями
2. **Проверяйте целостность** резервных копий перед восстановлением
3. **Регулярно очищайте** старые резервные копии для экономии места
4. **Тестируйте восстановление** на тестовой среде

## 🚨 Восстановление в критических ситуациях

Если база данных повреждена или потеряна:

1. **Найдите последнюю резервную копию:**
   ```bash
   python manage.py backup_db list
   ```

2. **Проверьте целостность:**
   ```bash
   python manage.py backup_db verify --file backups/последняя_копия.sqlite3
   ```

3. **Восстановите базу данных:**
   ```bash
   python restore_db.py --latest
   ```

4. **Проверьте восстановление:**
   ```bash
   python check_db.py
   ```

## 📊 Мониторинг

### Проверка состояния базы данных
```bash
# Показать информацию о пользователях
python check_db.py

# Проверить целостность текущей БД
python manage.py backup_db verify --file db.sqlite3
```

### Автоматические проверки
```bash
# Создать резервную копию и проверить её
python manage.py backup_db create --description "daily_check" --auto
python manage.py backup_db verify --file backups/последняя_копия.sqlite3
```

## 🔄 Интеграция с CI/CD

Для автоматического резервного копирования в CI/CD:

```yaml
# Пример для GitHub Actions
- name: Create database backup
  run: python manage.py backup_db create --description "ci_backup" --auto

- name: Run tests
  run: python test_telegram_bot_safe.py

- name: Restore database if tests fail
  if: failure()
  run: python restore_db.py --latest
```

## 📞 Поддержка

Если возникли проблемы с резервным копированием:

1. Проверьте права доступа к папке `backups/`
2. Убедитесь, что база данных не заблокирована
3. Проверьте свободное место на диске
4. Используйте команду `verify` для проверки целостности

---

**Помните: резервное копирование - это ваша страховка от потери данных!** 🛡️
