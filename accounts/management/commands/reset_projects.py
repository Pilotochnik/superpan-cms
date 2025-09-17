from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from projects.models import Project, ProjectMember, ProjectActivity
from kanban.models import KanbanBoard, KanbanColumn, ExpenseItem
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Очищает старые проекты и создает новые тестовые проекты'

    def handle(self, *args, **options):
        self.stdout.write('Очистка старых данных...')
        
        # Удаляем все старые данные
        ExpenseItem.objects.all().delete()
        KanbanColumn.objects.all().delete()
        KanbanBoard.objects.all().delete()
        ProjectMember.objects.all().delete()
        ProjectActivity.objects.all().delete()
        Project.objects.all().delete()
        
        self.stdout.write('Создание тестовых проектов...')
        
        # Создаем тестового пользователя-менеджера
        manager, created = User.objects.get_or_create(
            email='manager@superpan.ru',
            defaults={
                'username': 'manager',
                'first_name': 'Александр',
                'last_name': 'Петров',
                'role': 'admin',
                'is_active': True
            }
        )
        if created:
            manager.set_password('admin123')
            manager.save()
        
        # Создаем тестового прораба
        foreman, created = User.objects.get_or_create(
            email='foreman@superpan.ru',
            defaults={
                'username': 'foreman',
                'first_name': 'Михаил',
                'last_name': 'Сидоров',
                'role': 'foreman',
                'is_active': True
            }
        )
        if created:
            foreman.set_password('foreman123')
            foreman.save()
        
        # Создаем тестового подрядчика
        contractor, created = User.objects.get_or_create(
            email='contractor@superpan.ru',
            defaults={
                'username': 'contractor',
                'first_name': 'Дмитрий',
                'last_name': 'Козлов',
                'role': 'contractor',
                'is_active': True
            }
        )
        if created:
            contractor.set_password('contractor123')
            contractor.save()
        
        # Проект 1: Строительство жилого дома (Начальный этап)
        project1 = Project.objects.create(
            name='Строительство жилого дома "Солнечный"',
            description='Строительство 5-этажного жилого дома на 40 квартир в микрорайоне "Солнечный"',
            budget=Decimal('25000000.00'),
            spent_amount=Decimal('2500000.00'),
            status='in_progress',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            created_by=manager,
            foreman=foreman,
            address='г. Москва, ул. Солнечная, д. 15'
        )
        
        # Проект 2: Реконструкция офисного здания (Активный этап)
        project2 = Project.objects.create(
            name='Реконструкция офисного здания "Бизнес-центр"',
            description='Полная реконструкция 3-этажного офисного здания с модернизацией инженерных систем',
            budget=Decimal('15000000.00'),
            spent_amount=Decimal('8500000.00'),
            status='in_progress',
            start_date=timezone.now().date() - timedelta(days=60),
            end_date=timezone.now().date() + timedelta(days=120),
            created_by=manager,
            foreman=foreman,
            address='г. Москва, ул. Деловая, д. 42'
        )
        
        # Проект 3: Строительство торгового центра (Завершающий этап)
        project3 = Project.objects.create(
            name='Строительство торгового центра "МегаМолл"',
            description='Строительство 2-этажного торгового центра площадью 5000 кв.м с парковкой',
            budget=Decimal('40000000.00'),
            spent_amount=Decimal('38000000.00'),
            status='in_progress',
            start_date=timezone.now().date() - timedelta(days=240),
            end_date=timezone.now().date() + timedelta(days=30),
            created_by=manager,
            foreman=foreman,
            address='г. Москва, ул. Торговая, д. 100'
        )
        
        # Проект 4: Ремонт квартиры (Планирование)
        project4 = Project.objects.create(
            name='Ремонт квартиры в новостройке',
            description='Полный ремонт 3-комнатной квартиры площадью 85 кв.м с дизайнерским решением',
            budget=Decimal('1200000.00'),
            spent_amount=Decimal('0.00'),
            status='planning',
            start_date=timezone.now().date() + timedelta(days=30),
            end_date=timezone.now().date() + timedelta(days=90),
            created_by=manager,
            foreman=contractor,
            address='г. Москва, ул. Новая, д. 25, кв. 45'
        )
        
        # Проект 5: Строительство склада (Завершен)
        project5 = Project.objects.create(
            name='Строительство складского комплекса "Логистик"',
            description='Строительство 2-этажного складского комплекса площадью 3000 кв.м с офисными помещениями',
            budget=Decimal('18000000.00'),
            spent_amount=Decimal('18000000.00'),
            status='completed',
            start_date=timezone.now().date() - timedelta(days=365),
            end_date=timezone.now().date() - timedelta(days=60),
            created_by=manager,
            foreman=foreman,
            address='г. Москва, ул. Складская, д. 8'
        )
        
        # Создаем участников проектов
        projects = [project1, project2, project3, project4, project5]
        
        for project in projects:
            # Добавляем прораба как участника
            ProjectMember.objects.create(
                project=project,
                user=foreman,
                role='foreman',
                can_add_expenses=True,
                can_view_budget=True,
                is_active=True
            )
            
            # Добавляем подрядчика как участника
            ProjectMember.objects.create(
                project=project,
                user=contractor,
                role='contractor',
                can_add_expenses=True,
                can_view_budget=False,
                is_active=True
            )
            
            # Создаем канбан-доску для проекта
            board = KanbanBoard.objects.create(
                project=project,
                created_by=manager
            )
            
            # Создаем колонки для задач
            columns_data = [
                ('Новые', 'new', 0, '#f8f9fa'),
                ('К выполнению', 'todo', 1, '#e3f2fd'),
                ('В работе', 'in_progress', 2, '#fff3cd'),
                ('На проверке', 'review', 3, '#d1edff'),
                ('Выполнены', 'done', 4, '#d4edda'),
                ('Отменены', 'cancelled', 5, '#f8d7da'),
            ]
            
            for name, column_type, position, color in columns_data:
                KanbanColumn.objects.create(
                    board=board,
                    name=name,
                    column_type=column_type,
                    position=position,
                    color=color
                )
            
            # Создаем тестовые задачи для активных проектов
            if project.status == 'in_progress':
                self.create_sample_tasks(project, board)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно создано {len(projects)} тестовых проектов:\n'
                f'1. {project1.name} - {project1.get_status_display()} (Бюджет: {project1.budget:,}₽)\n'
                f'2. {project2.name} - {project2.get_status_display()} (Бюджет: {project2.budget:,}₽)\n'
                f'3. {project3.name} - {project3.get_status_display()} (Бюджет: {project3.budget:,}₽)\n'
                f'4. {project4.name} - {project4.get_status_display()} (Бюджет: {project4.budget:,}₽)\n'
                f'5. {project5.name} - {project5.get_status_display()} (Бюджет: {project5.budget:,}₽)\n\n'
                f'Тестовые пользователи:\n'
                f'- Менеджер: manager@superpan.ru / admin123\n'
                f'- Прораб: foreman@superpan.ru / foreman123\n'
                f'- Подрядчик: contractor@superpan.ru / contractor123'
            )
        )
    
    def create_sample_tasks(self, project, board):
        """Создает примеры задач для проекта"""
        from kanban.models import ExpenseItem
        
        # Получаем колонки
        new_column = board.columns.get(column_type='new')
        todo_column = board.columns.get(column_type='todo')
        in_progress_column = board.columns.get(column_type='in_progress')
        done_column = board.columns.get(column_type='done')
        
        # Задачи в зависимости от типа проекта
        if 'жилой дом' in project.name.lower():
            tasks = [
                ('Земляные работы', 'Выкопать котлован под фундамент', 'work', 40, 'new'),
                ('Фундаментные работы', 'Залить ленточный фундамент', 'work', 60, 'todo'),
                ('Кладка стен', 'Возвести стены из кирпича', 'work', 120, 'in_progress'),
                ('Кровельные работы', 'Установить крышу', 'work', 80, 'new'),
                ('Внутренняя отделка', 'Штукатурка и покраска стен', 'work', 100, 'new'),
            ]
        elif 'офисное здание' in project.name.lower():
            tasks = [
                ('Демонтаж старых конструкций', 'Удаление старых перегородок', 'work', 30, 'done'),
                ('Электромонтажные работы', 'Прокладка новой электропроводки', 'work', 50, 'in_progress'),
                ('Сантехнические работы', 'Установка новых сантехнических систем', 'work', 40, 'todo'),
                ('Отделочные работы', 'Поклейка обоев и покраска', 'work', 60, 'new'),
                ('Установка дверей и окон', 'Монтаж новых дверей и окон', 'work', 25, 'new'),
            ]
        elif 'торговый центр' in project.name.lower():
            tasks = [
                ('Строительство каркаса', 'Возведение металлического каркаса', 'work', 100, 'done'),
                ('Устройство кровли', 'Монтаж кровельного покрытия', 'work', 80, 'done'),
                ('Внутренние перегородки', 'Устройство внутренних стен', 'work', 60, 'in_progress'),
                ('Наружная отделка', 'Облицовка фасада', 'work', 70, 'todo'),
                ('Благоустройство территории', 'Устройство парковки и озеленение', 'work', 40, 'new'),
            ]
        else:
            tasks = [
                ('Планирование работ', 'Составление детального плана', 'work', 20, 'new'),
                ('Закупка материалов', 'Приобретение необходимых материалов', 'purchase', 15, 'todo'),
                ('Подготовка объекта', 'Подготовка к началу работ', 'work', 10, 'new'),
            ]
        
        for title, description, task_type, hours, status in tasks:
            column = {
                'new': new_column,
                'todo': todo_column,
                'in_progress': in_progress_column,
                'done': done_column
            }[status]
            
            ExpenseItem.objects.create(
                project=project,
                column=column,
                title=title,
                description=description,
                task_type=task_type,
                estimated_hours=Decimal(str(hours)),
                priority='medium',
                created_by=project.created_by,
                status=status
            )
