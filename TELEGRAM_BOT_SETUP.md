# 🤖 Настройка Telegram бота для SuperPan

## 📋 Обзор

Telegram бот обеспечивает мобильный доступ к системе SuperPan и отправляет уведомления о важных событиях.

### ✨ Возможности бота

- **🔐 Авторизация** - вход в систему через Telegram
- **📱 Мобильный доступ** - управление задачами с телефона
- **🔔 Уведомления** - автоматические уведомления о событиях
- **📊 Просмотр проектов** - список доступных проектов
- **📋 Создание задач** - добавление новых задач
- **✅ Утверждение статусов** - подтверждение изменений статусов

## 🚀 Создание бота

### 1. Создание через BotFather

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Введите имя бота (например: "SuperPan Bot")
4. Введите username бота (например: "superpan_bot")
5. Получите токен бота

### 2. Настройка команд

Отправьте BotFather команду `/setcommands` для вашего бота:

```
start - Начать работу с ботом
help - Показать справку
projects - Показать доступные проекты
tasks - Показать мои задачи
create_task - Создать новую задачу
```

### 3. Настройка описания

Отправьте BotFather команду `/setdescription`:

```
SuperPan - Система управления строительными проектами

Доступные команды:
/start - Авторизация в системе
/projects - Просмотр проектов
/tasks - Мои задачи
/create_task - Создать задачу
/help - Справка
```

## ⚙️ Настройка в системе

### 1. Переменные окружения

Добавьте в `.env` файл:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_USERNAME=superpan_bot
```

### 2. Запуск бота

```bash
# Запуск в режиме разработки
python run_telegram_bot.py

# Запуск в фоновом режиме (Linux/Mac)
nohup python run_telegram_bot.py &

# Запуск как сервис (Linux)
sudo systemctl start superpan-telegram-bot
```

### 3. Настройка веб-хука (для продакшена)

```bash
# Установите веб-хук
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://yourdomain.com/telegram/webhook/"}'

# Проверьте статус веб-хука
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

## 🔐 Система авторизации

### Как работает

1. **Пользователь** отправляет `/start` боту
2. **Бот** генерирует уникальный токен авторизации
3. **Пользователь** переходит по ссылке с токеном
4. **Система** авторизует пользователя через токен
5. **Бот** получает уведомление об успешной авторизации

### Настройка авторизации

1. **В админ-панели** перейдите в "Пользователи"
2. **Нажмите** "Зарегистрировать через Telegram"
3. **Введите** Telegram ID пользователя
4. **Система** создаст токен авторизации
5. **Пользователь** использует токен для входа

## 📱 Команды бота

### Основные команды

- `/start` - Начать работу, авторизация
- `/help` - Показать справку
- `/projects` - Список доступных проектов
- `/tasks` - Мои задачи
- `/create_task` - Создать новую задачу

### Интерактивные функции

- **Кнопки** для быстрого доступа к функциям
- **Inline клавиатуры** для выбора проектов
- **Формы** для создания задач
- **Уведомления** с кнопками действий

## 🔔 Система уведомлений

### Типы уведомлений

1. **Запросы на изменение статуса**
   - Отправляется админам проекта
   - Содержит ссылку на страницу утверждения
   - Кнопки для быстрого утверждения

2. **Уведомления о новых задачах**
   - Назначенным исполнителям
   - С описанием задачи и сроками

3. **Обновления статусов**
   - Подтверждение изменений
   - Уведомления об отклонениях

### Настройка уведомлений

```python
# В коде системы
from telegram_bot.bot import send_message_to_user

# Отправка уведомления
send_message_to_user(
    user_id=123456789,
    text="Новая задача назначена на вас",
    reply_markup=inline_keyboard
)
```

## 🛠️ Разработка и отладка

### Структура кода

```
telegram_bot/
├── bot.py              # Основной класс бота
├── management/
│   └── commands/       # Django команды
└── __init__.py
```

### Добавление новых команд

1. **Создайте метод** в классе `ConstructionBot`
2. **Добавьте обработчик** в `setup_handlers`
3. **Обновите список команд** в BotFather

```python
async def new_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Описание новой команды"""
    await update.message.reply_text("Ответ пользователю")
```

### Отладка

```bash
# Запуск с подробными логами
python run_telegram_bot.py --debug

# Проверка статуса бота
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"

# Получение обновлений
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
```

## 🔧 Конфигурация

### Настройки в settings.py

```python
# Telegram настройки
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_USERNAME = config('TELEGRAM_BOT_USERNAME')
TELEGRAM_WEBHOOK_URL = config('TELEGRAM_WEBHOOK_URL', default='')

# Настройки уведомлений
TELEGRAM_NOTIFICATIONS_ENABLED = True
TELEGRAM_ADMIN_NOTIFICATIONS = True
```

### Настройки безопасности

```python
# Валидация веб-хуков
TELEGRAM_WEBHOOK_SECRET = config('TELEGRAM_WEBHOOK_SECRET', default='')

# Ограничение доступа
TELEGRAM_ALLOWED_USERS = config('TELEGRAM_ALLOWED_USERS', default='')
```

## 📊 Мониторинг

### Логи бота

```bash
# Просмотр логов
tail -f logs/django.log | grep "TELEGRAM"

# Логи в реальном времени
python run_telegram_bot.py --verbose
```

### Метрики

- Количество активных пользователей
- Количество отправленных сообщений
- Статистика команд
- Ошибки и исключения

### Алерты

Настройте уведомления о:
- Ошибках бота
- Превышении лимитов API
- Проблемах с авторизацией

## 🚀 Деплой

### Локальная разработка

```bash
# Запуск бота локально
python run_telegram_bot.py
```

### Продакшен

1. **Настройте веб-хук**
2. **Установите переменные окружения**
3. **Запустите как сервис**

```bash
# Systemd сервис
sudo systemctl enable superpan-telegram-bot
sudo systemctl start superpan-telegram-bot
```

### Docker

```dockerfile
# Dockerfile для бота
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run_telegram_bot.py"]
```

## 🆘 Устранение неполадок

### Частые проблемы

1. **Бот не отвечает**
   - Проверьте токен бота
   - Проверьте интернет соединение
   - Проверьте логи ошибок

2. **Авторизация не работает**
   - Проверьте настройки базы данных
   - Проверьте Telegram ID пользователя
   - Проверьте срок действия токена

3. **Уведомления не приходят**
   - Проверьте настройки уведомлений
   - Проверьте права пользователей
   - Проверьте логи отправки

### Команды для диагностики

```bash
# Проверка статуса бота
curl "https://api.telegram.org/bot<TOKEN>/getMe"

# Проверка веб-хука
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Получение последних обновлений
curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
```

## 📞 Поддержка

### Документация

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [python-telegram-bot](https://python-telegram-bot.readthedocs.io/)

### Контакты

Для получения поддержки по настройке бота обращайтесь к администратору системы.

---

**Удачной настройки! 🤖**