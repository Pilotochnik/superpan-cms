# 🔄 Руководство по обновлению SuperPan

## 📋 Обзор

Это руководство описывает процесс обновления SuperPan на продакшен сервере с минимальным временем простоя.

## 🚀 Способы обновления

### 1. Ручное обновление (рекомендуется)

#### Быстрое обновление
```bash
# Перейти на сервер
ssh user@your-server.com

# Запустить скрипт обновления
cd /opt/superpan
sudo -u superpan ./update_production.sh
```

#### Принудительное обновление
```bash
# Принудительное обновление (игнорирует предупреждения)
sudo -u superpan ./update_production.sh --force
```

### 2. Автоматическое обновление

#### Настройка автоматических обновлений
```bash
# Добавить в cron для ежедневной проверки обновлений
sudo -u superpan crontab -e

# Добавить строку:
0 3 * * * /opt/superpan/auto_update.sh
```

#### Проверка обновлений без установки
```bash
cd /opt/superpan
git fetch origin master
git log HEAD..origin/master --oneline
```

## 📊 Процесс обновления

### Этапы обновления

1. **🔍 Проверка сервисов** - проверка текущего состояния
2. **💾 Резервное копирование** - создание бэкапа БД и кода
3. **⏹️ Остановка сервисов** - остановка Django и Telegram бота
4. **📥 Обновление кода** - получение изменений из Git
5. **📦 Обновление зависимостей** - установка новых пакетов
6. **🗄️ Миграции БД** - обновление структуры базы данных
7. **📁 Сбор статики** - обновление статических файлов
8. **✅ Проверка конфигурации** - валидация настроек
9. **🔄 Перезапуск сервисов** - запуск обновленных сервисов
10. **🧪 Тестирование** - проверка работоспособности

### Время простоя

- **Минимальное обновление:** 2-3 минуты
- **С миграциями БД:** 5-10 минут
- **С обновлением зависимостей:** 10-15 минут

## 🛠️ Детальные инструкции

### Подготовка к обновлению

#### 1. Проверка текущего состояния
```bash
# Проверка статуса сервисов
sudo systemctl status superpan
sudo systemctl status superpan-telegram-bot

# Проверка состояния БД
cd /opt/superpan
source venv/bin/activate
python db_monitor.py

# Проверка доступных обновлений
git fetch origin master
git log HEAD..origin/master --oneline
```

#### 2. Уведомление пользователей
```bash
# Отправить уведомление о технических работах
# (через Telegram бота или веб-интерфейс)
```

### Выполнение обновления

#### 1. Создание резервной копии
```bash
cd /opt/superpan
source venv/bin/activate
python manage.py backup_db create --description "before_update_$(date +%Y%m%d_%H%M%S)"
```

#### 2. Остановка сервисов
```bash
sudo systemctl stop superpan-telegram-bot
sudo systemctl stop superpan
```

#### 3. Обновление кода
```bash
cd /opt/superpan
git stash push -m "before_update"
git fetch origin master
git reset --hard origin/master
```

#### 4. Обновление зависимостей
```bash
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

#### 5. Миграции базы данных
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

#### 6. Запуск сервисов
```bash
sudo systemctl restart superpan
sudo systemctl restart superpan-telegram-bot
sudo systemctl reload nginx
```

#### 7. Проверка работоспособности
```bash
# Проверка статуса
sudo systemctl status superpan
sudo systemctl status superpan-telegram-bot

# Проверка веб-интерфейса
curl -I http://localhost:8000/

# Проверка БД
python db_monitor.py
```

## 🚨 Откат изменений

### Автоматический откат
```bash
# Если обновление прошло неудачно, скрипт автоматически откатится
# Проверьте логи для деталей
tail -f /opt/superpan/logs/auto_update.log
```

### Ручной откат
```bash
# 1. Остановить сервисы
sudo systemctl stop superpan-telegram-bot
sudo systemctl stop superpan

# 2. Восстановить код
cd /opt/superpan
git reset --hard HEAD~1  # или конкретный коммит

# 3. Восстановить БД
source venv/bin/activate
python restore_db.py --latest

# 4. Перезапустить сервисы
sudo systemctl restart superpan
sudo systemctl restart superpan-telegram-bot
```

## 📋 Чек-лист обновления

### Перед обновлением
- [ ] Проверить статус сервисов
- [ ] Создать резервную копию БД
- [ ] Уведомить пользователей о техработах
- [ ] Проверить доступные обновления
- [ ] Убедиться в наличии свободного места

### После обновления
- [ ] Проверить статус всех сервисов
- [ ] Протестировать веб-интерфейс
- [ ] Проверить работу Telegram бота
- [ ] Убедиться в корректности БД
- [ ] Проверить логи на ошибки
- [ ] Уведомить пользователей о завершении

## 🔧 Настройка автоматических обновлений

### Cron задачи

#### Ежедневная проверка обновлений
```bash
# Добавить в crontab пользователя superpan
0 3 * * * /opt/superpan/auto_update.sh
```

#### Еженедельная проверка с уведомлениями
```bash
# Проверка по воскресеньям в 2:00
0 2 * * 0 /opt/superpan/auto_update.sh && curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" -d "chat_id=$ADMIN_CHAT_ID" -d "text=✅ Еженедельное обновление SuperPan завершено"
```

### Telegram уведомления

#### Настройка уведомлений об обновлениях
```bash
# Добавить в .env файл
TELEGRAM_ADMIN_CHAT_ID=your_chat_id
TELEGRAM_UPDATE_NOTIFICATIONS=true
```

## 📊 Мониторинг обновлений

### Логи обновлений
```bash
# Просмотр логов автоматических обновлений
tail -f /opt/superpan/logs/auto_update.log

# Просмотр логов сервисов
sudo journalctl -u superpan -f
sudo journalctl -u superpan-telegram-bot -f
```

### Проверка версии
```bash
# Текущая версия в Git
cd /opt/superpan
git describe --tags

# Информация о последнем коммите
git log -1 --pretty=format:"%h - %an, %ar : %s"
```

## ⚠️ Важные замечания

### Безопасность
- **Всегда создавайте резервные копии** перед обновлением
- **Тестируйте обновления** на тестовой среде
- **Планируйте обновления** на время минимальной нагрузки
- **Имейте план отката** на случай проблем

### Производительность
- **Обновляйте в нерабочее время** для минимизации простоя
- **Мониторьте производительность** после обновления
- **Проверяйте использование ресурсов** сервера

### Совместимость
- **Проверяйте совместимость** версий Python и зависимостей
- **Читайте CHANGELOG** перед обновлением
- **Тестируйте новые функции** перед использованием

## 🆘 Решение проблем

### Частые проблемы

#### 1. Ошибки миграций
```bash
# Проверить статус миграций
python manage.py showmigrations

# Применить конкретную миграцию
python manage.py migrate app_name migration_name
```

#### 2. Проблемы с зависимостями
```bash
# Переустановить зависимости
pip install -r requirements.txt --force-reinstall
```

#### 3. Ошибки статических файлов
```bash
# Пересобрать статические файлы
python manage.py collectstatic --clear --noinput
```

#### 4. Проблемы с сервисами
```bash
# Проверить конфигурацию
sudo systemctl daemon-reload
sudo systemctl restart superpan
```

### Получение помощи

#### Логи для диагностики
```bash
# Собрать информацию для техподдержки
cd /opt/superpan
source venv/bin/activate
python db_monitor.py > diagnostic_report.txt
git log -10 --oneline >> diagnostic_report.txt
sudo systemctl status superpan >> diagnostic_report.txt
```

#### Контакты
- **GitHub Issues:** https://github.com/Pilotochnik/superpan-cms/issues
- **Email:** support@superpan.com
- **Telegram:** @superpan_support

---

**⚠️ ВАЖНО:** Всегда тестируйте процедуры обновления на тестовой среде перед применением в продакшене!
