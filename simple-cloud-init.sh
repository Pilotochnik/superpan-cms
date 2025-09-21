#!/bin/sh
# Простой Cloud-init скрипт для SuperPan

echo "🚀 НАЧИНАЕМ НАСТРОЙКУ SUPERPAN"
echo "==============================="

# Обновление системы
apt update && apt upgrade -y

# Установка базовых пакетов
apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib git curl

# Создание пользователя
useradd -m -s /bin/bash superpan

# Создание директории
mkdir -p /var/www/superpan
chown superpan:superpan /var/www/superpan

echo "✅ БАЗОВАЯ НАСТРОЙКА ЗАВЕРШЕНА"
echo "==============================="
echo "Следующие шаги выполните вручную:"
echo "1. Подключитесь по SSH"
echo "2. Клонируйте репозиторий"
echo "3. Настройте Django"
echo "==============================="
