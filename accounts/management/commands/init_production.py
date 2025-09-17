from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()

class Command(BaseCommand):
    help = 'Инициализация данных для продакшена'

    def handle(self, *args, **options):
        self.stdout.write('Инициализация данных для продакшена...')
        
        # Создаем суперпользователя
        if not User.objects.filter(email='admin@superpan.ru').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@superpan.ru',
                password='admin123',
                first_name='Администратор',
                last_name='Системы',
                role='admin'
            )
            self.stdout.write('✅ Создан суперпользователь: admin@superpan.ru / admin123')
        
        # Запускаем команды создания тестовых данных
        call_command('populate_estimate_data')
        call_command('populate_warehouse_data')
        call_command('reset_projects')
        call_command('add_sample_tasks')
        
        self.stdout.write(self.style.SUCCESS('✅ Данные для продакшена инициализированы!'))
        self.stdout.write('🔑 Логин: admin@superpan.ru')
        self.stdout.write('🔑 Пароль: admin123')
