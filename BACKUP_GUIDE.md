# 💾 Руководство по резервному копированию SuperPan

## 📋 Обзор

Система SuperPan включает автоматическую систему резервного копирования базы данных для обеспечения безопасности данных.

## 🔧 Автоматические бэкапы

### Настройка автоматических бэкапов

```bash
# Настройка автоматических бэкапов каждые 3 дня
python setup_auto_backup.py
```

### Расписание бэкапов

- **Частота:** Каждые 3 дня
- **Время:** 19:15 (настраивается)
- **Формат:** JSON + SQLite
- **Хранение:** Папка `backups/`

## 🛠️ Ручное управление бэкапами

### Создание бэкапа

```bash
# Создать бэкап с автоматическим именем
python backup_manager.py backup

# Создать бэкап с пользовательским именем
python backup_manager.py backup "backup_before_update"
```

### Восстановление из бэкапа

```bash
# Показать список доступных бэкапов
python backup_manager.py list

# Восстановить из бэкапа
python backup_manager.py restore backup_name

# Восстановить последний бэкап
python backup_manager.py restore latest
```

### Удаление старых бэкапов

```bash
# Удалить бэкапы старше 30 дней
python backup_manager.py cleanup 30
```

## 📁 Структура бэкапов

```
backups/
├── db_backup_20250911_191019_before_tests.json
├── db_backup_20250911_191019_before_tests.sqlite3
├── db_backup_20250911_191123_demo_backup.json
├── db_backup_20250911_191123_demo_backup.sqlite3
└── ...
```

### Форматы бэкапов

1. **JSON файлы** - структурированные данные для восстановления
2. **SQLite файлы** - полные копии базы данных

## 🔄 Процесс восстановления

### 1. Остановка сервера

```bash
# Остановите Django сервер
# Остановите Telegram бота
```

### 2. Восстановление базы данных

```bash
# Восстановите из JSON бэкапа
python backup_manager.py restore backup_name

# Или скопируйте SQLite файл
cp backups/db_backup_YYYYMMDD_HHMMSS.sqlite3 db.sqlite3
```

### 3. Проверка восстановления

```bash
# Проверьте целостность данных
python manage.py check --database default

# Запустите сервер
python manage.py runserver
```

## 🚀 Бэкапы для продакшена

### PostgreSQL бэкапы

Для продакшена с PostgreSQL:

```bash
# Создание бэкапа PostgreSQL
pg_dump -h hostname -U username -d database_name > backup.sql

# Восстановление PostgreSQL
psql -h hostname -U username -d database_name < backup.sql
```

### Автоматизация бэкапов

```bash
# Cron задача для ежедневных бэкапов
0 2 * * * /path/to/backup_script.sh

# Скрипт бэкапа
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL > "backup_$DATE.sql"
```

## 🔒 Безопасность бэкапов

### Шифрование

```bash
# Шифрование бэкапа
gpg --cipher-algo AES256 --compress-algo 1 --symmetric backup.sql

# Расшифровка
gpg --decrypt backup.sql.gpg > backup.sql
```

### Хранение

- **Локально:** В папке `backups/`
- **Облако:** AWS S3, Google Drive, Dropbox
- **Внешние носители:** USB, внешние диски

### Доступ

- Ограничьте доступ к папке бэкапов
- Используйте сильные пароли для архивированных бэкапов
- Регулярно проверяйте целостность бэкапов

## 📊 Мониторинг бэкапов

### Проверка статуса

```bash
# Проверка последнего бэкапа
python backup_manager.py status

# Проверка размера папки бэкапов
du -sh backups/
```

### Алерты

Настройте уведомления о:
- Успешном создании бэкапа
- Ошибках создания бэкапа
- Превышении размера папки бэкапов

## 🔧 Настройка

### Конфигурация

```python
# В backup_manager.py
BACKUP_DIR = 'backups'
MAX_BACKUPS = 30  # Максимум бэкапов
RETENTION_DAYS = 90  # Хранение в днях
```

### Переменные окружения

```env
# Настройки бэкапов
BACKUP_ENABLED=True
BACKUP_SCHEDULE=3  # Дни между бэкапами
BACKUP_TIME=19:15  # Время создания бэкапа
```

## 📱 Интеграция с системой

### Django команды

```bash
# Создание бэкапа через Django
python manage.py backup_db

# Восстановление через Django
python manage.py restore_db backup_name
```

### API endpoints

```python
# Создание бэкапа через API
POST /api/backup/create/

# Список бэкапов через API
GET /api/backup/list/
```

## 🆘 Восстановление после сбоя

### Полное восстановление

1. **Остановите все сервисы**
2. **Восстановите базу данных**
3. **Проверьте целостность**
4. **Запустите сервисы**

### Частичное восстановление

```bash
# Восстановление только пользователей
python manage.py loaddata users_backup.json

# Восстановление только проектов
python manage.py loaddata projects_backup.json
```

## 📈 Оптимизация

### Сжатие бэкапов

```bash
# Сжатие JSON бэкапов
gzip backups/*.json

# Сжатие SQLite бэкапов
sqlite3 backup.db ".backup compressed_backup.db"
```

### Инкрементальные бэкапы

```bash
# Создание инкрементального бэкапа
rsync -av --link-dest=previous_backup/ current_data/ new_backup/
```

## 📞 Поддержка

### Полезные команды

```bash
# Проверка целостности базы данных
python manage.py check --database default

# Анализ размера базы данных
sqlite3 db.sqlite3 ".dbinfo"

# Оптимизация базы данных
sqlite3 db.sqlite3 "VACUUM;"
```

### Контакты

При проблемах с бэкапами обращайтесь к администратору системы.

---

**Безопасного хранения данных! 💾**
