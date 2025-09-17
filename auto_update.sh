#!/bin/bash
# Автоматическое обновление SuperPan через cron

# Логирование
LOG_FILE="/opt/superpan/logs/auto_update.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== НАЧАЛО АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ ==="

# Переходим в директорию приложения
cd /opt/superpan

# Проверяем, есть ли обновления
log "Проверка обновлений из Git..."
git fetch origin master

# Сравниваем локальную и удаленную ветки
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/master)

if [ "$LOCAL" = "$REMOTE" ]; then
    log "Обновлений нет. Завершение."
    exit 0
fi

log "Найдены обновления. Начинаем процесс обновления..."

# Проверяем, что сервисы работают
if ! systemctl is-active --quiet superpan; then
    log "ОШИБКА: Django сервис не активен. Пропускаем обновление."
    exit 1
fi

# Создаем резервную копию
log "Создание резервной копии..."
source venv/bin/activate
python manage.py backup_db create --description "auto_update_$(date +%Y%m%d_%H%M%S)" --auto

# Останавливаем Telegram бота
log "Остановка Telegram бота..."
systemctl stop superpan-telegram-bot

# Обновляем код
log "Обновление кода..."
git stash push -m "auto_update_$(date +%Y%m%d_%H%M%S)"
git reset --hard origin/master

# Обновляем зависимости
log "Обновление зависимостей..."
pip install -r requirements.txt --upgrade

# Выполняем миграции
log "Выполнение миграций..."
python manage.py migrate

# Собираем статические файлы
log "Сбор статических файлов..."
python manage.py collectstatic --noinput

# Перезапускаем сервисы
log "Перезапуск сервисов..."
systemctl restart superpan
systemctl restart superpan-telegram-bot

# Проверяем работоспособность
sleep 10

if systemctl is-active --quiet superpan && systemctl is-active --quiet superpan-telegram-bot; then
    log "✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО"
    
    # Отправляем уведомление в Telegram (если настроено)
    # curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
    #     -d "chat_id=$ADMIN_CHAT_ID" \
    #     -d "text=✅ SuperPan автоматически обновлен до последней версии"
else
    log "❌ ОШИБКА: Сервисы не запустились после обновления"
    
    # Откатываемся к предыдущей версии
    log "Выполнение отката..."
    git reset --hard "$LOCAL"
    systemctl restart superpan
    systemctl restart superpan-telegram-bot
    
    # Отправляем уведомление об ошибке
    # curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
    #     -d "chat_id=$ADMIN_CHAT_ID" \
    #     -d "text=❌ Ошибка автоматического обновления SuperPan. Выполнен откат."
    
    exit 1
fi

log "=== ЗАВЕРШЕНИЕ АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ ==="
