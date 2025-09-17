from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from kanban.task_models import TaskCategory, TaskPriority, TaskStatus


class Command(BaseCommand):
    help = 'Заполняет базовые данные для системы задач'

    def handle(self, *args, **options):
        self.stdout.write('📋 Заполнение данных для системы задач...')
        
        # Создаем категории задач
        self.create_task_categories()
        
        # Создаем приоритеты
        self.create_task_priorities()
        
        # Создаем статусы
        self.create_task_statuses()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Данные для системы задач успешно заполнены!')
        )

    def create_task_categories(self):
        """Создает категории задач"""
        categories_data = [
            ('Закупки', 'Закупка материалов и оборудования', '#28a745', 'bi-cart'),
            ('Работы', 'Строительные и монтажные работы', '#007bff', 'bi-hammer'),
            ('Поставки', 'Доставка материалов', '#ffc107', 'bi-truck'),
            ('Контроль', 'Контроль качества и приемка', '#dc3545', 'bi-check-circle'),
            ('Документация', 'Ведение документации', '#6c757d', 'bi-file-text'),
            ('Координация', 'Координация работ', '#17a2b8', 'bi-people'),
            ('Безопасность', 'Обеспечение безопасности', '#fd7e14', 'bi-shield-check'),
            ('Прочее', 'Прочие задачи', '#6f42c1', 'bi-three-dots'),
        ]
        
        for name, description, color, icon in categories_data:
            category, created = TaskCategory.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'color': color,
                    'icon': icon,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✅ Создана категория: {name}')
            else:
                self.stdout.write(f'  ℹ️ Категория уже существует: {name}')

    def create_task_priorities(self):
        """Создает приоритеты задач"""
        priorities_data = [
            ('Критический', 1, '#dc3545', 'bi-exclamation-triangle-fill'),
            ('Высокий', 2, '#fd7e14', 'bi-arrow-up-circle-fill'),
            ('Средний', 3, '#ffc107', 'bi-dash-circle-fill'),
            ('Низкий', 4, '#28a745', 'bi-arrow-down-circle-fill'),
            ('Обычный', 5, '#6c757d', 'bi-circle'),
        ]
        
        for name, level, color, icon in priorities_data:
            priority, created = TaskPriority.objects.get_or_create(
                name=name,
                defaults={
                    'level': level,
                    'color': color,
                    'icon': icon,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✅ Создан приоритет: {name}')
            else:
                self.stdout.write(f'  ℹ️ Приоритет уже существует: {name}')

    def create_task_statuses(self):
        """Создает статусы задач"""
        statuses_data = [
            ('Новая', 'Задача создана, но еще не начата', '#6c757d', 'bi-circle', False, 1),
            ('К выполнению', 'Задача готова к выполнению', '#17a2b8', 'bi-play-circle', False, 2),
            ('В работе', 'Задача выполняется', '#007bff', 'bi-arrow-clockwise', False, 3),
            ('На проверке', 'Задача выполнена, ожидает проверки', '#ffc107', 'bi-eye', False, 4),
            ('Выполнена', 'Задача полностью выполнена', '#28a745', 'bi-check-circle-fill', True, 5),
            ('Отложена', 'Задача отложена', '#6c757d', 'bi-pause-circle', False, 6),
            ('Отменена', 'Задача отменена', '#dc3545', 'bi-x-circle-fill', True, 7),
        ]
        
        for name, description, color, icon, is_final, order in statuses_data:
            status, created = TaskStatus.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'color': color,
                    'icon': icon,
                    'is_final': is_final,
                    'is_active': True,
                    'order': order
                }
            )
            if created:
                self.stdout.write(f'  ✅ Создан статус: {name}')
            else:
                self.stdout.write(f'  ℹ️ Статус уже существует: {name}')
