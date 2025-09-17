from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Создает пользователей с разными ролями для тестирования системы'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Создание пользователей с ролями...'))

        users_data = [
            # Администратор
            {
                'email': 'admin@superpan.ru',
                'password': 'admin123',
                'first_name': 'Администратор',
                'last_name': 'Системы',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            },
            # Главный инженер
            {
                'email': 'chief@superpan.ru',
                'password': 'chief123',
                'first_name': 'Иван',
                'last_name': 'Петров',
                'role': User.Role.CHIEF_ENGINEER,
                'is_staff': True,
            },
            # Прораб
            {
                'email': 'foreman@superpan.ru',
                'password': 'foreman123',
                'first_name': 'Сергей',
                'last_name': 'Сидоров',
                'role': User.Role.FOREMAN,
            },
            # Кладовщик
            {
                'email': 'keeper@superpan.ru',
                'password': 'keeper123',
                'first_name': 'Мария',
                'last_name': 'Козлова',
                'role': User.Role.WAREHOUSE_KEEPER,
            },
            # Снабженец
            {
                'email': 'supplier@superpan.ru',
                'password': 'supplier123',
                'first_name': 'Алексей',
                'last_name': 'Новиков',
                'role': User.Role.SUPPLIER,
            },
            # Экономист
            {
                'email': 'economist@superpan.ru',
                'password': 'economist123',
                'first_name': 'Елена',
                'last_name': 'Смирнова',
                'role': User.Role.ECONOMIST,
            },
            # Подрядчик
            {
                'email': 'contractor@superpan.ru',
                'password': 'contractor123',
                'first_name': 'Дмитрий',
                'last_name': 'Волков',
                'role': User.Role.CONTRACTOR,
            },
        ]

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for user_data in users_data:
                email = user_data['email']
                password = user_data.pop('password')
                
                # Устанавливаем username равным email
                user_data['username'] = email
                
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults=user_data
                )
                
                if created:
                    user.set_password(password)
                    user.save()
                    created_count += 1
                    self.stdout.write(f'✅ Создан пользователь: {email} ({user.get_role_display()})')
                else:
                    # Обновляем существующего пользователя
                    for key, value in user_data.items():
                        setattr(user, key, value)
                    user.set_password(password)
                    user.save()
                    updated_count += 1
                    self.stdout.write(f'🔄 Обновлен пользователь: {email} ({user.get_role_display()})')

        self.stdout.write(self.style.SUCCESS(f'Готово! Создано: {created_count}, обновлено: {updated_count}'))
        self.stdout.write('\n📋 Данные для входа:')
        self.stdout.write('👑 Администратор: admin@superpan.ru / admin123')
        self.stdout.write('👷 Главный инженер: chief@superpan.ru / chief123')
        self.stdout.write('🔨 Прораб: foreman@superpan.ru / foreman123')
        self.stdout.write('📦 Кладовщик: keeper@superpan.ru / keeper123')
        self.stdout.write('🚚 Снабженец: supplier@superpan.ru / supplier123')
        self.stdout.write('👷 Подрядчик: contractor@superpan.ru / contractor123')
