# Makefile для SuperPan проекта

.PHONY: help install test lint format security clean run migrate collectstatic

# Цвета для вывода
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)SuperPan - Система управления строительными проектами$(NC)"
	@echo ""
	@echo "$(YELLOW)Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Установить зависимости
	@echo "$(YELLOW)Установка зависимостей...$(NC)"
	pip install -r requirements.txt

install-dev: ## Установить зависимости для разработки
	@echo "$(YELLOW)Установка зависимостей для разработки...$(NC)"
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

migrate: ## Применить миграции
	@echo "$(YELLOW)Применение миграций...$(NC)"
	python manage.py migrate

makemigrations: ## Создать миграции
	@echo "$(YELLOW)Создание миграций...$(NC)"
	python manage.py makemigrations

collectstatic: ## Собрать статические файлы
	@echo "$(YELLOW)Сбор статических файлов...$(NC)"
	python manage.py collectstatic --noinput

run: ## Запустить сервер разработки
	@echo "$(YELLOW)Запуск сервера разработки...$(NC)"
	python manage.py runserver 0.0.0.0:8000

run-bot: ## Запустить Telegram бота
	@echo "$(YELLOW)Запуск Telegram бота...$(NC)"
	python run_telegram_bot.py

test: ## Запустить тесты
	@echo "$(YELLOW)Запуск тестов...$(NC)"
	pytest --cov=. --cov-report=term-missing

test-verbose: ## Запустить тесты с подробным выводом
	@echo "$(YELLOW)Запуск тестов с подробным выводом...$(NC)"
	pytest -v --cov=. --cov-report=term-missing

lint: ## Проверить стиль кода
	@echo "$(YELLOW)Проверка стиля кода...$(NC)"
	flake8 .

format: ## Форматировать код
	@echo "$(YELLOW)Форматирование кода...$(NC)"
	black .
	isort .

format-check: ## Проверить форматирование кода
	@echo "$(YELLOW)Проверка форматирования...$(NC)"
	black --check .
	isort --check-only .

security: ## Проверить безопасность
	@echo "$(YELLOW)Проверка безопасности...$(NC)"
	bandit -r . -f json

quality: ## Полная проверка качества кода
	@echo "$(YELLOW)Полная проверка качества кода...$(NC)"
	python scripts/quality_check.py

quality-fix: ## Исправить форматирование и проверить качество
	@echo "$(YELLOW)Исправление форматирования и проверка качества...$(NC)"
	python scripts/quality_check.py --fix

clean: ## Очистить временные файлы
	@echo "$(YELLOW)Очистка временных файлов...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build

superuser: ## Создать суперпользователя
	@echo "$(YELLOW)Создание суперпользователя...$(NC)"
	python manage.py createsuperuser

backup: ## Создать резервную копию
	@echo "$(YELLOW)Создание резервной копии...$(NC)"
	python backup_manager.py backup

restore: ## Восстановить из резервной копии (требует BACKUP_NAME)
	@echo "$(YELLOW)Восстановление из резервной копии...$(NC)"
	@if [ -z "$(BACKUP_NAME)" ]; then \
		echo "$(RED)Ошибка: укажите BACKUP_NAME=имя_бэкапа$(NC)"; \
		exit 1; \
	fi
	python backup_manager.py restore $(BACKUP_NAME)

version-bump: ## Увеличить версию (требует TYPE=patch|minor|major)
	@echo "$(YELLOW)Увеличение версии...$(NC)"
	@if [ -z "$(TYPE)" ]; then \
		echo "$(RED)Ошибка: укажите TYPE=patch|minor|major$(NC)"; \
		exit 1; \
	fi
	python version_manager.py bump $(TYPE)

version-release: ## Создать релиз (требует TYPE=patch|minor|major)
	@echo "$(YELLOW)Создание релиза...$(NC)"
	@if [ -z "$(TYPE)" ]; then \
		echo "$(RED)Ошибка: укажите TYPE=patch|minor|major$(NC)"; \
		exit 1; \
	fi
	python version_manager.py release $(TYPE)

setup: install migrate collectstatic superuser ## Первоначальная настройка проекта
	@echo "$(GREEN)✅ Проект настроен!$(NC)"
	@echo "$(YELLOW)Теперь вы можете запустить сервер командой: make run$(NC)"

dev-setup: install-dev migrate collectstatic superuser ## Настройка для разработки
	@echo "$(GREEN)✅ Проект настроен для разработки!$(NC)"
	@echo "$(YELLOW)Теперь вы можете запустить сервер командой: make run$(NC)"

ci: format-check lint security test ## Команды для CI/CD
	@echo "$(GREEN)✅ Все проверки CI/CD пройдены!$(NC)"
