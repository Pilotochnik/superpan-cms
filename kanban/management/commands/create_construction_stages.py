from django.core.management.base import BaseCommand
from kanban.models import ConstructionStage


class Command(BaseCommand):
    help = 'Создает базовые этапы строительства'

    def handle(self, *args, **options):
        stages_data = [
            {
                'name': 'Подготовительные работы',
                'description': 'Подготовка участка, разметка, временные сооружения',
                'order': 1,
                'color': '#007bff'
            },
            {
                'name': 'Земляные работы',
                'description': 'Рытье котлована, планировка, дренаж',
                'order': 2,
                'color': '#6f42c1'
            },
            {
                'name': 'Фундамент',
                'description': 'Устройство фундамента, гидроизоляция',
                'order': 3,
                'color': '#20c997'
            },
            {
                'name': 'Стены и перекрытия',
                'description': 'Возведение стен, устройство перекрытий',
                'order': 4,
                'color': '#fd7e14'
            },
            {
                'name': 'Кровля',
                'description': 'Устройство кровли, водосточной системы',
                'order': 5,
                'color': '#dc3545'
            },
            {
                'name': 'Инженерные системы',
                'description': 'Электромонтаж, сантехника, отопление, вентиляция',
                'order': 6,
                'color': '#6c757d'
            },
            {
                'name': 'Отделочные работы',
                'description': 'Внутренняя и наружная отделка',
                'order': 7,
                'color': '#ffc107'
            },
            {
                'name': 'Благоустройство',
                'description': 'Озеленение, дорожки, ограждения',
                'order': 8,
                'color': '#28a745'
            },
            {
                'name': 'Сдача объекта',
                'description': 'Приемка работ, документооборот',
                'order': 9,
                'color': '#17a2b8'
            }
        ]

        created_count = 0
        for stage_data in stages_data:
            stage, created = ConstructionStage.objects.get_or_create(
                name=stage_data['name'],
                defaults=stage_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Создан этап: {stage.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Этап уже существует: {stage.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Создано этапов: {created_count}')
        )
