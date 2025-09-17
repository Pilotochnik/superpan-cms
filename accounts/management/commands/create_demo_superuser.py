from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = 'Создает демо-суперпользователя для системы "Проектный Офис"'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='admin@project-office.ru',
            help='Email для суперпользователя (по умолчанию: admin@project-office.ru)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Пароль для суперпользователя (по умолчанию: admin123)'
        )
        parser.add_argument(
            '--first_name',
            type=str,
            default='Администратор',
            help='Имя суперпользователя'
        )
        parser.add_argument(
            '--last_name',
            type=str,
            default='Системы',
            help='Фамилия суперпользователя'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        try:
            # Проверяем, существует ли уже пользователь с таким email
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'Пользователь с email {email} уже существует')
                )
                return

            # Создаем суперпользователя
            user = User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=User.Role.SUPERUSER
            )

            self.stdout.write(
                self.style.SUCCESS(f'✅ Суперпользователь успешно создан!')
            )
            self.stdout.write(f'📧 Email: {email}')
            self.stdout.write(f'🔑 Пароль: {password}')
            self.stdout.write(f'👤 Имя: {first_name} {last_name}')
            self.stdout.write(f'🎭 Роль: {user.get_role_display()}')
            self.stdout.write('')
            self.stdout.write('🚀 Теперь вы можете войти в систему:')
            self.stdout.write('   - Основная система: http://127.0.0.1:8000/')
            self.stdout.write('   - Простая админка: http://127.0.0.1:8000/management/')
            self.stdout.write('   - Django админка: http://127.0.0.1:8000/admin/')

        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при создании пользователя: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Неожиданная ошибка: {e}')
            )
