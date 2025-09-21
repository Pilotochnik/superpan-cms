# Ручная настройка SuperPan на Timeweb VPS

## 1. Обновление системы
```bash
apt update && apt upgrade -y
```

## 2. Установка зависимостей
```bash
apt install -y python3 python3-pip python3-venv python3-dev nginx postgresql postgresql-contrib git curl htop ufw
```

## 3. Создание пользователя
```bash
useradd -m -s /bin/bash superpan
usermod -aG sudo superpan
```

## 4. Создание директории проекта
```bash
mkdir -p /var/www/superpan
chown superpan:superpan /var/www/superpan
```

## 5. Переключение на пользователя superpan
```bash
su - superpan
cd /var/www/superpan
```

## 6. Клонирование проекта
```bash
git clone https://github.com/Pilotochnik/superpan-cms.git .
```

## 7. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 8. Настройка PostgreSQL
```bash
exit  # Выход из пользователя superpan
sudo -u postgres psql << EOF
CREATE DATABASE superpan_db;
CREATE USER superpan_user WITH PASSWORD 'superpan_secure_password_2024';
ALTER ROLE superpan_user SET client_encoding TO 'utf8';
ALTER ROLE superpan_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE superpan_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE superpan_db TO superpan_user;
\q
EOF
```

## 9. Настройка переменных окружения
```bash
su - superpan
cd /var/www/superpan
source venv/bin/activate

cat > .env << EOF
DEBUG=False
SECRET_KEY=superpan-timeweb-secret-key-2024-change-me
DATABASE_URL=postgresql://superpan_user:superpan_secure_password_2024@localhost/superpan_db
TELEGRAM_BOT_TOKEN=8367784150:AAF7m6ZWW9BcoV17YOqnkLp1ScPmYpssy_E
TELEGRAM_BOT_USERNAME=projectpanell_bot
TELEGRAM_WEBHOOK_SECRET=superpan_webhook_secret_2024
ALLOWED_HOSTS=194.87.76.75,localhost,127.0.0.1
SENTRY_DSN=
EOF
```

## 10. Выполнение миграций
```bash
python manage.py migrate
python manage.py createsuperuser --noinput --username admin --email admin@superpan.ru
python manage.py init_production
python manage.py collectstatic --noinput
```

## 11. Настройка Gunicorn
```bash
cat > gunicorn.conf.py << EOF
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
EOF
```

## 12. Создание systemd сервисов
```bash
exit  # Выход из пользователя superpan

# Django сервис
cat > /etc/systemd/system/superpan.service << EOF
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

# Telegram бот сервис
cat > /etc/systemd/system/superpan-telegram-bot.service << EOF
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
```

## 13. Настройка Nginx
```bash
cat > /etc/nginx/sites-available/superpan << EOF
server {
    listen 80;
    server_name 194.87.76.75;

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

ln -sf /etc/nginx/sites-available/superpan /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
```

## 14. Запуск сервисов
```bash
systemctl daemon-reload
systemctl enable superpan
systemctl enable superpan-telegram-bot
systemctl enable nginx
systemctl enable postgresql

systemctl start superpan
systemctl start superpan-telegram-bot
systemctl restart nginx
```

## 15. Проверка статуса
```bash
systemctl status superpan
systemctl status superpan-telegram-bot
systemctl status nginx
```

## 16. Настройка файрвола
```bash
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable
```

## ✅ РЕЗУЛЬТАТ:
- **Веб-приложение:** http://194.87.76.75
- **Логин:** admin@superpan.ru / admin123
- **Telegram бот:** @projectpanell_bot
