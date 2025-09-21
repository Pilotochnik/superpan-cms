#!/bin/bash
# Скрипт деплоя SuperPan на Reg.ru хостинг

echo "🚀 ДЕПЛОЙ SUPERPAN НА REG.RU"
echo "============================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

print_status "Обновление системы..."
sudo apt update && sudo apt upgrade -y

print_status "Установка зависимостей..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    nginx \
    postgresql \
    postgresql-contrib \
    git \
    curl \
    htop \
    ufw

print_status "Создание пользователя для приложения..."
if ! id "superpan" &>/dev/null; then
    sudo useradd -m -s /bin/bash superpan
    sudo usermod -aG sudo superpan
fi

print_status "Создание директории приложения..."
sudo mkdir -p /var/www/superpan
sudo chown superpan:superpan /var/www/superpan

print_status "Клонирование репозитория..."
cd /var/www/superpan
if [ ! -d ".git" ]; then
    sudo -u superpan git clone https://github.com/Pilotochnik/superpan-cms.git .
else
    sudo -u superpan git pull origin master
fi

print_status "Создание виртуального окружения..."
sudo -u superpan python3 -m venv venv
sudo -u superpan ./venv/bin/pip install --upgrade pip

print_status "Установка Python зависимостей..."
sudo -u superpan ./venv/bin/pip install -r requirements.txt

print_status "Настройка PostgreSQL..."
sudo -u postgres psql << EOF
CREATE DATABASE superpan_db;
CREATE USER superpan_user WITH PASSWORD 'superpan_secure_password_2024';
ALTER ROLE superpan_user SET client_encoding TO 'utf8';
ALTER ROLE superpan_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE superpan_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE superpan_db TO superpan_user;
\q
EOF

print_status "Настройка переменных окружения..."
sudo -u superpan tee .env << EOF
DEBUG=False
SECRET_KEY=superpan-regru-secret-key-2024-change-me
DATABASE_URL=postgresql://superpan_user:superpan_secure_password_2024@localhost/superpan_db
TELEGRAM_BOT_TOKEN=8367784150:AAF7m6ZWW9BcoV17YOqnkLp1ScPmYpssy_E
TELEGRAM_BOT_USERNAME=projectpanell_bot
TELEGRAM_WEBHOOK_SECRET=superpan_webhook_secret_2024
ALLOWED_HOSTS=your-domain.ru,www.your-domain.ru,localhost,127.0.0.1
SENTRY_DSN=
EOF

print_status "Выполнение миграций..."
sudo -u superpan ./venv/bin/python manage.py migrate

print_status "Создание суперпользователя..."
sudo -u superpan ./venv/bin/python manage.py createsuperuser --noinput --username admin --email admin@superpan.ru

print_status "Инициализация данных..."
sudo -u superpan ./venv/bin/python manage.py init_production

print_status "Сбор статических файлов..."
sudo -u superpan ./venv/bin/python manage.py collectstatic --noinput

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

print_status "Создание systemd сервиса..."
sudo tee /etc/systemd/system/superpan.service << EOF
[Unit]
Description=SuperPan Django Application
After=network.target

[Service]
User=superpan
Group=superpan
WorkingDirectory=/var/www/superpan
Environment="PATH=/var/www/superpan/venv/bin"
ExecStart=/var/www/superpan/venv/bin/gunicorn --config gunicorn.conf.py superpan.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

print_status "Создание сервиса для Telegram бота..."
sudo tee /etc/systemd/system/superpan-telegram-bot.service << EOF
[Unit]
Description=SuperPan Telegram Bot
After=network.target

[Service]
User=superpan
Group=superpan
WorkingDirectory=/var/www/superpan
Environment="PATH=/var/www/superpan/venv/bin"
ExecStart=/var/www/superpan/venv/bin/python run_telegram_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

print_status "Настройка Nginx..."
sudo tee /etc/nginx/sites-available/superpan << EOF
server {
    listen 80;
    server_name your-domain.ru www.your-domain.ru;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/superpan;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        root /var/www/superpan;
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

print_status "Запуск сервисов..."
sudo systemctl daemon-reload
sudo systemctl enable superpan
sudo systemctl enable superpan-telegram-bot
sudo systemctl enable nginx
sudo systemctl enable postgresql

sudo systemctl start superpan
sudo systemctl start superpan-telegram-bot
sudo systemctl restart nginx

print_status "Проверка статуса сервисов..."
sudo systemctl status superpan --no-pager
sudo systemctl status superpan-telegram-bot --no-pager
sudo systemctl status nginx --no-pager

echo "================================"
echo "✅ ДЕПЛОЙ ЗАВЕРШЕН УСПЕШНО!"
echo "================================"
echo "🌐 Веб-приложение: http://your-domain.ru"
echo "📱 Telegram бот: @projectpanell_bot"
echo "🔧 Управление: sudo systemctl status superpan"
echo "📊 Логи: sudo journalctl -u superpan -f"
echo "================================"
echo "⚠️  НЕ ЗАБУДЬТЕ:"
echo "1. Пройти идентификацию в Reg.ru"
echo "2. Настроить домен в панели управления"
echo "3. Получить SSL сертификат"
echo "================================"
