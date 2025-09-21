#!/bin/sh
# Cloud-init скрипт для автоматической настройки SuperPan на Timeweb VPS

echo "🚀 НАЧИНАЕМ АВТОМАТИЧЕСКУЮ НАСТРОЙКУ SUPERPAN"
echo "=============================================="

# Обновление системы
apt update && apt upgrade -y

# Установка необходимых пакетов
apt install -y \
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
    ufw \
    certbot \
    python3-certbot-nginx

# Создание пользователя для приложения
useradd -m -s /bin/bash superpan
usermod -aG sudo superpan

# Создание директории приложения
mkdir -p /var/www/superpan
chown superpan:superpan /var/www/superpan

# Переключение на пользователя superpan
cd /var/www/superpan

# Клонирование репозитория
su - superpan -c "git clone https://github.com/Pilotochnik/superpan-cms.git ."

# Создание виртуального окружения
su - superpan -c "cd /var/www/superpan && python3 -m venv venv"
su - superpan -c "cd /var/www/superpan && ./venv/bin/pip install --upgrade pip"

# Установка зависимостей
su - superpan -c "cd /var/www/superpan && ./venv/bin/pip install -r requirements.txt"

# Настройка PostgreSQL
sudo -u postgres psql << EOF
CREATE DATABASE superpan_db;
CREATE USER superpan_user WITH PASSWORD 'superpan_secure_password_2024';
ALTER ROLE superpan_user SET client_encoding TO 'utf8';
ALTER ROLE superpan_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE superpan_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE superpan_db TO superpan_user;
\q
EOF

# Настройка переменных окружения
su - superpan -c "cd /var/www/superpan && tee .env << 'EOF'
DEBUG=False
SECRET_KEY=superpan-timeweb-secret-key-2024-change-me
DATABASE_URL=postgresql://superpan_user:superpan_secure_password_2024@localhost/superpan_db
TELEGRAM_BOT_TOKEN=8367784150:AAF7m6ZWW9BcoV17YOqnkLp1ScPmYpssy_E
TELEGRAM_BOT_USERNAME=projectpanell_bot
TELEGRAM_WEBHOOK_SECRET=superpan_webhook_secret_2024
ALLOWED_HOSTS=localhost,127.0.0.1,31.31.196.16
SENTRY_DSN=
EOF'"

# Выполнение миграций
su - superpan -c "cd /var/www/superpan && ./venv/bin/python manage.py migrate"
su - superpan -c "cd /var/www/superpan && ./venv/bin/python manage.py createsuperuser --noinput --username admin --email admin@superpan.ru"
su - superpan -c "cd /var/www/superpan && ./venv/bin/python manage.py init_production"
su - superpan -c "cd /var/www/superpan && ./venv/bin/python manage.py collectstatic --noinput"

# Настройка Gunicorn
su - superpan -c "cd /var/www/superpan && tee gunicorn.conf.py << 'EOF'
bind = "127.0.0.1:8000"
workers = 2
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
EOF'"

# Создание systemd сервиса для Django
tee /etc/systemd/system/superpan.service << EOF
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

# Создание systemd сервиса для Telegram бота
tee /etc/systemd/system/superpan-telegram-bot.service << EOF
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

# Настройка Nginx
tee /etc/nginx/sites-available/superpan << EOF
server {
    listen 80;
    server_name _;

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
ln -sf /etc/nginx/sites-available/superpan /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации Nginx
nginx -t

# Запуск сервисов
systemctl daemon-reload
systemctl enable superpan
systemctl enable superpan-telegram-bot
systemctl enable nginx
systemctl enable postgresql

systemctl start superpan
systemctl start superpan-telegram-bot
systemctl restart nginx

# Настройка файрвола
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "=============================================="
echo "✅ АВТОМАТИЧЕСКАЯ НАСТРОЙКА ЗАВЕРШЕНА!"
echo "=============================================="
echo "🌐 Веб-приложение: http://$(curl -s ifconfig.me)"
echo "📱 Telegram бот: @projectpanell_bot"
echo "🔧 Управление: sudo systemctl status superpan"
echo "📊 Логи: sudo journalctl -u superpan -f"
echo "=============================================="
