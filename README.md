# SuperPan - Система управления строительными проектами

## 🏗️ Описание

SuperPan - это комплексная система управления строительными проектами с интеграцией Telegram бота для мобильного доступа и уведомлений.

### ✨ Основные возможности

- **📊 Управление проектами** - создание, редактирование, отслеживание прогресса
- **📋 Канбан-доска задач** - визуальное управление задачами с системой статусов
- **👥 Управление участниками** - роли, права доступа, назначение задач
- **📱 Telegram интеграция** - авторизация через Telegram, уведомления
- **📦 Управление складом** - учет оборудования и материалов
- **💰 Сметы и расценки** - расчет стоимости проектов
- **📈 Аналитика** - отчеты и статистика по проектам
- **🔄 Система утверждений** - запросы на изменение статусов с уведомлениями

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.8+
- Django 5.2+
- PostgreSQL (для продакшена) или SQLite (для разработки)

### Установка

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd superpan
```

2. **Создайте виртуальное окружение:**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Настройте переменные окружения:**
```bash
cp env.example .env
```

Отредактируйте `.env` файл:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_BOT_USERNAME=your_bot_username
DATABASE_URL=sqlite:///db.sqlite3
```

5. **Примените миграции:**
```bash
python manage.py migrate
```

6. **Создайте суперпользователя:**
```bash
python manage.py createsuperuser
```

7. **Соберите статические файлы:**
```bash
python manage.py collectstatic
```

8. **Запустите сервер:**
```bash
python manage.py runserver
```

9. **Запустите Telegram бота (в отдельном терминале):**
```bash
python run_telegram_bot.py
```

## 🤖 Настройка Telegram бота

### Создание бота

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Создайте нового бота командой `/newbot`
3. Получите токен бота
4. Добавьте токен в `.env` файл

### Настройка веб-хука (для продакшена)

```bash
# Установите веб-хук для бота
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://yourdomain.com/telegram/webhook/"}'
```

## 👥 Система ролей

### Роли пользователей

- **👑 Администратор** - полный доступ ко всем функциям
- **👷 Прораб** - управление проектами и задачами
- **📋 Главный инженер** - техническое руководство
- **📦 Кладовщик** - управление складом
- **👤 Рабочий** - выполнение задач

### Права доступа

- **Создание проектов** - только администраторы
- **Управление задачами** - прорабы и выше
- **Изменение статусов** - рабочие (с утверждением админа)
- **Управление складом** - кладовщики и выше

## 📱 Мобильный доступ

### Через Telegram

1. Найдите вашего бота в Telegram
2. Отправьте команду `/start`
3. Следуйте инструкциям для авторизации
4. Используйте команды бота для управления задачами

### Через веб-интерфейс

- Откройте браузер на телефоне
- Перейдите по адресу вашего сервера
- Войдите через Telegram авторизацию

## 🔄 Система утверждений

### Как работает

1. **Рабочий** меняет статус задачи
2. **Система** создает запрос на утверждение
3. **Админ** получает уведомление в Telegram
4. **Админ** утверждает или отклоняет запрос
5. **Статус** обновляется автоматически

### Уведомления

- Все уведомления приходят в Telegram
- Ссылки ведут прямо на страницу утверждения
- История изменений сохраняется

## 🗄️ База данных

### Резервное копирование

Система автоматически создает бэкапы базы данных:

```bash
# Создать бэкап
python backup_manager.py backup

# Восстановить из бэкапа
python backup_manager.py restore backup_name
```

### Миграции

```bash
# Создать миграции
python manage.py makemigrations

# Применить миграции
python manage.py migrate
```

## 🚀 Деплой

### Heroku

1. Создайте приложение в Heroku
2. Подключите PostgreSQL
3. Установите переменные окружения
4. Деплойте код

```bash
git push heroku main
```

### Railway

1. Подключите GitHub репозиторий
2. Настройте переменные окружения
3. Деплойте автоматически

### Render

1. Создайте веб-сервис
2. Подключите PostgreSQL
3. Настройте переменные окружения
4. Деплойте

## 🔧 Конфигурация

### Переменные окружения

```env
# Основные настройки
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# База данных
DATABASE_URL=postgresql://user:password@host:port/database

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_BOT_USERNAME=your_bot_username

# Email (опционально)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Настройки безопасности

- CSRF защита включена
- Rate limiting настроен
- CORS настроен для API
- Безопасные cookies в продакшене

## 📊 API

### Основные endpoints

- `/api/projects/` - управление проектами
- `/api/tasks/` - управление задачами
- `/api/warehouse/` - управление складом
- `/telegram/webhook/` - веб-хук для Telegram

### Аутентификация

- Session-based для веб-интерфейса
- Token-based для API
- Telegram авторизация

## 🐛 Отладка

### Логи

Логи сохраняются в папке `logs/`:

```bash
tail -f logs/django.log
```

### Отладка Telegram бота

```bash
# Запуск с отладкой
python run_telegram_bot.py --debug
```

## 📞 Поддержка

### Документация

- [Django Documentation](https://docs.djangoproject.com/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

### Контакты

Для получения поддержки обращайтесь к администратору системы.

## 📄 Лицензия

Этот проект разработан для внутреннего использования компании.

---

**Версия:** 1.0.0  
**Последнее обновление:** Сентябрь 2025