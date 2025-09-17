from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from projects.estimate_models import (
    EstimateCategory, EstimateUnit, EstimateRate
)


class Command(BaseCommand):
    help = 'Заполняет справочник расценок базовыми данными'

    def handle(self, *args, **options):
        self.stdout.write('🏗️ Заполнение справочника расценок...')
        
        # Создаем единицы измерения
        self.create_units()
        
        # Создаем категории работ
        self.create_categories()
        
        # Создаем базовые расценки
        self.create_rates()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Справочник расценок успешно заполнен!')
        )

    def create_units(self):
        """Создает единицы измерения"""
        units_data = [
            ('м²', 'квадратный метр', 'Площадь'),
            ('м³', 'кубический метр', 'Объем'),
            ('м', 'метр', 'Длина'),
            ('м.п.', 'метр погонный', 'Погонная длина'),
            ('шт', 'штука', 'Количество'),
            ('кг', 'килограмм', 'Масса'),
            ('т', 'тонна', 'Масса'),
            ('час', 'час', 'Время'),
            ('день', 'день', 'Время'),
            ('м²/день', 'квадратный метр в день', 'Производительность'),
        ]
        
        for short_name, name, description in units_data:
            unit, created = EstimateUnit.objects.get_or_create(
                short_name=short_name,
                defaults={
                    'name': name,
                    'description': description,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✅ Создана единица: {name} ({short_name})')
            else:
                self.stdout.write(f'  ℹ️ Единица уже существует: {name} ({short_name})')

    def create_categories(self):
        """Создает категории работ"""
        categories_data = [
            ('01', 'Земляные работы', 'Работы по разработке грунта'),
            ('02', 'Фундаментные работы', 'Устройство фундаментов'),
            ('03', 'Стены и перегородки', 'Кладка и монтаж стен'),
            ('04', 'Перекрытия', 'Устройство перекрытий'),
            ('05', 'Кровельные работы', 'Устройство кровли'),
            ('06', 'Отделочные работы', 'Внутренняя и наружная отделка'),
            ('07', 'Сантехнические работы', 'Водопровод и канализация'),
            ('08', 'Электромонтажные работы', 'Электрические работы'),
            ('09', 'Отопление и вентиляция', 'Системы отопления и вентиляции'),
            ('10', 'Благоустройство', 'Благоустройство территории'),
        ]
        
        for code, name, description in categories_data:
            category, created = EstimateCategory.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': description,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✅ Создана категория: {code} - {name}')
            else:
                self.stdout.write(f'  ℹ️ Категория уже существует: {code} - {name}')

    def create_rates(self):
        """Создает базовые расценки"""
        # Получаем категории и единицы
        earth_works = EstimateCategory.objects.get(code='01')
        foundation_works = EstimateCategory.objects.get(code='02')
        walls_works = EstimateCategory.objects.get(code='03')
        finishing_works = EstimateCategory.objects.get(code='06')
        
        m2 = EstimateUnit.objects.get(short_name='м²')
        m3 = EstimateUnit.objects.get(short_name='м³')
        m = EstimateUnit.objects.get(short_name='м')
        mp = EstimateUnit.objects.get(short_name='м.п.')
        kg = EstimateUnit.objects.get(short_name='кг')
        hour = EstimateUnit.objects.get(short_name='час')
        
        rates_data = [
            # Земляные работы
            ('01-001', 'Разработка грунта экскаватором', earth_works, m3, 
             Decimal('150.00'), Decimal('80.00'), Decimal('60.00'), Decimal('10.00'), Decimal('2.5')),
            ('01-002', 'Обратная засыпка грунта', earth_works, m3,
             Decimal('80.00'), Decimal('40.00'), Decimal('30.00'), Decimal('10.00'), Decimal('1.5')),
            ('01-003', 'Уплотнение грунта', earth_works, m2,
             Decimal('25.00'), Decimal('15.00'), Decimal('8.00'), Decimal('2.00'), Decimal('0.5')),
            
            # Фундаментные работы
            ('02-001', 'Устройство ленточного фундамента', foundation_works, m3,
             Decimal('1200.00'), Decimal('400.00'), Decimal('700.00'), Decimal('100.00'), Decimal('8.0')),
            ('02-002', 'Устройство монолитной плиты', foundation_works, m3,
             Decimal('1000.00'), Decimal('350.00'), Decimal('600.00'), Decimal('50.00'), Decimal('6.0')),
            ('02-003', 'Гидроизоляция фундамента', foundation_works, m2,
             Decimal('180.00'), Decimal('60.00'), Decimal('100.00'), Decimal('20.00'), Decimal('2.0')),
            
            # Стены и перегородки
            ('03-001', 'Кладка кирпичная', walls_works, m3,
             Decimal('800.00'), Decimal('300.00'), Decimal('450.00'), Decimal('50.00'), Decimal('12.0')),
            ('03-002', 'Кладка из газобетона', walls_works, m3,
             Decimal('600.00'), Decimal('200.00'), Decimal('350.00'), Decimal('50.00'), Decimal('8.0')),
            ('03-003', 'Устройство перегородок из ГКЛ', walls_works, m2,
             Decimal('350.00'), Decimal('150.00'), Decimal('180.00'), Decimal('20.00'), Decimal('3.0')),
            
            # Отделочные работы
            ('06-001', 'Штукатурка стен', finishing_works, m2,
             Decimal('180.00'), Decimal('80.00'), Decimal('90.00'), Decimal('10.00'), Decimal('2.5')),
            ('06-002', 'Покраска стен', finishing_works, m2,
             Decimal('120.00'), Decimal('50.00'), Decimal('60.00'), Decimal('10.00'), Decimal('1.5')),
            ('06-003', 'Укладка плитки', finishing_works, m2,
             Decimal('400.00'), Decimal('150.00'), Decimal('220.00'), Decimal('30.00'), Decimal('4.0')),
            ('06-004', 'Устройство стяжки', finishing_works, m2,
             Decimal('250.00'), Decimal('100.00'), Decimal('130.00'), Decimal('20.00'), Decimal('2.0')),
            ('06-005', 'Укладка ламината', finishing_works, m2,
             Decimal('300.00'), Decimal('120.00'), Decimal('160.00'), Decimal('20.00'), Decimal('2.5')),
        ]
        
        for code, name, category, unit, base_price, labor_cost, material_cost, equipment_cost, labor_hours in rates_data:
            rate, created = EstimateRate.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'category': category,
                    'unit': unit,
                    'base_price': base_price,
                    'labor_cost': labor_cost,
                    'material_cost': material_cost,
                    'equipment_cost': equipment_cost,
                    'labor_hours': labor_hours,
                    'complexity_factor': Decimal('1.00'),
                    'region_factor': Decimal('1.00'),
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✅ Создана расценка: {code} - {name}')
            else:
                self.stdout.write(f'  ℹ️ Расценка уже существует: {code} - {name}')
        
        self.stdout.write(f'  📊 Всего расценок: {EstimateRate.objects.count()}')
