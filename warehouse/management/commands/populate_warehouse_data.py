from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from warehouse.models import WarehouseCategory, WarehouseItem

User = get_user_model()

class Command(BaseCommand):
    help = 'Заполняет склад тестовыми данными: категории, материалы и оборудование'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Заполнение склада тестовыми данными...'))

        # Создаем категории
        categories_data = [
            {'name': 'Строительные материалы', 'description': 'Кирпич, бетон, цемент и другие основные материалы'},
            {'name': 'Отделочные материалы', 'description': 'Краска, обои, плитка, ламинат'},
            {'name': 'Электрооборудование', 'description': 'Провода, розетки, выключатели, светильники'},
            {'name': 'Сантехника', 'description': 'Трубы, краны, смесители, унитазы'},
            {'name': 'Инструменты', 'description': 'Молотки, отвертки, дрели, пилы'},
            {'name': 'Строительная техника', 'description': 'Бетономешалки, краны, экскаваторы'},
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = WarehouseCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(f'Создана категория: {category.name}')

        # Создаем материалы
        materials_data = [
            # Строительные материалы
            {'name': 'Кирпич красный', 'item_type': 'MATERIAL', 'category': 'Строительные материалы', 
             'unit': 'шт', 'current_quantity': 5000, 'min_quantity': 1000, 'purchase_price': 15.50, 'selling_price': 18.00},
            {'name': 'Цемент М400', 'item_type': 'MATERIAL', 'category': 'Строительные материалы',
             'unit': 'мешок', 'current_quantity': 200, 'min_quantity': 50, 'purchase_price': 350.00, 'selling_price': 420.00},
            {'name': 'Песок речной', 'item_type': 'MATERIAL', 'category': 'Строительные материалы',
             'unit': 'м³', 'current_quantity': 50, 'min_quantity': 10, 'purchase_price': 800.00, 'selling_price': 950.00},
            {'name': 'Щебень фракция 20-40', 'item_type': 'MATERIAL', 'category': 'Строительные материалы',
             'unit': 'м³', 'current_quantity': 30, 'min_quantity': 5, 'purchase_price': 1200.00, 'selling_price': 1400.00},
            
            # Отделочные материалы
            {'name': 'Краска акриловая белая', 'item_type': 'MATERIAL', 'category': 'Отделочные материалы',
             'unit': 'л', 'current_quantity': 100, 'min_quantity': 20, 'purchase_price': 450.00, 'selling_price': 550.00},
            {'name': 'Плитка керамическая 30x30', 'item_type': 'MATERIAL', 'category': 'Отделочные материалы',
             'unit': 'м²', 'current_quantity': 200, 'min_quantity': 50, 'purchase_price': 1200.00, 'selling_price': 1500.00},
            {'name': 'Ламинат дуб', 'item_type': 'MATERIAL', 'category': 'Отделочные материалы',
             'unit': 'м²', 'current_quantity': 150, 'min_quantity': 30, 'purchase_price': 800.00, 'selling_price': 1000.00},
            
            # Электрооборудование
            {'name': 'Кабель ВВГ 3x2.5', 'item_type': 'MATERIAL', 'category': 'Электрооборудование',
             'unit': 'м', 'current_quantity': 1000, 'min_quantity': 200, 'purchase_price': 45.00, 'selling_price': 55.00},
            {'name': 'Розетка с заземлением', 'item_type': 'MATERIAL', 'category': 'Электрооборудование',
             'unit': 'шт', 'current_quantity': 50, 'min_quantity': 10, 'purchase_price': 120.00, 'selling_price': 150.00},
            {'name': 'Выключатель одноклавишный', 'item_type': 'MATERIAL', 'category': 'Электрооборудование',
             'unit': 'шт', 'current_quantity': 30, 'min_quantity': 5, 'purchase_price': 80.00, 'selling_price': 100.00},
            
            # Сантехника
            {'name': 'Труба ПВХ 110мм', 'item_type': 'MATERIAL', 'category': 'Сантехника',
             'unit': 'м', 'current_quantity': 200, 'min_quantity': 50, 'purchase_price': 180.00, 'selling_price': 220.00},
            {'name': 'Смеситель для кухни', 'item_type': 'MATERIAL', 'category': 'Сантехника',
             'unit': 'шт', 'current_quantity': 15, 'min_quantity': 3, 'purchase_price': 2500.00, 'selling_price': 3000.00},
        ]

        for material_data in materials_data:
            material, created = WarehouseItem.objects.get_or_create(
                name=material_data['name'],
                defaults={
                    'item_type': material_data['item_type'],
                    'category': categories[material_data['category']],
                    'unit': material_data['unit'],
                    'current_quantity': material_data['current_quantity'],
                    'min_quantity': material_data['min_quantity'],
                    'purchase_price': material_data['purchase_price'],
                    'selling_price': material_data['selling_price'],
                    'description': f'Тестовый {material_data["name"].lower()}',
                }
            )
            if created:
                self.stdout.write(f'Создан материал: {material.name}')

        # Создаем оборудование
        equipment_data = [
            # Инструменты
            {'name': 'Дрель ударная Bosch', 'item_type': 'EQUIPMENT', 'category': 'Инструменты',
             'unit': 'шт', 'current_quantity': 5, 'min_quantity': 2, 'purchase_price': 8500.00, 'selling_price': 10000.00},
            {'name': 'Перфоратор Makita', 'item_type': 'EQUIPMENT', 'category': 'Инструменты',
             'unit': 'шт', 'current_quantity': 3, 'min_quantity': 1, 'purchase_price': 12000.00, 'selling_price': 15000.00},
            {'name': 'Болгарка 125мм', 'item_type': 'EQUIPMENT', 'category': 'Инструменты',
             'unit': 'шт', 'current_quantity': 4, 'min_quantity': 2, 'purchase_price': 3500.00, 'selling_price': 4200.00},
            {'name': 'Шуруповерт аккумуляторный', 'item_type': 'EQUIPMENT', 'category': 'Инструменты',
             'unit': 'шт', 'current_quantity': 6, 'min_quantity': 3, 'purchase_price': 4500.00, 'selling_price': 5500.00},
            
            # Строительная техника
            {'name': 'Бетономешалка 200л', 'item_type': 'EQUIPMENT', 'category': 'Строительная техника',
             'unit': 'шт', 'current_quantity': 2, 'min_quantity': 1, 'purchase_price': 25000.00, 'selling_price': 30000.00},
            {'name': 'Леса строительные 2м', 'item_type': 'EQUIPMENT', 'category': 'Строительная техника',
             'unit': 'секция', 'current_quantity': 20, 'min_quantity': 5, 'purchase_price': 1500.00, 'selling_price': 1800.00},
            {'name': 'Лестница алюминиевая 3м', 'item_type': 'EQUIPMENT', 'category': 'Строительная техника',
             'unit': 'шт', 'current_quantity': 3, 'min_quantity': 1, 'purchase_price': 8000.00, 'selling_price': 9500.00},
        ]

        for equipment_data in equipment_data:
            equipment, created = WarehouseItem.objects.get_or_create(
                name=equipment_data['name'],
                defaults={
                    'item_type': equipment_data['item_type'],
                    'category': categories[equipment_data['category']],
                    'unit': equipment_data['unit'],
                    'current_quantity': equipment_data['current_quantity'],
                    'min_quantity': equipment_data['min_quantity'],
                    'purchase_price': equipment_data['purchase_price'],
                    'selling_price': equipment_data['selling_price'],
                    'description': f'Тестовое оборудование: {equipment_data["name"].lower()}',
                }
            )
            if created:
                self.stdout.write(f'Создано оборудование: {equipment.name}')

        self.stdout.write(self.style.SUCCESS('Склад успешно заполнен тестовыми данными!'))
        self.stdout.write(f'Создано категорий: {len(categories)}')
        self.stdout.write(f'Создано материалов: {len(materials_data)}')
        self.stdout.write(f'Создано оборудования: {len(equipment_data)}')
