"""
Django команда для автоматического резервного копирования
Проверяет, когда была создана последняя резервная копия,
и создает новую, если прошло больше 3 дней
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
import os
import json
from pathlib import Path
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Автоматическое резервное копирование каждые 3 дня'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно создать резервную копию, даже если не прошло 3 дня'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='Количество дней между резервными копиями (по умолчанию 3)'
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Только проверить, нужна ли резервная копия, не создавать'
        )
    
    def handle(self, *args, **options):
        force = options['force']
        days = options['days']
        check_only = options['check_only']
        
        if check_only:
            self.check_backup_needed(days)
        else:
            self.auto_backup(force, days)
    
    def check_backup_needed(self, days):
        """Проверяет, нужна ли резервная копия"""
        try:
            last_backup = self.get_last_backup()
            
            if not last_backup:
                self.stdout.write(
                    self.style.WARNING("Резервные копии не найдены - нужна резервная копия")
                )
                return True
            
            last_backup_date = self.get_backup_date(last_backup)
            # Убеждаемся, что оба времени имеют одинаковый тип (aware или naive)
            now = timezone.now()
            if last_backup_date.tzinfo is None:
                last_backup_date = timezone.make_aware(last_backup_date)
            elif now.tzinfo is None:
                now = timezone.make_aware(now)
            
            days_since_backup = (now - last_backup_date).days
            
            if days_since_backup >= days:
                self.stdout.write(
                    self.style.WARNING(f"Последняя резервная копия была {days_since_backup} дней назад - нужна новая")
                )
                return True
            else:
                remaining_days = days - days_since_backup
                self.stdout.write(
                    self.style.SUCCESS(f"Резервная копия актуальна. Следующая через {remaining_days} дней")
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Ошибка проверки: {e}")
            )
            return True
    
    def auto_backup(self, force, days):
        """Автоматически создает резервную копию при необходимости"""
        try:
            # Проверяем, нужна ли резервная копия
            if not force:
                if not self.check_backup_needed(days):
                    self.stdout.write("Резервная копия не нужна")
                    return
            
            # Создаем резервную копию
            self.stdout.write("Создание автоматической резервной копии...")
            
            # Импортируем команду создания резервной копии
            from django.core.management import call_command
            
            # Создаем резервную копию
            call_command('backup_db', 'create', '--description', 'auto_3days', '--auto')
            
            self.stdout.write(
                self.style.SUCCESS("Автоматическая резервная копия создана успешно!")
            )
            
            # Очищаем старые резервные копии (оставляем 10)
            self.stdout.write("Очистка старых резервных копий...")
            call_command('backup_db', 'cleanup', '--keep', '10', '--auto')
            
            # Показываем статистику
            self.show_backup_stats()
            
        except Exception as e:
            raise CommandError(f"Ошибка автоматического резервного копирования: {e}")
    
    def get_last_backup(self):
        """Получает последнюю резервную копию"""
        try:
            backup_dir = Path('backups')
            if not backup_dir.exists():
                return None
            
            backup_files = list(backup_dir.glob("db_backup_*.sqlite3"))
            if not backup_files:
                return None
            
            # Сортируем по времени модификации (новые сначала)
            return max(backup_files, key=lambda x: x.stat().st_mtime)
            
        except Exception:
            return None
    
    def get_backup_date(self, backup_file):
        """Получает дату создания резервной копии"""
        try:
            # Сначала пробуем получить из метаданных
            metadata_file = backup_file.with_suffix('.json')
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    return datetime.fromisoformat(metadata['created_at'].replace('Z', '+00:00'))
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass
            
            # Если метаданные недоступны, используем время модификации файла
            return datetime.fromtimestamp(backup_file.stat().st_mtime, tz=timezone.utc)
            
        except Exception:
            # В крайнем случае используем текущее время
            return timezone.now()
    
    def show_backup_stats(self):
        """Показывает статистику резервных копий"""
        try:
            backup_dir = Path('backups')
            if not backup_dir.exists():
                return
            
            backup_files = list(backup_dir.glob("db_backup_*.sqlite3"))
            total_size = sum(f.stat().st_size for f in backup_files)
            size_mb = total_size / (1024 * 1024)
            
            self.stdout.write(f"\n📊 Статистика резервных копий:")
            self.stdout.write(f"   Всего копий: {len(backup_files)}")
            self.stdout.write(f"   Общий размер: {size_mb:.2f} MB")
            
            # Показываем последние 3 копии
            if backup_files:
                sorted_files = sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True)
                self.stdout.write(f"\n📁 Последние резервные копии:")
                for i, backup_file in enumerate(sorted_files[:3], 1):
                    stat = backup_file.stat()
                    size_mb = stat.st_size / (1024 * 1024)
                    date_str = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                    self.stdout.write(f"   {i}. {backup_file.name} ({size_mb:.2f} MB, {date_str})")
            
        except Exception as e:
            self.stdout.write(f"Ошибка получения статистики: {e}")
    
    def send_notification(self, message):
        """Отправляет уведомление о резервном копировании"""
        try:
            # Здесь можно добавить отправку уведомлений (email, Telegram, etc.)
            # Пока просто логируем
            self.stdout.write(f"📧 Уведомление: {message}")
        except Exception as e:
            self.stdout.write(f"Ошибка отправки уведомления: {e}")
