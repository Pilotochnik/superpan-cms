"""
Django команда для управления резервными копиями базы данных
Использование:
    python manage.py backup_db create --description "before_tests"
    python manage.py backup_db list
    python manage.py backup_db restore --file backups/db_backup_20250911_160000_before_tests.sqlite3
    python manage.py backup_db cleanup --keep 5
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import shutil
import sqlite3
import datetime
import json
from pathlib import Path


class Command(BaseCommand):
    help = 'Управление резервными копиями базы данных'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['create', 'restore', 'list', 'cleanup', 'verify'],
            help='Действие для выполнения'
        )
        parser.add_argument(
            '--file',
            help='Путь к файлу резервной копии (для restore/verify)'
        )
        parser.add_argument(
            '--description',
            default='manual',
            help='Описание резервной копии'
        )
        parser.add_argument(
            '--keep',
            type=int,
            default=10,
            help='Количество резервных копий для сохранения'
        )
        parser.add_argument(
            '--auto',
            action='store_true',
            help='Автоматический режим (без подтверждений)'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'create':
            self.create_backup(options)
        elif action == 'restore':
            self.restore_backup(options)
        elif action == 'list':
            self.list_backups()
        elif action == 'cleanup':
            self.cleanup_backups(options)
        elif action == 'verify':
            self.verify_backup(options)
    
    def create_backup(self, options):
        """Создает резервную копию базы данных"""
        try:
            db_path = settings.DATABASES['default']['NAME']
            backup_dir = Path('backups')
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            description = options['description']
            backup_filename = f"db_backup_{timestamp}_{description}.sqlite3"
            backup_path = backup_dir / backup_filename
            
            self.stdout.write(f"Создание резервной копии: {backup_filename}")
            
            # Копируем файл базы данных
            shutil.copy2(db_path, backup_path)
            
            # Создаем метаданные
            metadata = {
                "created_at": datetime.datetime.now().isoformat(),
                "description": description,
                "db_size": os.path.getsize(backup_path),
                "original_db": str(db_path).replace('\\', '/'),
                "backup_path": str(backup_path).replace('\\', '/')
            }
            
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(
                self.style.SUCCESS(f"Резервная копия создана: {backup_path}")
            )
            self.stdout.write(f"Размер: {metadata['db_size']} байт")
            
        except Exception as e:
            raise CommandError(f"Ошибка создания резервной копии: {e}")
    
    def restore_backup(self, options):
        """Восстанавливает базу данных из резервной копии"""
        backup_file = options['file']
        auto = options['auto']
        
        if not backup_file:
            raise CommandError("Укажите файл резервной копии с --file")
        
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            raise CommandError(f"Файл резервной копии не найден: {backup_path}")
        
        # Подтверждение в интерактивном режиме
        if not auto:
            self.stdout.write(
                self.style.WARNING("ВНИМАНИЕ: Это действие заменит текущую базу данных!")
            )
            confirm = input("Продолжить? (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write("Операция отменена")
                return
        
        try:
            db_path = settings.DATABASES['default']['NAME']
            
            # Создаем резервную копию текущей БД
            self.stdout.write("Создание резервной копии текущей БД...")
            current_backup = self.create_backup({'description': 'before_restore'})
            
            # Восстанавливаем базу данных
            shutil.copy2(backup_path, db_path)
            
            self.stdout.write(
                self.style.SUCCESS(f"База данных восстановлена из: {backup_path}")
            )
            self.stdout.write(f"Текущая БД сохранена как: {current_backup}")
            
        except Exception as e:
            raise CommandError(f"Ошибка восстановления: {e}")
    
    def list_backups(self):
        """Показывает список резервных копий"""
        try:
            backup_dir = Path('backups')
            if not backup_dir.exists():
                self.stdout.write("Резервные копии не найдены")
                return
            
            backups = []
            
            for backup_file in backup_dir.glob("db_backup_*.sqlite3"):
                metadata_file = backup_file.with_suffix('.json')
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        backups.append({
                            'file': backup_file,
                            'metadata': metadata
                        })
                    except json.JSONDecodeError:
                        # Старый файл метаданных с ошибками - используем информацию о файле
                        stat = backup_file.stat()
                        backups.append({
                            'file': backup_file,
                            'metadata': {
                                'created_at': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'description': 'legacy_corrupted',
                                'db_size': stat.st_size
                            }
                        })
                else:
                    # Старая резервная копия без метаданных
                    stat = backup_file.stat()
                    backups.append({
                        'file': backup_file,
                        'metadata': {
                            'created_at': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'description': 'legacy',
                            'db_size': stat.st_size
                        }
                    })
            
            # Сортируем по дате создания (новые сначала)
            backups.sort(key=lambda x: x['metadata']['created_at'], reverse=True)
            
            if not backups:
                self.stdout.write("Резервные копии не найдены")
                return
            
            self.stdout.write(f"\nДоступные резервные копии ({len(backups)}):")
            self.stdout.write("=" * 80)
            
            for i, backup in enumerate(backups, 1):
                metadata = backup['metadata']
                file_size = metadata.get('db_size', 0)
                size_mb = file_size / (1024 * 1024)
                
                self.stdout.write(f"{i:2d}. {backup['file'].name}")
                self.stdout.write(f"    Дата: {metadata['created_at']}")
                self.stdout.write(f"    Описание: {metadata.get('description', 'N/A')}")
                self.stdout.write(f"    Размер: {size_mb:.2f} MB")
                self.stdout.write("")
                
        except Exception as e:
            raise CommandError(f"Ошибка получения списка резервных копий: {e}")
    
    def cleanup_backups(self, options):
        """Удаляет старые резервные копии"""
        try:
            backup_dir = Path('backups')
            if not backup_dir.exists():
                self.stdout.write("Папка резервных копий не найдена")
                return
            
            keep_count = options['keep']
            auto = options['auto']
            
            backups = []
            for backup_file in backup_dir.glob("db_backup_*.sqlite3"):
                metadata_file = backup_file.with_suffix('.json')
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        backups.append({
                            'file': backup_file,
                            'metadata': metadata
                        })
                    except json.JSONDecodeError:
                        # Старый файл метаданных с ошибками - используем информацию о файле
                        stat = backup_file.stat()
                        backups.append({
                            'file': backup_file,
                            'metadata': {
                                'created_at': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'description': 'legacy_corrupted',
                                'db_size': stat.st_size
                            }
                        })
                else:
                    stat = backup_file.stat()
                    backups.append({
                        'file': backup_file,
                        'metadata': {
                            'created_at': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'description': 'legacy',
                            'db_size': stat.st_size
                        }
                    })
            
            backups.sort(key=lambda x: x['metadata']['created_at'], reverse=True)
            
            if len(backups) <= keep_count:
                self.stdout.write(f"Количество резервных копий ({len(backups)}) не превышает лимит ({keep_count})")
                return
            
            to_delete = backups[keep_count:]
            
            if not auto:
                self.stdout.write(f"Будет удалено {len(to_delete)} старых резервных копий:")
                for backup in to_delete:
                    self.stdout.write(f"  - {backup['file'].name}")
                
                confirm = input("Продолжить? (yes/no): ")
                if confirm.lower() != 'yes':
                    self.stdout.write("Операция отменена")
                    return
            
            deleted_count = 0
            for backup in to_delete:
                try:
                    backup['file'].unlink()
                    
                    metadata_file = backup['file'].with_suffix('.json')
                    if metadata_file.exists():
                        metadata_file.unlink()
                    
                    deleted_count += 1
                    self.stdout.write(f"Удалена: {backup['file'].name}")
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Не удалось удалить {backup['file'].name}: {e}")
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f"Удалено старых резервных копий: {deleted_count}")
            )
            
        except Exception as e:
            raise CommandError(f"Ошибка очистки старых резервных копий: {e}")
    
    def verify_backup(self, options):
        """Проверяет целостность резервной копии"""
        backup_file = options['file']
        
        if not backup_file:
            raise CommandError("Укажите файл резервной копии с --file")
        
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            raise CommandError(f"Файл резервной копии не найден: {backup_path}")
        
        try:
            self.stdout.write(f"Проверка целостности: {backup_path}")
            
            # Проверяем, что это валидная SQLite база
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            
            # Проверяем основные таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['accounts_user']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                self.stdout.write(
                    self.style.WARNING(f"Отсутствуют таблицы: {missing_tables}")
                )
            
            # Проверяем количество записей
            cursor.execute("SELECT COUNT(*) FROM accounts_user")
            user_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM projects_project")
            project_count = cursor.fetchone()[0]
            
            conn.close()
            
            self.stdout.write(self.style.SUCCESS("Резервная копия валидна"))
            self.stdout.write(f"Пользователей: {user_count}")
            self.stdout.write(f"Проектов: {project_count}")
            self.stdout.write(f"Таблиц: {len(tables)}")
            
        except sqlite3.Error as e:
            raise CommandError(f"Резервная копия повреждена: {e}")
        except Exception as e:
            raise CommandError(f"Ошибка проверки резервной копии: {e}")
