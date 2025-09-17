# 🚀 Руководство по деплою SuperPan

## 📋 Подготовка к деплою

### 1. Проверка готовности

Перед деплоем убедитесь, что:

- [ ] Все тесты пройдены
- [ ] База данных мигрирована
- [ ] Статические файлы собраны
- [ ] Переменные окружения настроены
- [ ] Telegram бот настроен

### 2. Переменные окружения для продакшена

Создайте `.env` файл с продакшен настройками:

```env
# Основные настройки
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# База данных (PostgreSQL для продакшена)
DATABASE_URL=postgresql://user:password@host:port/database

# Telegram бот
TELEGRAM_BOT_TOKEN=your-production-bot-token
TELEGRAM_BOT_USERNAME=your_production_bot_username

# Email настройки (опционально)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# Безопасность
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

## 🌐 Деплой на Heroku

### 1. Подготовка

```bash
# Установите Heroku CLI
# Создайте приложение
heroku create your-app-name

# Добавьте PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev
```

### 2. Переменные окружения

```bash
# Установите переменные окружения
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS="your-app-name.herokuapp.com"
heroku config:set TELEGRAM_BOT_TOKEN="your-bot-token"
heroku config:set TELEGRAM_BOT_USERNAME="your_bot_username"
```

### 3. Деплой

```bash
# Деплой кода
git push heroku main

# Примените миграции
heroku run python manage.py migrate

# Создайте суперпользователя
heroku run python manage.py createsuperuser

# Соберите статические файлы
heroku run python manage.py collectstatic --noinput
```

### 4. Настройка Telegram бота

```bash
# Установите веб-хук
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-app-name.herokuapp.com/telegram/webhook/"}'
```

## 🚂 Деплой на Railway

### 1. Подготовка

1. Зайдите на [Railway.app](https://railway.app)
2. Подключите GitHub репозиторий
3. Создайте новый проект

### 2. Настройка базы данных

1. Добавьте PostgreSQL сервис
2. Скопируйте DATABASE_URL из переменных окружения

### 3. Переменные окружения

В настройках проекта добавьте:

```
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_BOT_USERNAME=your_bot_username
```

### 4. Деплой

Railway автоматически деплоит при пуше в main ветку.

## 🎨 Деплой на Render

### 1. Подготовка

1. Зайдите на [Render.com](https://render.com)
2. Создайте новый Web Service
3. Подключите GitHub репозиторий

### 2. Настройка

```yaml
# render.yaml (уже создан в проекте)
services:
  - type: web
    name: superpan
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn superpan.wsgi
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: False
      - key: TELEGRAM_BOT_TOKEN
        sync: false
```

### 3. База данных

1. Создайте PostgreSQL сервис
2. Добавьте DATABASE_URL в переменные окружения

## 🔧 Настройка после деплоя

### 1. Первоначальная настройка

```bash
# Примените миграции
python manage.py migrate

# Создайте суперпользователя
python manage.py createsuperuser

# Соберите статические файлы
python manage.py collectstatic --noinput
```

### 2. Настройка Telegram бота

```bash
# Установите веб-хук
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://yourdomain.com/telegram/webhook/"}'

# Проверьте статус бота
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"
```

### 3. Создание первого пользователя

1. Войдите в админ-панель
2. Перейдите в "Пользователи" → "Зарегистрировать через Telegram"
3. Следуйте инструкциям для создания пользователя

## 📊 Мониторинг

### 1. Логи

```bash
# Heroku
heroku logs --tail

# Railway
# Логи доступны в веб-интерфейсе

# Render
# Логи доступны в веб-интерфейсе
```

### 2. Мониторинг базы данных

- Проверяйте размер базы данных
- Настройте автоматические бэкапы
- Мониторьте производительность

### 3. Мониторинг Telegram бота

```bash
# Проверьте статус веб-хука
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"

# Получите информацию о боте
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"
```

## 🔒 Безопасность

### 1. SSL сертификаты

- Heroku: автоматически
- Railway: автоматически  
- Render: автоматически

### 2. Настройки безопасности

```python
# settings.py для продакшена
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 3. Ограничение доступа

- Настройте ALLOWED_HOSTS
- Используйте сильные пароли
- Регулярно обновляйте зависимости

## 🔄 Обновления

### 1. Обновление кода

```bash
# Heroku
git push heroku main

# Railway/Render
git push origin main
```

### 2. Обновление зависимостей

```bash
# Обновите requirements.txt
pip freeze > requirements.txt

# Деплойте изменения
git add requirements.txt
git commit -m "Update dependencies"
git push
```

### 3. Миграции базы данных

```bash
# Создайте миграции
python manage.py makemigrations

# Примените миграции
python manage.py migrate
```

## 🆘 Устранение неполадок

### 1. Проблемы с базой данных

```bash
# Проверьте подключение
python manage.py dbshell

# Сброс миграций (осторожно!)
python manage.py migrate --fake-initial
```

### 2. Проблемы с Telegram ботом

```bash
# Удалите веб-хук
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook"

# Установите заново
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://yourdomain.com/telegram/webhook/"}'
```

### 3. Проблемы со статическими файлами

```bash
# Пересоберите статические файлы
python manage.py collectstatic --clear --noinput
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи приложения
2. Проверьте статус базы данных
3. Проверьте настройки Telegram бота
4. Обратитесь к администратору системы

---

**Удачного деплоя! 🚀**
