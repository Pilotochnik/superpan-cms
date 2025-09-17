#!/bin/bash
# Скрипт обновления SuperPan на продакшен сервере

set -e  # Остановить при любой ошибке

echo "🔄 ОБНОВЛЕНИЕ SUPERPAN НА ПРОДАКШЕНЕ"
echo "===================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для цветного вывода
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Проверка прав пользователя
if [[ $EUID -eq 0 ]]; then
   print_error "Не запускайте этот скрипт от root! Используйте пользователя superpan."
   exit 1
fi

# Переменные
APP_DIR="/opt/superpan"
BACKUP_DIR="/opt/superpan/backups"
VENV_DIR="/opt/superpan/venv"
GIT_REPO="https://github.com/Pilotochnik/superpan-cms.git"

# Функция создания резервной копии
create_backup() {
    print_step "Создание резервной копии перед обновлением..."
    
    # Создаем резервную копию БД
    cd $APP_DIR
    source $VENV_DIR/bin/activate
    python manage.py backup_db create --description "before_update_$(date +%Y%m%d_%H%M%S)" --auto
    
    # Создаем резервную копию кода
    BACKUP_CODE_DIR="$BACKUP_DIR/code_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p $BACKUP_CODE_DIR
    cp -r $APP_DIR $BACKUP_CODE_DIR/
    
    print_status "Резервная копия создана: $BACKUP_CODE_DIR"
}

# Функция проверки статуса сервисов
check_services() {
    print_step "Проверка статуса сервисов..."
    
    if systemctl is-active --quiet superpan; then
        print_status "Django сервис активен"
    else
        print_warning "Django сервис не активен"
    fi
    
    if systemctl is-active --quiet superpan-telegram-bot; then
        print_status "Telegram бот активен"
    else
        print_warning "Telegram бот не активен"
    fi
}

# Функция остановки сервисов
stop_services() {
    print_step "Остановка сервисов..."
    
    sudo systemctl stop superpan-telegram-bot
    sudo systemctl stop superpan
    
    print_status "Сервисы остановлены"
}

# Функция обновления кода
update_code() {
    print_step "Обновление кода из Git..."
    
    cd $APP_DIR
    
    # Сохраняем локальные изменения
    git stash push -m "local_changes_before_update_$(date +%Y%m%d_%H%M%S)"
    
    # Получаем обновления
    git fetch origin master
    git reset --hard origin/master
    
    print_status "Код обновлен до последней версии"
}

# Функция обновления зависимостей
update_dependencies() {
    print_step "Обновление Python зависимостей..."
    
    cd $APP_DIR
    source $VENV_DIR/bin/activate
    
    # Обновляем pip
    pip install --upgrade pip
    
    # Обновляем зависимости
    pip install -r requirements.txt --upgrade
    
    print_status "Зависимости обновлены"
}

# Функция выполнения миграций
run_migrations() {
    print_step "Выполнение миграций базы данных..."
    
    cd $APP_DIR
    source $VENV_DIR/bin/activate
    
    # Проверяем, есть ли новые миграции
    python manage.py showmigrations --plan | grep -q "\[ \]" && HAS_MIGRATIONS=true || HAS_MIGRATIONS=false
    
    if [ "$HAS_MIGRATIONS" = true ]; then
        print_warning "Обнаружены новые миграции"
        python manage.py migrate
        print_status "Миграции выполнены"
    else
        print_status "Новых миграций нет"
    fi
}

# Функция сбора статических файлов
collect_static() {
    print_step "Сбор статических файлов..."
    
    cd $APP_DIR
    source $VENV_DIR/bin/activate
    
    python manage.py collectstatic --noinput
    
    print_status "Статические файлы собраны"
}

# Функция проверки конфигурации
check_config() {
    print_step "Проверка конфигурации Django..."
    
    cd $APP_DIR
    source $VENV_DIR/bin/activate
    
    python manage.py check --deploy
    
    print_status "Конфигурация проверена"
}

# Функция перезапуска сервисов
restart_services() {
    print_step "Перезапуск сервисов..."
    
    # Перезагружаем конфигурацию systemd
    sudo systemctl daemon-reload
    
    # Перезапускаем Django
    sudo systemctl restart superpan
    
    # Перезапускаем Telegram бота
    sudo systemctl restart superpan-telegram-bot
    
    # Перезапускаем Nginx
    sudo systemctl reload nginx
    
    print_status "Сервисы перезапущены"
}

# Функция проверки работоспособности
verify_deployment() {
    print_step "Проверка работоспособности..."
    
    # Ждем запуска сервисов
    sleep 5
    
    # Проверяем статус сервисов
    if systemctl is-active --quiet superpan; then
        print_status "✅ Django сервис запущен"
    else
        print_error "❌ Django сервис не запущен"
        return 1
    fi
    
    if systemctl is-active --quiet superpan-telegram-bot; then
        print_status "✅ Telegram бот запущен"
    else
        print_error "❌ Telegram бот не запущен"
        return 1
    fi
    
    # Проверяем доступность веб-интерфейса
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ | grep -q "200\|302"; then
        print_status "✅ Веб-интерфейс доступен"
    else
        print_error "❌ Веб-интерфейс недоступен"
        return 1
    fi
    
    # Проверяем состояние БД
    cd $APP_DIR
    source $VENV_DIR/bin/activate
    python db_monitor.py > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        print_status "✅ База данных в норме"
    else
        print_warning "⚠️ Проблемы с базой данных"
    fi
    
    print_status "Проверка завершена"
}

# Функция отката изменений
rollback() {
    print_error "Произошла ошибка! Выполняем откат..."
    
    # Останавливаем сервисы
    sudo systemctl stop superpan-telegram-bot
    sudo systemctl stop superpan
    
    # Восстанавливаем код из резервной копии
    LATEST_BACKUP=$(ls -t $BACKUP_DIR/code_backup_* | head -n 1)
    if [ -n "$LATEST_BACKUP" ]; then
        print_warning "Восстанавливаем код из: $LATEST_BACKUP"
        rm -rf $APP_DIR/*
        cp -r $LATEST_BACKUP/* $APP_DIR/
    fi
    
    # Восстанавливаем БД из последней резервной копии
    cd $APP_DIR
    source $VENV_DIR/bin/activate
    python restore_db.py --latest
    
    # Перезапускаем сервисы
    sudo systemctl restart superpan
    sudo systemctl restart superpan-telegram-bot
    
    print_warning "Откат выполнен"
}

# Основная функция обновления
main() {
    # Проверяем аргументы
    if [ "$1" = "--force" ]; then
        FORCE_UPDATE=true
    else
        FORCE_UPDATE=false
    fi
    
    # Проверяем, что мы в правильной директории
    if [ ! -f "$APP_DIR/manage.py" ]; then
        print_error "Не найден manage.py в $APP_DIR"
        exit 1
    fi
    
    print_status "Начинаем обновление SuperPan..."
    print_status "Директория приложения: $APP_DIR"
    
    # Проверяем статус сервисов до обновления
    check_services
    
    # Создаем резервную копию
    create_backup
    
    # Останавливаем сервисы
    stop_services
    
    # Обновляем код
    update_code
    
    # Обновляем зависимости
    update_dependencies
    
    # Выполняем миграции
    run_migrations
    
    # Собираем статические файлы
    collect_static
    
    # Проверяем конфигурацию
    check_config
    
    # Перезапускаем сервисы
    restart_services
    
    # Проверяем работоспособность
    if verify_deployment; then
        echo "===================================="
        print_status "✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!"
        echo "===================================="
        print_status "🌐 Веб-интерфейс: http://your-domain.com"
        print_status "📱 Telegram бот: @your_bot_username"
        print_status "📊 Статус сервисов:"
        sudo systemctl status superpan --no-pager -l
        sudo systemctl status superpan-telegram-bot --no-pager -l
        echo "===================================="
    else
        print_error "❌ ОБНОВЛЕНИЕ ЗАВЕРШИЛОСЬ С ОШИБКАМИ!"
        rollback
        exit 1
    fi
}

# Обработка сигналов для корректного завершения
trap 'print_error "Обновление прервано!"; rollback; exit 1' INT TERM

# Запуск основной функции
main "$@"
