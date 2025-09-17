#!/usr/bin/env python
"""
Менеджер резервного копирования базы данных
Автоматически создает и восстанавливает резервные копии
"""

import os
import sys
import shutil
import sqlite3
import datetime
import json
from pathlib import Path

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'superpan.settings')
import django
django.setup()

from django.conf import settings


class DatabaseBackupManager:
    """Менеджер резервного копирования базы данных"""
    
    def __init__(self):
        self.db_path = settings.DATABASES['default']['NAME']
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self, description="manual"):
        """Создает резервную копию базы данных"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"db_backup_{timestamp}_{description}.sqlite3"
            backup_path = self.backup_dir / backup_filename
            
            print(f"[BACKUP] Создание резервной копии: {backup_filename}")
            
            # Копируем файл базы данных
            shutil.copy2(self.db_path, backup_path)
            
            # Создаем метаданные резервной копии
            metadata = {
                "created_at": datetime.datetime.now().isoformat(),
                "description": description,
                "db_size": os.path.getsize(backup_path),
                "original_db": self.db_path,
                "backup_path": str(backup_path)
            }
            
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"[OK] Резервная копия создана: {backup_path}")
            print(f"[INFO] Размер: {metadata['db_size']} байт")
            
            return str(backup_path)
            
        except Exception as e:
            print(f"[ERROR] Ошибка создания резервной копии: {e}")
            return None
    
    def restore_backup(self, backup_path):
        """Восстанавливает базу данных из резервной копии"""
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                print(f"[ERROR] Файл резервной копии не найден: {backup_path}")
                return False
            
            print(f"[RESTORE] Восстановление из резервной копии: {backup_path}")
            
            # Создаем резервную копию текущей БД перед восстановлением
            current_backup = self.create_backup("before_restore")
            
            # Восстанавливаем базу данных
            shutil.copy2(backup_path, self.db_path)
            
            print(f"[OK] База данных восстановлена из: {backup_path}")
            print(f"[INFO] Текущая БД сохранена как: {current_backup}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Ошибка восстановления: {e}")
            return False
    
    def list_backups(self):
        """Показывает список доступных резервных копий"""
        try:
            backups = []
            
            for backup_file in self.backup_dir.glob("db_backup_*.sqlite3"):
                metadata_file = backup_file.with_suffix('.json')
                
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    backups.append({
                        'file': backup_file,
                        'metadata': metadata
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
            
            return backups
            
        except Exception as e:
            print(f"[ERROR] Ошибка получения списка резервных копий: {e}")
            return []
    
    def show_backups(self):
        """Показывает список резервных копий в консоли"""
        backups = self.list_backups()
        
        if not backups:
            print("[INFO] Резервные копии не найдены")
            return
        
        print(f"\n[BACKUPS] Доступные резервные копии ({len(backups)}):")
        print("=" * 80)
        
        for i, backup in enumerate(backups, 1):
            metadata = backup['metadata']
            file_size = metadata.get('db_size', 0)
            size_mb = file_size / (1024 * 1024)
            
            print(f"{i:2d}. {backup['file'].name}")
            print(f"    Дата: {metadata['created_at']}")
            print(f"    Описание: {metadata.get('description', 'N/A')}")
            print(f"    Размер: {size_mb:.2f} MB")
            print()
    
    def cleanup_old_backups(self, keep_count=10):
        """Удаляет старые резервные копии, оставляя только последние N"""
        try:
            backups = self.list_backups()
            
            if len(backups) <= keep_count:
                print(f"[INFO] Количество резервных копий ({len(backups)}) не превышает лимит ({keep_count})")
                return
            
            to_delete = backups[keep_count:]
            deleted_count = 0
            
            for backup in to_delete:
                try:
                    backup['file'].unlink()  # Удаляем .sqlite3 файл
                    
                    # Удаляем метаданные если есть
                    metadata_file = backup['file'].with_suffix('.json')
                    if metadata_file.exists():
                        metadata_file.unlink()
                    
                    deleted_count += 1
                    print(f"[CLEANUP] Удалена старая резервная копия: {backup['file'].name}")
                    
                except Exception as e:
                    print(f"[WARN] Не удалось удалить {backup['file'].name}: {e}")
            
            print(f"[OK] Удалено старых резервных копий: {deleted_count}")
            
        except Exception as e:
            print(f"[ERROR] Ошибка очистки старых резервных копий: {e}")
    
    def verify_backup(self, backup_path):
        """Проверяет целостность резервной копии"""
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                print(f"[ERROR] Файл резервной копии не найден: {backup_path}")
                return False
            
            print(f"[VERIFY] Проверка целостности: {backup_path}")
            
            # Проверяем, что это валидная SQLite база
            try:
                conn = sqlite3.connect(backup_path)
                cursor = conn.cursor()
                
                # Проверяем основные таблицы
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['accounts_user', 'projects_project', 'kanban_expenseitem']
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    print(f"[WARN] Отсутствуют таблицы: {missing_tables}")
                
                # Проверяем количество записей
                cursor.execute("SELECT COUNT(*) FROM accounts_user")
                user_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM projects_project")
                project_count = cursor.fetchone()[0]
                
                conn.close()
                
                print(f"[OK] Резервная копия валидна")
                print(f"[INFO] Пользователей: {user_count}")
                print(f"[INFO] Проектов: {project_count}")
                print(f"[INFO] Таблиц: {len(tables)}")
                
                return True
                
            except sqlite3.Error as e:
                print(f"[ERROR] Резервная копия повреждена: {e}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Ошибка проверки резервной копии: {e}")
            return False


def main():
    """Главная функция для работы с резервными копиями"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Менеджер резервного копирования базы данных')
    parser.add_argument('action', choices=['create', 'restore', 'list', 'cleanup', 'verify'], 
                       help='Действие для выполнения')
    parser.add_argument('--file', help='Путь к файлу резервной копии (для restore/verify)')
    parser.add_argument('--description', default='manual', help='Описание резервной копии')
    parser.add_argument('--keep', type=int, default=10, help='Количество резервных копий для сохранения')
    
    args = parser.parse_args()
    
    manager = DatabaseBackupManager()
    
    if args.action == 'create':
        backup_path = manager.create_backup(args.description)
        if backup_path:
            print(f"\n[SUCCESS] Резервная копия создана: {backup_path}")
        else:
            print("\n[ERROR] Не удалось создать резервную копию")
            sys.exit(1)
    
    elif args.action == 'restore':
        if not args.file:
            print("[ERROR] Укажите файл резервной копии с --file")
            sys.exit(1)
        
        if manager.restore_backup(args.file):
            print("\n[SUCCESS] База данных восстановлена")
        else:
            print("\n[ERROR] Не удалось восстановить базу данных")
            sys.exit(1)
    
    elif args.action == 'list':
        manager.show_backups()
    
    elif args.action == 'cleanup':
        manager.cleanup_old_backups(args.keep)
    
    elif args.action == 'verify':
        if not args.file:
            print("[ERROR] Укажите файл резервной копии с --file")
            sys.exit(1)
        
        if manager.verify_backup(args.file):
            print("\n[SUCCESS] Резервная копия валидна")
        else:
            print("\n[ERROR] Резервная копия повреждена")
            sys.exit(1)


if __name__ == '__main__':
    main()
