from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from projects.models import Project
from kanban.models import KanbanBoard, KanbanColumn, ExpenseItem
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Добавляет примеры задач для всех проектов'

    def handle(self, *args, **options):
        self.stdout.write('Добавление примеров задач...')
        
        # Получаем все проекты
        projects = Project.objects.all()
        
        for project in projects:
            self.stdout.write(f'Обработка проекта: {project.name}')
            
            # Получаем канбан-доску проекта
            try:
                board = KanbanBoard.objects.get(project=project)
            except KanbanBoard.DoesNotExist:
                self.stdout.write(f'  Канбан-доска не найдена для проекта {project.name}')
                continue
            
            # Получаем колонки
            columns = {
                'new': board.columns.get(column_type='new'),
                'todo': board.columns.get(column_type='todo'),
                'in_progress': board.columns.get(column_type='in_progress'),
                'review': board.columns.get(column_type='review'),
                'done': board.columns.get(column_type='done'),
                'cancelled': board.columns.get(column_type='cancelled'),
            }
            
            # Создаем задачи в зависимости от типа проекта
            if 'жилой дом' in project.name.lower():
                tasks = self.get_house_tasks(project)
            elif 'офисное здание' in project.name.lower():
                tasks = self.get_office_tasks(project)
            elif 'торговый центр' in project.name.lower():
                tasks = self.get_mall_tasks(project)
            elif 'квартир' in project.name.lower():
                tasks = self.get_apartment_tasks(project)
            elif 'склад' in project.name.lower():
                tasks = self.get_warehouse_tasks(project)
            else:
                tasks = self.get_generic_tasks(project)
            
            # Создаем задачи
            for task_data in tasks:
                column = columns[task_data['status']]
                ExpenseItem.objects.create(
                    project=project,
                    column=column,
                    title=task_data['title'],
                    description=task_data['description'],
                    task_type=task_data['task_type'],
                    estimated_hours=Decimal(str(task_data['hours'])),
                    amount=Decimal(str(task_data.get('amount', task_data['hours'] * 1000))),  # Примерная стоимость: 1000₽ за час
                    priority=task_data['priority'],
                    created_by=project.created_by,
                    status=task_data['status'],
                    progress_percent=task_data.get('progress', 0),
                    is_urgent=task_data.get('urgent', False),
                    tags=task_data.get('tags', '')
                )
            
            self.stdout.write(f'  Добавлено {len(tasks)} задач')
        
        self.stdout.write(self.style.SUCCESS('Все задачи успешно добавлены!'))
    
    def get_house_tasks(self, project):
        """Задачи для строительства жилого дома"""
        return [
            # Новые задачи
            {
                'title': 'Земляные работы',
                'description': 'Выкопать котлован под фундамент, подготовить площадку',
                'task_type': 'work',
                'hours': 40,
                'status': 'new',
                'priority': 'high',
                'tags': 'фундамент, земляные работы'
            },
            {
                'title': 'Закупка кирпича',
                'description': 'Приобрести кирпич для кладки стен (50,000 шт.)',
                'task_type': 'purchase',
                'hours': 8,
                'status': 'new',
                'priority': 'medium',
                'tags': 'материалы, кирпич'
            },
            {
                'title': 'Кровельные работы',
                'description': 'Установка стропильной системы и кровельного покрытия',
                'task_type': 'work',
                'hours': 80,
                'status': 'new',
                'priority': 'medium',
                'tags': 'кровля, монтаж'
            },
            
            # К выполнению
            {
                'title': 'Фундаментные работы',
                'description': 'Залить ленточный фундамент, гидроизоляция',
                'task_type': 'work',
                'hours': 60,
                'status': 'todo',
                'priority': 'high',
                'tags': 'фундамент, бетон'
            },
            {
                'title': 'Доставка бетона',
                'description': 'Организовать доставку бетона для фундамента',
                'task_type': 'delivery',
                'hours': 4,
                'status': 'todo',
                'priority': 'high',
                'tags': 'доставка, бетон'
            },
            
            # В работе
            {
                'title': 'Кладка стен',
                'description': 'Возведение стен из кирпича по проекту',
                'task_type': 'work',
                'hours': 120,
                'status': 'in_progress',
                'priority': 'high',
                'progress': 45,
                'tags': 'кладка, стены'
            },
            {
                'title': 'Монтаж перекрытий',
                'description': 'Устройство железобетонных перекрытий',
                'task_type': 'work',
                'hours': 50,
                'status': 'in_progress',
                'priority': 'high',
                'progress': 20,
                'tags': 'перекрытия, бетон'
            },
            
            # На проверке
            {
                'title': 'Электромонтажные работы',
                'description': 'Прокладка электропроводки по этажам',
                'task_type': 'work',
                'hours': 40,
                'status': 'review',
                'priority': 'medium',
                'progress': 100,
                'tags': 'электрика, монтаж'
            },
            
            # Выполнены
            {
                'title': 'Проектирование',
                'description': 'Разработка проектной документации',
                'task_type': 'documentation',
                'hours': 80,
                'status': 'done',
                'priority': 'high',
                'progress': 100,
                'tags': 'проект, документация'
            },
            {
                'title': 'Получение разрешений',
                'description': 'Оформление разрешительной документации',
                'task_type': 'documentation',
                'hours': 20,
                'status': 'done',
                'priority': 'high',
                'progress': 100,
                'tags': 'разрешения, документы'
            }
        ]
    
    def get_office_tasks(self, project):
        """Задачи для реконструкции офисного здания"""
        return [
            # Новые задачи
            {
                'title': 'Демонтаж старых перегородок',
                'description': 'Удаление старых гипсокартонных перегородок',
                'task_type': 'work',
                'hours': 30,
                'status': 'new',
                'priority': 'medium',
                'tags': 'демонтаж, перегородки'
            },
            {
                'title': 'Закупка материалов',
                'description': 'Приобретение отделочных материалов',
                'task_type': 'purchase',
                'hours': 12,
                'status': 'new',
                'priority': 'medium',
                'tags': 'материалы, отделка'
            },
            
            # К выполнению
            {
                'title': 'Сантехнические работы',
                'description': 'Установка новых сантехнических систем',
                'task_type': 'work',
                'hours': 40,
                'status': 'todo',
                'priority': 'high',
                'tags': 'сантехника, монтаж'
            },
            
            # В работе
            {
                'title': 'Электромонтажные работы',
                'description': 'Прокладка новой электропроводки',
                'task_type': 'work',
                'hours': 50,
                'status': 'in_progress',
                'priority': 'high',
                'progress': 60,
                'tags': 'электрика, проводка'
            },
            {
                'title': 'Отделочные работы',
                'description': 'Поклейка обоев и покраска стен',
                'task_type': 'work',
                'hours': 60,
                'status': 'in_progress',
                'priority': 'medium',
                'progress': 30,
                'tags': 'отделка, покраска'
            },
            
            # На проверке
            {
                'title': 'Установка дверей',
                'description': 'Монтаж новых межкомнатных дверей',
                'task_type': 'installation',
                'hours': 25,
                'status': 'review',
                'priority': 'medium',
                'progress': 100,
                'tags': 'двери, монтаж'
            },
            
            # Выполнены
            {
                'title': 'Демонтаж старых конструкций',
                'description': 'Удаление старых перегородок и конструкций',
                'task_type': 'work',
                'hours': 30,
                'status': 'done',
                'priority': 'high',
                'progress': 100,
                'tags': 'демонтаж, подготовка'
            }
        ]
    
    def get_mall_tasks(self, project):
        """Задачи для строительства торгового центра"""
        return [
            # Новые задачи
            {
                'title': 'Благоустройство территории',
                'description': 'Устройство парковки и озеленение',
                'task_type': 'work',
                'hours': 40,
                'status': 'new',
                'priority': 'medium',
                'tags': 'благоустройство, парковка'
            },
            
            # К выполнению
            {
                'title': 'Наружная отделка',
                'description': 'Облицовка фасада торгового центра',
                'task_type': 'work',
                'hours': 70,
                'status': 'todo',
                'priority': 'high',
                'tags': 'фасад, отделка'
            },
            
            # В работе
            {
                'title': 'Внутренние перегородки',
                'description': 'Устройство внутренних стен и перегородок',
                'task_type': 'work',
                'hours': 60,
                'status': 'in_progress',
                'priority': 'high',
                'progress': 80,
                'tags': 'перегородки, стены'
            },
            
            # На проверке
            {
                'title': 'Система вентиляции',
                'description': 'Монтаж системы приточно-вытяжной вентиляции',
                'task_type': 'work',
                'hours': 45,
                'status': 'review',
                'priority': 'high',
                'progress': 100,
                'tags': 'вентиляция, монтаж'
            },
            
            # Выполнены
            {
                'title': 'Строительство каркаса',
                'description': 'Возведение металлического каркаса здания',
                'task_type': 'work',
                'hours': 100,
                'status': 'done',
                'priority': 'high',
                'progress': 100,
                'tags': 'каркас, металл'
            },
            {
                'title': 'Устройство кровли',
                'description': 'Монтаж кровельного покрытия',
                'task_type': 'work',
                'hours': 80,
                'status': 'done',
                'priority': 'high',
                'progress': 100,
                'tags': 'кровля, монтаж'
            }
        ]
    
    def get_apartment_tasks(self, project):
        """Задачи для ремонта квартиры"""
        return [
            # Новые задачи
            {
                'title': 'Планирование дизайна',
                'description': 'Разработка дизайн-проекта интерьера',
                'task_type': 'documentation',
                'hours': 20,
                'status': 'new',
                'priority': 'high',
                'tags': 'дизайн, планирование'
            },
            {
                'title': 'Закупка материалов',
                'description': 'Приобретение отделочных материалов и сантехники',
                'task_type': 'purchase',
                'hours': 15,
                'status': 'new',
                'priority': 'medium',
                'tags': 'материалы, закупка'
            },
            
            # К выполнению
            {
                'title': 'Демонтаж старых покрытий',
                'description': 'Удаление старых обоев, плитки, напольных покрытий',
                'task_type': 'work',
                'hours': 25,
                'status': 'todo',
                'priority': 'high',
                'tags': 'демонтаж, подготовка'
            },
            
            # В работе
            {
                'title': 'Черновые работы',
                'description': 'Штукатурка стен, выравнивание полов',
                'task_type': 'work',
                'hours': 40,
                'status': 'in_progress',
                'priority': 'high',
                'progress': 50,
                'tags': 'черновые работы, штукатурка'
            },
            
            # На проверке
            {
                'title': 'Электромонтаж',
                'description': 'Прокладка электропроводки и установка розеток',
                'task_type': 'work',
                'hours': 20,
                'status': 'review',
                'priority': 'high',
                'progress': 100,
                'tags': 'электрика, монтаж'
            },
            
            # Выполнены
            {
                'title': 'Замеры и расчеты',
                'description': 'Обмер помещений и расчет материалов',
                'task_type': 'control',
                'hours': 8,
                'status': 'done',
                'priority': 'high',
                'progress': 100,
                'tags': 'замеры, расчеты'
            }
        ]
    
    def get_warehouse_tasks(self, project):
        """Задачи для строительства склада (завершенный проект)"""
        return [
            # Все задачи выполнены
            {
                'title': 'Строительство каркаса',
                'description': 'Возведение металлического каркаса склада',
                'task_type': 'work',
                'hours': 80,
                'status': 'done',
                'priority': 'high',
                'progress': 100,
                'tags': 'каркас, металл'
            },
            {
                'title': 'Устройство кровли',
                'description': 'Монтаж кровельного покрытия',
                'task_type': 'work',
                'hours': 60,
                'status': 'done',
                'priority': 'high',
                'progress': 100,
                'tags': 'кровля, монтаж'
            },
            {
                'title': 'Устройство полов',
                'description': 'Заливка бетонных полов в складских помещениях',
                'task_type': 'work',
                'hours': 40,
                'status': 'done',
                'priority': 'high',
                'progress': 100,
                'tags': 'полы, бетон'
            },
            {
                'title': 'Монтаж ворот',
                'description': 'Установка складских ворот',
                'task_type': 'installation',
                'hours': 20,
                'status': 'done',
                'priority': 'medium',
                'progress': 100,
                'tags': 'ворота, монтаж'
            },
            {
                'title': 'Электромонтаж',
                'description': 'Прокладка электропроводки и освещения',
                'task_type': 'work',
                'hours': 35,
                'status': 'done',
                'priority': 'high',
                'progress': 100,
                'tags': 'электрика, освещение'
            },
            {
                'title': 'Система пожаротушения',
                'description': 'Установка системы автоматического пожаротушения',
                'task_type': 'work',
                'hours': 25,
                'status': 'done',
                'priority': 'high',
                'progress': 100,
                'tags': 'пожаротушение, безопасность'
            }
        ]
    
    def get_generic_tasks(self, project):
        """Общие задачи для любого проекта"""
        return [
            {
                'title': 'Планирование работ',
                'description': 'Составление детального плана выполнения работ',
                'task_type': 'documentation',
                'hours': 20,
                'status': 'new',
                'priority': 'high',
                'tags': 'планирование, документация'
            },
            {
                'title': 'Контроль качества',
                'description': 'Проверка качества выполненных работ',
                'task_type': 'control',
                'hours': 15,
                'status': 'todo',
                'priority': 'medium',
                'tags': 'контроль, качество'
            }
        ]
