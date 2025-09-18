# 🎨 Деплой SuperPan на Render

## 📋 Подготовка

### 1. Создайте аккаунт на Render
- Перейдите на [render.com](https://render.com)
- Войдите через GitHub
- Подтвердите email

### 2. Подготовьте Telegram бота
- Найдите [@BotFather](https://t.me/BotFather) в Telegram
- Создайте бота командой `/newbot`
- Сохраните токен бота

## 🚀 Деплой

### Шаг 1: Создание базы данных PostgreSQL
1. В Render нажмите "New +"
2. Выберите "PostgreSQL"
3. Настройте:
   - **Name**: `superpan-db`
   - **Database**: `superpan`
   - **User**: `superpan_user`
   - **Password**: сгенерируйте надёжный пароль
   - **Plan**: Free
4. Нажмите "Create Database"
5. **Скопируйте DATABASE_URL** - он понадобится позже

### Шаг 2: Создание веб-сервиса
1. Нажмите "New +" → "Web Service"
2. Подключите GitHub репозиторий
3. Выберите репозиторий `superpan-cms`
4. Настройте:
   - **Name**: `superpan`
   - **Environment**: `Python 3`
   - **Region**: `Oregon (US West)`
   - **Branch**: `master`
   - **Root Directory**: оставьте пустым
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python manage.py migrate && python manage.py init_production && python manage.py collectstatic --noinput && gunicorn superpan.wsgi:application`

### Шаг 3: Настройка переменных окружения
В разделе "Environment Variables" добавьте:

```env
DEBUG=False
SECRET_KEY=your-super-secret-key-here-change-this
ALLOWED_HOSTS=*.onrender.com,localhost,127.0.0.1
DATABASE_URL=postgresql://superpan_user:password@dpg-xxxxx-a.oregon-postgres.render.com/superpan
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_BOT_USERNAME=your_bot_username
TELEGRAM_WEBHOOK_SECRET=your-webhook-secret
SENTRY_DSN=
```

**Важно**: Замените `DATABASE_URL` на реальный URL из шага 1!

### Шаг 4: Деплой
1. Нажмите "Create Web Service"
2. Render автоматически:
   - Установит зависимости
   - Выполнит миграции
   - Создаст тестовые данные
   - Соберёт статические файлы
   - Запустит приложение

## 🔧 Настройка после деплоя

### 1. Получите URL приложения
- В Render найдите ваш сервис
- Скопируйте URL (например: `https://superpan.onrender.com`)

### 2. Настройте Telegram webhook
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://superpan.onrender.com/telegram/webhook/"}'
```

### 3. Проверьте работу
- Откройте URL приложения в браузере
- Войдите как `admin@superpan.ru` / `admin123`
- Протестируйте Telegram бота

## 📱 Создание Telegram бота

1. Найдите [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Введите имя: `SuperPan Test Bot`
4. Введите username: `superpan_test_bot`
5. Скопируйте токен

## 🔍 Мониторинг

### Логи приложения
- В Render перейдите в ваш сервис
- Вкладка "Logs" - просмотр логов в реальном времени

### Статус сервисов
- Проверьте статус веб-сервиса
- Проверьте статус базы данных
- Убедитесь, что все переменные окружения настроены

## 🆘 Устранение неполадок

### Проблема: Приложение не запускается
**Решение:**
1. Проверьте логи в Render
2. Убедитесь, что DATABASE_URL корректный
3. Проверьте, что все переменные окружения настроены

### Проблема: Ошибки базы данных
**Решение:**
1. Убедитесь, что PostgreSQL создан
2. Проверьте DATABASE_URL
3. Убедитесь, что база данных запущена

### Проблема: Telegram бот не отвечает
**Решение:**
1. Проверьте TELEGRAM_BOT_TOKEN
2. Убедитесь, что webhook настроен правильно
3. Проверьте логи приложения

### Проблема: Статические файлы не загружаются
**Решение:**
1. Убедитесь, что `collectstatic` выполняется
2. Проверьте настройки STATIC_ROOT
3. Убедитесь, что whitenoise настроен

## 📊 Особенности Render

### Бесплатный план включает:
- ✅ 750 часов работы в месяц
- ✅ PostgreSQL база данных
- ✅ SSL сертификаты
- ✅ Автоматический деплой
- ✅ Логи и мониторинг
- ✅ Custom domains

### Ограничения бесплатного плана:
- ⚠️ Приложение "засыпает" после 15 минут неактивности
- ⚠️ Первый запрос после сна может быть медленным
- ⚠️ Ограниченное количество запросов

## 🔄 Обновления

Для обновления приложения:
1. Сделайте изменения в коде
2. Запушьте в GitHub
3. Render автоматически задеплоит обновления

## 💰 Стоимость

- **Бесплатно** для тестирования
- **$7/месяц** для всегда активного приложения (Starter план)

## 🎯 Рекомендации

### Для тестирования:
- Используйте бесплатный план
- Приложение будет "засыпать" при неактивности
- Идеально для демонстрации и тестирования

### Для продакшена:
- Рассмотрите Starter план ($7/месяц)
- Приложение будет работать 24/7
- Лучшая производительность

---

**🚀 Готово к деплою на Render! Следуйте инструкции выше!**
