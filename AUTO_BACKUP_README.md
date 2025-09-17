# 🤖 Автоматическое резервное копирование каждые 3 дня

Система автоматического создания резервных копий базы данных каждые 3 дня с поддержкой Windows, Linux и macOS.

## 🚀 Быстрый старт

### 1. Автоматическая настройка
```bash
# Универсальный скрипт настройки
python setup_auto_backup.py
```

### 2. Ручная настройка

#### Windows (Планировщик задач)
```bash
# Настройка для Windows
python setup_windows_scheduler.py
```

#### Linux/Mac (Cron)
```bash
# Настройка для Linux/Mac
python setup_cron.py
```

## 📋 Команды управления

### Проверка статуса
```bash
# Проверить, нужна ли резервная копия
python manage.py auto_backup --check-only

# Проверить с настройкой дней
python manage.py auto_backup --check-only --days 5
```

### Создание резервной копии
```bash
# Автоматическое создание (если нужно)
python manage.py auto_backup

# Принудительное создание
python manage.py auto_backup --force

# С настройкой интервала
python manage.py auto_backup --days 7
```

### Управление резервными копиями
```bash
# Показать все копии
python manage.py backup_db list

# Очистить старые копии
python manage.py backup_db cleanup --keep 10 --auto

# Проверить целостность
python manage.py backup_db verify --file backups/имя_файла.sqlite3
```

## ⚙️ Настройка планировщиков

### Windows - Планировщик задач

1. **Автоматическая настройка:**
   ```bash
   python setup_windows_scheduler.py
   ```

2. **Ручная настройка:**
   - Откройте "Планировщик задач"
   - Создайте базовую задачу
   - Настройте запуск каждые 3 дня
   - Действие: `python manage.py auto_backup --days 3`
   - Начальная папка: путь к проекту

3. **Управление задачей:**
   ```cmd
   # Просмотр задач
   schtasks /query /tn SuperPan_AutoBackup
   
   # Запуск вручную
   schtasks /run /tn SuperPan_AutoBackup
   
   # Удаление задачи
   schtasks /delete /tn SuperPan_AutoBackup /f
   ```

### Linux/Mac - Cron

1. **Автоматическая настройка:**
   ```bash
   python setup_cron.py
   ```

2. **Ручная настройка:**
   ```bash
   # Открыть crontab
   crontab -e
   
   # Добавить строку (каждые 3 дня в 00:00)
   0 0 */3 * * cd /path/to/project && python manage.py auto_backup --days 3 >> backup.log 2>&1
   ```

3. **Systemd (альтернатива cron):**
   ```bash
   # Скрипт создаст systemd сервис
   python setup_cron.py
   
   # Установка сервиса
   sudo cp superpan-backup.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable superpan-backup.timer
   sudo systemctl start superpan-backup.timer
   ```

## 🔧 Конфигурация

### Настройка интервала
```bash
# Каждые 3 дня (по умолчанию)
python manage.py auto_backup --days 3

# Каждую неделю
python manage.py auto_backup --days 7

# Каждый день
python manage.py auto_backup --days 1
```

### Настройка очистки
```bash
# Оставить 5 последних копий
python manage.py backup_db cleanup --keep 5 --auto

# Оставить 20 последних копий
python manage.py backup_db cleanup --keep 20 --auto
```

## 📊 Мониторинг

### Проверка статуса
```bash
# Текущий статус
python manage.py auto_backup --check-only

# Список всех резервных копий
python manage.py backup_db list

# Статистика
python manage.py auto_backup --force  # Покажет статистику
```

### Логи
- **Windows:** Планировщик задач → Журналы
- **Linux/Mac:** `tail -f backup.log`
- **Systemd:** `journalctl -u superpan-backup`

## 🚨 Устранение неполадок

### Проблема: Задача не запускается
```bash
# Проверьте права доступа
python manage.py auto_backup --check-only

# Запустите вручную
python manage.py auto_backup --force

# Проверьте логи планировщика
```

### Проблема: Ошибки кодировки (Windows)
```bash
# Установите переменную окружения
set PYTHONIOENCODING=utf-8
python manage.py auto_backup
```

### Проблема: Недостаточно места
```bash
# Очистите старые копии
python manage.py backup_db cleanup --keep 5 --auto

# Проверьте размер папки backups
dir backups
```

## 📁 Структура файлов

```
backups/                          # Резервные копии
├── db_backup_20250911_191523_auto_3days.sqlite3
├── db_backup_20250911_191523_auto_3days.json
└── ...

accounts/management/commands/
├── auto_backup.py                # Команда автоматического резервного копирования
└── backup_db.py                  # Команда управления резервными копиями

setup_auto_backup.py              # Универсальный скрипт настройки
setup_windows_scheduler.py        # Настройка для Windows
setup_cron.py                     # Настройка для Linux/Mac
backup_manager.py                 # Основной менеджер
restore_db.py                     # Быстрое восстановление
```

## ✅ Что автоматизировано

- ✅ **Проверка необходимости** резервной копии
- ✅ **Автоматическое создание** каждые 3 дня
- ✅ **Очистка старых** резервных копий
- ✅ **Проверка целостности** резервных копий
- ✅ **Статистика и мониторинг**
- ✅ **Поддержка Windows, Linux, macOS**
- ✅ **Логирование операций**

## 🎯 Рекомендации

1. **Тестируйте настройку** перед использованием в продакшене
2. **Мониторьте логи** для выявления проблем
3. **Регулярно проверяйте** целостность резервных копий
4. **Настройте уведомления** о создании резервных копий
5. **Проверяйте свободное место** на диске

## 🔄 Интеграция с CI/CD

```yaml
# GitHub Actions пример
- name: Auto Backup
  run: python manage.py auto_backup --days 3
  schedule: '0 0 */3 * *'  # каждые 3 дня
```

---

**Теперь ваша база данных автоматически защищена! 🛡️**
