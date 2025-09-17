#!/bin/bash
# Скрипт автоматического деплоя SuperPan на продакшен сервер

set -e  # Остановить при любой ошибке

echo "🚀 ДЕПЛОЙ SUPERPAN НА ПРОДАКШЕН"
echo "================================"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для цветного вывода
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав суперпользователя
if [[ $EUID -eq 0 ]]; then
   print_error "Не запускайте этот скрипт от root! Используйте обычного пользователя."
   exit 1
fi

# Обновление системы
print_status "Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
print_status "Установка зависимостей..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    nginx \
    postgresql \
    postgresql-contrib \
    redis-server \
    git \
    curl \
    certbot \
    python3-certbot-nginx \
    htop \
    ufw \
    fail2ban

# Создание пользователя для приложения
print_status "Настройка пользователя приложения..."
if ! id "superpan" &>/dev/null; then
    sudo useradd -m -s /bin/bash superpan
    sudo usermod -aG sudo superpan
fi

# Создание директории приложения
print_status "Создание директории приложения..."
sudo mkdir -p /opt/superpan
sudo chown superpan:superpan /opt/superpan

# Клонирование репозитория
print_status "Клонирование репозитория..."
cd /opt/superpan
if [ ! -d ".git" ]; then
    sudo -u superpan git clone https://github.com/Pilotochnik/superpan-cms.git .
else
    sudo -u superpan git pull origin master
fi

# Создание виртуального окружения
print_status "Создание виртуального окружения..."
sudo -u superpan python3 -m venv venv
sudo -u superpan ./venv/bin/pip install --upgrade pip

# Установка зависимостей
print_status "Установка Python зависимостей..."
sudo -u superpan ./venv/bin/pip install -r requirements.txt

# Настройка PostgreSQL
print_status "Настройка PostgreSQL..."
sudo -u postgres psql << EOF
CREATE DATABASE superpan_db;
CREATE USER superpan_user WITH PASSWORD 'your_secure_password_here';
ALTER ROLE superpan_user SET client_encoding TO 'utf8';
ALTER ROLE superpan_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE superpan_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE superpan_db TO superpan_user;
\q
EOF

# Настройка переменных окружения
print_status "Настройка переменных окружения..."
sudo -u superpan cp env.example .env
sudo -u superpan tee .env << EOF
DEBUG=False
SECRET_KEY=your_secret_key_here
DATABASE_URL=postgresql://superpan_user:your_secure_password_here@localhost/superpan_db
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret
SENTRY_DSN=your_sentry_dsn
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
EOF

# Выполнение миграций
print_status "Выполнение миграций..."
sudo -u superpan ./venv/bin/python manage.py migrate

# Создание суперпользователя
print_status "Создание суперпользователя..."
sudo -u superpan ./venv/bin/python manage.py createsuperuser --noinput --username admin --email admin@example.com

# Сбор статических файлов
print_status "Сбор статических файлов..."
sudo -u superpan ./venv/bin/python manage.py collectstatic --noinput

# Настройка Gunicorn
print_status "Настройка Gunicorn..."
sudo -u superpan tee gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
daemon = False
user = "superpan"
group = "superpan"
tmp_upload_dir = None
EOF

# Создание systemd сервиса для Gunicorn
print_status "Создание systemd сервиса..."
sudo tee /etc/systemd/system/superpan.service << EOF
[Unit]
Description=SuperPan Django Application
After=network.target

[Service]
User=superpan
Group=superpan
WorkingDirectory=/opt/superpan
Environment="PATH=/opt/superpan/venv/bin"
ExecStart=/opt/superpan/venv/bin/gunicorn --config gunicorn.conf.py superpan.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Создание systemd сервиса для Telegram бота
print_status "Создание сервиса для Telegram бота..."
sudo tee /etc/systemd/system/superpan-telegram-bot.service << EOF
[Unit]
Description=SuperPan Telegram Bot
After=network.target

[Service]
User=superpan
Group=superpan
WorkingDirectory=/opt/superpan
Environment="PATH=/opt/superpan/venv/bin"
ExecStart=/opt/superpan/venv/bin/python run_telegram_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Настройка Nginx
print_status "Настройка Nginx..."
sudo tee /etc/nginx/sites-available/superpan << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /opt/superpan;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        root /opt/superpan;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Активация сайта Nginx
sudo ln -sf /etc/nginx/sites-available/superpan /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации Nginx
sudo nginx -t

# Настройка файрвола
print_status "Настройка файрвола..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Настройка fail2ban
print_status "Настройка fail2ban..."
sudo tee /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
EOF

# Настройка автоматических бэкапов
print_status "Настройка автоматических бэкапов..."
sudo -u superpan ./venv/bin/python setup_auto_backup.py

# Создание cron задачи для мониторинга
print_status "Настройка мониторинга..."
sudo -u superpan crontab << EOF
# Мониторинг БД каждые 6 часов
0 */6 * * * cd /opt/superpan && ./venv/bin/python db_monitor.py

# Автоматические бэкапы каждые 3 дня
0 2 */3 * * cd /opt/superpan && ./venv/bin/python manage.py auto_backup --force

# Очистка старых бэкапов каждую неделю
0 3 * * 0 cd /opt/superpan && ./venv/bin/python manage.py backup_db cleanup --keep 10 --auto
EOF

# Запуск сервисов
print_status "Запуск сервисов..."
sudo systemctl daemon-reload
sudo systemctl enable superpan
sudo systemctl enable superpan-telegram-bot
sudo systemctl enable nginx
sudo systemctl enable postgresql
sudo systemctl enable redis-server
sudo systemctl enable fail2ban

sudo systemctl start superpan
sudo systemctl start superpan-telegram-bot
sudo systemctl restart nginx

# Настройка SSL сертификата
print_warning "Настройка SSL сертификата..."
print_warning "Замените 'your-domain.com' на ваш реальный домен и выполните:"
print_warning "sudo certbot --nginx -d your-domain.com -d www.your-domain.com"

# Проверка статуса сервисов
print_status "Проверка статуса сервисов..."
sudo systemctl status superpan --no-pager
sudo systemctl status superpan-telegram-bot --no-pager
sudo systemctl status nginx --no-pager

echo "================================"
echo "✅ ДЕПЛОЙ ЗАВЕРШЕН УСПЕШНО!"
echo "================================"
echo "🌐 Веб-приложение: http://your-domain.com"
echo "📱 Telegram бот: @your_bot_username"
echo "🔧 Управление: sudo systemctl status superpan"
echo "📊 Логи: sudo journalctl -u superpan -f"
echo "================================"
