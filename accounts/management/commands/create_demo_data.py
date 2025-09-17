from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from decimal import Decimal
import uuid

User = get_user_model()


class Command(BaseCommand):
    help = 'Создает демо-данные для системы "Проектный Офис"'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие демо-данные перед созданием новых',
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Создание демо-данных для "Проектный Офис"...')
        
        if options['clear']:
            self.clear_demo_data()
        
        try:
            with transaction.atomic():
                self.create_users()
                self.create_categories()
                self.create_projects()
                self.create_access_keys()
                self.create_expenses()
                
            self.stdout.write(
                self.style.SUCCESS('🎉 Демо-данные успешно созданы!')
            )
            self.print_credentials()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при создании демо-данных: {e}')
            )

    def clear_demo_data(self):
        """Очистка существующих демо-данных"""
        self.stdout.write('🧹 Очистка существующих данных...')
        
        # Удаляем всех пользователей кроме суперпользователей
        User.objects.exclude(is_superuser=True).delete()
        
        # Импортируем модели для очистки
        from projects.models import Project
        from kanban.models import ExpenseCategory, ExpenseItem
        from accounts.models import ProjectAccessKey
        
        ExpenseItem.objects.all().delete()
        ProjectAccessKey.objects.all().delete()
        Project.objects.all().delete()
        ExpenseCategory.objects.all().delete()
        
        self.stdout.write('✅ Данные очищены')

    def create_users(self):
        """Создание пользователей"""
        self.stdout.write('👥 Создание пользователей...')
        
        # Создаем прораба
        self.foreman = User.objects.create_user(
            email='foreman@project-office.ru',
            password='foreman123',
            first_name='Иван',
            last_name='Прорабов',
            role='foreman'
        )
        self.stdout.write('✅ Создан прораб: foreman@project-office.ru / foreman123')
        
        # Создаем подрядчиков
        self.contractors = []
        contractor_data = [
            ('contractor1@project-office.ru', 'Петр', 'Строителев'),
            ('contractor2@project-office.ru', 'Сергей', 'Электриков'),
            ('contractor3@project-office.ru', 'Михаил', 'Сантехников'),
        ]
        
        for email, first_name, last_name in contractor_data:
            contractor = User.objects.create_user(
                email=email,
                password='contractor123',
                first_name=first_name,
                last_name=last_name,
                role='contractor'
            )
            self.contractors.append(contractor)
            self.stdout.write(f'✅ Создан подрядчик: {email} / contractor123')

    def create_categories(self):
        """Создание категорий расходов"""
        self.stdout.write('📂 Создание категорий расходов...')
        
        from kanban.models import ExpenseCategory
        
        categories_data = [
            ('Строительные материалы', 'Цемент, кирпич, арматура', '#e74c3c'),
            ('Электрика', 'Провода, розетки, выключатели', '#f39c12'),
            ('Сантехника', 'Трубы, краны, сантехника', '#3498db'),
            ('Инструменты', 'Строительные инструменты', '#9b59b6'),
            ('Топливо', 'Бензин, дизель для техники', '#e67e22'),
        ]
        
        self.categories = []
        for name, description, color in categories_data:
            category = ExpenseCategory.objects.create(
                name=name,
                description=description,
                color=color,
                is_active=True
            )
            self.categories.append(category)
            self.stdout.write(f'✅ Создана категория: {name}')

    def create_projects(self):
        """Создание проектов"""
        self.stdout.write('🏗️ Создание проектов...')
        
        from projects.models import Project
        
        # Получаем суперпользователя
        superuser = User.objects.filter(is_superuser=True).first()
        
        self.project = Project.objects.create(
            name='Строительство жилого дома',
            description='Строительство двухэтажного жилого дома площадью 200 кв.м.',
            budget=Decimal('1000000.00'),
            status='active',
            address='г. Москва, ул. Строительная, д. 15',
            created_by=superuser or self.foreman,
            foreman=self.foreman
        )
        self.stdout.write('✅ Создан проект: Строительство жилого дома')

    def create_access_keys(self):
        """Создание ключей доступа"""
        self.stdout.write('🔑 Создание ключей доступа...')
        
        from accounts.models import ProjectAccessKey
        
        superuser = User.objects.filter(is_superuser=True).first()
        
        for contractor in self.contractors:
            access_key = ProjectAccessKey.objects.create(
                project_id=self.project.id,
                assigned_to=contractor,
                created_by=superuser or self.foreman,
                is_active=True,
                description=f'Доступ для {contractor.get_full_name()}'
            )
            self.stdout.write(f'✅ Создан ключ доступа для {contractor.get_full_name()}')

    def create_expenses(self):
        """Создание расходов и канбан-доски"""
        self.stdout.write('💰 Создание расходов...')
        
        from kanban.models import KanbanBoard, KanbanColumn, ExpenseItem
        
        # Создаем канбан-доску
        board = KanbanBoard.objects.create(
            project=self.project,
            created_by=self.foreman
        )
        
        # Создаем колонки
        columns_data = [
            ('Ожидает', 'pending', 0, '#f8f9fa'),
            ('На рассмотрении', 'in_review', 1, '#fff3cd'),
            ('Одобрено', 'approved', 2, '#d1edff'),
            ('Отклонено', 'rejected', 3, '#f8d7da'),
            ('Оплачено', 'paid', 4, '#d4edda'),
        ]
        
        columns = []
        for name, column_type, position, color in columns_data:
            column = KanbanColumn.objects.create(
                board=board,
                name=name,
                column_type=column_type,
                position=position,
                color=color
            )
            columns.append(column)
        
        # Создаем демо-расходы
        expenses_data = [
            ('Закупка цемента', 'Цемент М400, 50 мешков', 'material', Decimal('25000.00'), 'high', self.categories[0], self.contractors[0], 1),
            ('Электропроводка 1 этаж', 'Монтаж электропроводки первого этажа', 'labor', Decimal('45000.00'), 'medium', self.categories[1], self.contractors[1], 2),
            ('Сантехнические трубы', 'Трубы для водоснабжения и канализации', 'material', Decimal('18000.00'), 'medium', self.categories[2], self.contractors[2], 0),
            ('Топливо для экскаватора', 'Дизельное топливо для земляных работ', 'fuel', Decimal('8500.00'), 'low', self.categories[4], self.contractors[0], 4),
            ('Аренда бетономешалки', 'Аренда бетономешалки на 5 дней', 'equipment', Decimal('12000.00'), 'medium', self.categories[3], self.contractors[1], 0),
            ('Кирпич облицовочный', 'Кирпич для облицовки фасада', 'material', Decimal('65000.00'), 'high', self.categories[0], self.contractors[2], 1),
        ]
        
        for title, description, task_type, amount, priority, category, created_by, column_idx in expenses_data:
            expense = ExpenseItem.objects.create(
                project=self.project,
                column=columns[column_idx],
                title=title,
                description=description,
                task_type=task_type,
                amount=amount,
                priority=priority,
                category=category,
                created_by=created_by,
                position=0
            )
            self.stdout.write(f'✅ Создан расход: {title}')
        
        # Обновляем потраченную сумму проекта
        self.project.update_spent_amount()
        
        self.stdout.write('✅ Канбан-доска создана')

    def print_credentials(self):
        """Вывод учетных данных"""
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎯 Система готова к использованию!'))
        self.stdout.write('')
        self.stdout.write('👥 Учетные данные для входа:')
        self.stdout.write(f'   🔑 Прораб: foreman@project-office.ru / foreman123')
        for i, contractor in enumerate(self.contractors, 1):
            self.stdout.write(f'   👷 Подрядчик {i}: {contractor.email} / contractor123')
        self.stdout.write('')
        self.stdout.write('🌐 Доступные страницы:')
        self.stdout.write('   📊 Главная: http://127.0.0.1:8000/')
        self.stdout.write('   🏗️ Проекты: http://127.0.0.1:8000/projects/')
        self.stdout.write('   📋 Канбан: http://127.0.0.1:8000/kanban/board/{project_id}/')
        self.stdout.write('   ⚙️ Админка: http://127.0.0.1:8000/management/')
        self.stdout.write('')
        self.stdout.write('📈 Демо-проект:')
        self.stdout.write(f'   📁 {self.project.name}')
        self.stdout.write(f'   💰 Бюджет: {self.project.budget:,.0f} ₽')
        self.stdout.write(f'   💸 Потрачено: {self.project.spent_amount:,.0f} ₽')
