import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from django.conf import settings
from asgiref.sync import sync_to_async

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Импорт Django моделей
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'superpan.settings')
django.setup()

from accounts.models import TelegramUser, User, TelegramAuthToken
from projects.models import Project, ProjectMember
from kanban.models import ExpenseItem, ConstructionStage, ExpenseCategory


class ConstructionBot:
    """Telegram бот для управления строительными проектами"""
    
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("projects", self.projects_command))
        self.application.add_handler(CommandHandler("tasks", self.tasks_command))
        self.application.add_handler(CommandHandler("stages", self.stages_command))
        self.application.add_handler(CommandHandler("create_task", self.create_task_command))
        
        # Обработчики кнопок
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Обработчик текстовых сообщений для создания задач
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        
        # Обработчик фото и файлов для создания задач
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo_message))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document_message))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def send_message(self, update, text, reply_markup=None):
        """Универсальная функция для отправки сообщений"""
        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup)
        else:
            await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
    
    async def send_message_to_user(self, user_id, text, reply_markup=None):
        """Отправка сообщения пользователю по его Telegram ID"""
        try:
            await self.application.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
            return False
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user = update.effective_user
        message_text = update.message.text
        
        print(f"[START] Получена команда /start от пользователя {user.id} ({user.first_name})")
        print(f"[START] Полное сообщение: {message_text}")
        print(f"[START] Аргументы: {context.args}")
        print(f"[START] Количество аргументов: {len(context.args)}")
        
        # Проверяем, есть ли токен авторизации в команде
        if len(context.args) > 0:
            print(f"[START] Первый аргумент: '{context.args[0]}'")
            if context.args[0].startswith('auth_'):
                auth_token = context.args[0][5:]  # Убираем префикс 'auth_'
                print(f"[AUTH] Найден токен авторизации: {auth_token}")
                await self.handle_auth_token(update, context, auth_token, user)
                return
            else:
                print(f"[WARN] Первый аргумент не содержит 'auth_': '{context.args[0]}'")
        else:
            print("[WARN] Нет аргументов в команде /start")
        
        try:
            # Проверяем, есть ли пользователь в системе
            telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=user.id)
            django_user = await sync_to_async(lambda: telegram_user.user)()
            user_name = await sync_to_async(lambda: django_user.get_full_name())()
            
            user_role_display = await sync_to_async(lambda: django_user.get_role_display())()
            welcome_text = f"""
🏗️ Привет, {user_name}!
Роль: {user_role_display}

Выберите действие:
            """
            
            # Создаем URL для перехода в панель
            from django.urls import reverse
            from django.contrib.sites.models import Site
            
            # Получаем домен сайта
            try:
                current_site = await sync_to_async(Site.objects.get_current)()
                domain = current_site.domain
            except:
                domain = "127.0.0.1:8000"  # Fallback для разработки
            
            # Создаем токен для автоматического входа
            from accounts.models import TelegramAuthToken
            import uuid
            from datetime import datetime, timedelta
            
            # Создаем временный токен для входа в панель
            login_token = str(uuid.uuid4())
            from django.utils import timezone
            expires_at = timezone.now() + timedelta(minutes=30)  # Токен действует 30 минут
            
            login_auth_token = await sync_to_async(TelegramAuthToken.objects.create)(
                token=login_token,
                user=django_user,
                telegram_user=telegram_user,
                expires_at=expires_at,
                is_used=False
            )
            
            print(f"[AUTH] Создан токен для входа: {login_token}, истекает: {expires_at}")
            
            # URL для автоматического входа
            panel_url = f"http://{domain}{reverse('accounts:telegram_login')}?auth_token={login_token}"
            
            keyboard = [
                [InlineKeyboardButton("🌐 Вернуться в панель", url=panel_url)],
                [InlineKeyboardButton("📋 Мои задачи", callback_data="tasks")],
                [InlineKeyboardButton("🏗️ Проекты", callback_data="projects")],
                [InlineKeyboardButton("➕ Создать задачу", callback_data="create_task")],
                [InlineKeyboardButton("❓ Помощь", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
        except TelegramUser.DoesNotExist:
            welcome_text = f"""
🏗️ Добро пожаловать в Construction Bot!

Привет, {user.first_name}!

Для использования бота необходимо сначала авторизоваться в веб-приложении:
1. Перейдите на сайт проекта
2. Войдите в систему
3. Подключите ваш Telegram аккаунт в профиле

После этого вы сможете управлять проектами через бота!
            """
            reply_markup = None
        except Exception as e:
            print(f"[ERROR] Ошибка в start_command: {e}")
            welcome_text = f"""
🏗️ Добро пожаловать в Construction Bot!

Привет, {user.first_name}!

Произошла ошибка при обработке запроса.
Попробуйте позже или обратитесь к администратору.
            """
            reply_markup = None
        
        await self.send_message(update, welcome_text, reply_markup=reply_markup)
    
    async def handle_auth_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE, auth_token: str, user):
        """Обработка токена авторизации"""
        print(f"[AUTH] Обрабатываем токен авторизации: {auth_token}")
        print(f"[AUTH] Пользователь: {user.id} ({user.first_name} {user.last_name})")
        print(f"[AUTH] Username: @{user.username}")
        
        try:
            # Сначала проверяем, является ли токен валидным UUID
            try:
                import uuid
                uuid.UUID(auth_token)
            except ValueError:
                print(f"[ERROR] Невалидный формат токена: {auth_token}")
                await update.message.reply_text("Неверный формат токена авторизации.")
                return
            
            # Ищем токен в базе данных
            try:
                print(f"[AUTH] Ищем токен в базе данных...")
                auth_token_obj = await sync_to_async(TelegramAuthToken.objects.get)(token=auth_token)
                print(f"[AUTH] Токен найден в базе данных: {auth_token_obj.token}")
                print(f"[AUTH] Токен создан: {auth_token_obj.created_at}")
                print(f"[AUTH] Токен истекает: {auth_token_obj.expires_at}")
                print(f"[AUTH] Токен использован: {auth_token_obj.is_used}")
            except TelegramAuthToken.DoesNotExist:
                print(f"[ERROR] Токен не найден в базе данных: {auth_token}")
                await update.message.reply_text("Неверный токен авторизации.")
                return
            
            # Проверяем, не истек ли токен
            if await sync_to_async(auth_token_obj.is_expired)():
                await update.message.reply_text("Токен авторизации истек. Попробуйте еще раз.")
                return
            
            # Проверяем, не использован ли токен
            if auth_token_obj.is_used:
                print(f"[ERROR] Токен уже использован: {auth_token_obj.is_used}")
                await update.message.reply_text("Токен уже использован.")
                return
            
            print(f"[AUTH] Токен валиден, продолжаем авторизацию...")
            
            # Создаем или обновляем пользователя Telegram
            print(f"[AUTH] Создаем/находим пользователя Telegram для ID: {user.id}")
            
            # Сначала создаем Django пользователя
            email = f"telegram_{user.id}@example.com"
            print(f"[AUTH] Создаем/находим Django пользователя: {email}")
            
            try:
                django_user = await sync_to_async(User.objects.get)(email=email)
                print(f"[AUTH] Найден существующий Django пользователь: {django_user.email}")
            except User.DoesNotExist:
                print(f"[AUTH] Создаем нового Django пользователя: {email}")
                django_user = await sync_to_async(User.objects.create_user)(
                    email=email,
                    first_name=user.first_name or 'Telegram',
                    last_name=user.last_name or 'User',
                    role='foreman',  # По умолчанию прораб
                    is_active=True
                )
                print(f"[AUTH] Django пользователь создан: {django_user.email} (ID: {django_user.id})")
            
            # Теперь создаем Telegram пользователя с привязкой к Django пользователю
            telegram_user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
                telegram_id=user.id,
                defaults={
                    'user': django_user,  # Сразу привязываем к Django пользователю
                    'username': user.username or '',
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'photo_url': '',
                    'language_code': user.language_code or 'ru'
                }
            )
            
            if created:
                print(f"[AUTH] Создан новый пользователь Telegram: {telegram_user.telegram_id}")
            else:
                print(f"[AUTH] Найден существующий пользователь Telegram: {telegram_user.telegram_id}")
                # Обновляем данные существующего пользователя
                telegram_user.username = user.username or ''
                telegram_user.first_name = user.first_name or ''
                telegram_user.last_name = user.last_name or ''
                telegram_user.photo_url = ''
                telegram_user.language_code = user.language_code or 'ru'
                await sync_to_async(telegram_user.save)()
                print(f"[AUTH] Telegram пользователь обновлен")
            
            # Отмечаем токен как использованный
            print(f"[AUTH] Отмечаем токен как использованный...")
            await sync_to_async(auth_token_obj.mark_as_used)(django_user, telegram_user)
            print(f"[AUTH] Токен отмечен как использованный")
            
            user_name = await sync_to_async(lambda: django_user.get_full_name())()
            welcome_text = f"""
✅ Авторизация успешна!

Добро пожаловать, {user_name}!

Ваш Telegram аккаунт успешно привязан к системе.
Теперь вы можете управлять проектами через бота!

Используйте /help для списка команд.
            """
            
            # Создаем URL для автоматического входа в панель
            from django.urls import reverse
            from django.contrib.sites.models import Site
            from django.conf import settings
            
            # Получаем домен сайта
            try:
                current_site = await sync_to_async(Site.objects.get_current)()
                domain = current_site.domain
            except:
                domain = "127.0.0.1:8000"  # Fallback для разработки
            
            # Создаем токен для автоматического входа
            from accounts.models import TelegramAuthToken
            import uuid
            from datetime import datetime, timedelta
            
            # Создаем временный токен для входа в панель
            login_token = str(uuid.uuid4())
            from django.utils import timezone
            expires_at = timezone.now() + timedelta(minutes=30)  # Токен действует 30 минут
            
            login_auth_token = await sync_to_async(TelegramAuthToken.objects.create)(
                token=login_token,
                user=django_user,
                telegram_user=telegram_user,
                expires_at=expires_at,
                is_used=False
            )
            
            print(f"[AUTH] Создан токен для входа: {login_token}, истекает: {expires_at}")
            
            # URL для автоматического входа
            panel_url = f"http://{domain}{reverse('accounts:telegram_login')}?auth_token={login_token}"
            
            keyboard = [
                [InlineKeyboardButton("🌐 Вернуться в панель", url=panel_url)],
                [InlineKeyboardButton("📋 Мои задачи", callback_data="my_tasks")],
                [InlineKeyboardButton("🏗️ Проекты", callback_data="projects")],
                [InlineKeyboardButton("➕ Создать задачу", callback_data="create_task")],
                [InlineKeyboardButton("❓ Помощь", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_text, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Ошибка в handle_auth_token: {e}")
            await update.message.reply_text("❌ Произошла ошибка при авторизации. Попробуйте еще раз.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
🔧 Доступные команды:

/start - Начать работу с ботом
/help - Показать это сообщение
/projects - Список ваших проектов
/tasks - Ваши задачи
/stages - Этапы строительства
/create_task - Создать новую задачу

📱 Управление:
• Используйте кнопки для быстрого доступа
• Отправьте номер задачи для просмотра деталей
• Используйте команды для навигации

❓ Нужна помощь? Обратитесь к администратору.
        """
        await self.send_message(update, help_text)
    
    async def projects_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /projects - показать проекты пользователя"""
        try:
            telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=update.effective_user.id)
            user = await sync_to_async(lambda: telegram_user.user)()
            user_role = await sync_to_async(lambda: user.role)()
            
            # Получаем проекты через метод get_accessible_projects()
            projects = await sync_to_async(list)(user.get_accessible_projects().order_by('-created_at')[:10])
            
            if not projects:
                role_text = {
                    'admin': 'администратор',
                    'foreman': 'прораб',
                    'warehouse_keeper': 'кладовщик',
                    'supplier': 'снабженец',
                    'contractor': 'подрядчик'
                }.get(user_role, 'пользователь')
                
                await self.send_message(update, f"📭 У вас как {role_text} пока нет проектов.")
                return
            
            user_role_display = await sync_to_async(lambda: user.get_role_display())()
            text = f"🏗️ Проекты ({user_role_display}):\n\n"
            keyboard = []
            
            # Подготавливаем данные для всех проектов
            project_data = []
            for project in projects:
                try:
                    project_status = project.status
                except:
                    project_status = 'unknown'
                
                status_emoji = {
                    'planning': '📋',
                    'in_progress': '🚧',
                    'on_hold': '⏸️',
                    'completed': '✅',
                    'cancelled': '❌'
                }.get(project_status, '❓')
                
                project_data.append({
                    'project': project,
                    'status_emoji': status_emoji
                })
            
            # Теперь обрабатываем данные асинхронно
            for data in project_data:
                project = data['project']
                status_emoji = data['status_emoji']
                
                # Получаем роль пользователя в проекте
                project_role = "👤 Участник"
                project_created_by = await sync_to_async(lambda: project.created_by)()
                project_foreman = await sync_to_async(lambda: project.foreman)()
                
                if project_created_by == user:
                    project_role = "👑 Создатель"
                elif project_foreman == user:
                    project_role = "👷 Прораб"
                
                project_name = await sync_to_async(lambda: project.name)()
                project_budget = await sync_to_async(lambda: project.budget)()
                project_spent = await sync_to_async(lambda: project.spent_amount)()
                project_id = await sync_to_async(lambda: project.id)()
                
                if project_budget > 0:
                    progress = (project_spent / project_budget) * 100
                    text += f"{status_emoji} {project_name}\n💰 {project_budget:,.0f}₽ | 💸 {project_spent:,.0f}₽ | 📊 {progress:.0f}%\n\n"
                else:
                    text += f"{status_emoji} {project_name}\n💰 {project_budget:,.0f}₽ | 💸 {project_spent:,.0f}₽\n\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"📋 {project_name[:30]}{'...' if len(project_name) > 30 else ''}",
                    callback_data=f"project_{project_id}"
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await self.send_message(update, text, reply_markup=reply_markup)
            
        except TelegramUser.DoesNotExist:
            await self.send_message(update, "❌ Сначала авторизуйтесь в веб-приложении.")
        except Exception as e:
            logger.error(f"Ошибка в projects_command: {e}")
            await self.send_message(update, "❌ Произошла ошибка при получении проектов.")
    
    async def tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /tasks - показать задачи пользователя"""
        try:
            telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=update.effective_user.id)
            user = await sync_to_async(lambda: telegram_user.user)()
            user_role = await sync_to_async(lambda: user.role)()
            
            # Получаем задачи в зависимости от роли
            if user_role == 'admin':
                # Администратор видит все задачи
                tasks = await sync_to_async(lambda: list(ExpenseItem.objects.all().order_by('-created_at')[:15]))()
            elif user_role == 'foreman':
                # Прораб видит задачи своих проектов
                projects = await sync_to_async(lambda: list(Project.objects.filter(
                    Q(foreman=user) | Q(created_by=user)
                ).values_list('id', flat=True)))()
                tasks = await sync_to_async(lambda: list(ExpenseItem.objects.filter(
                    project_id__in=projects
                ).order_by('-created_at')[:15]))()
            else:
                # Остальные роли видят свои задачи
                tasks = await sync_to_async(lambda: list(ExpenseItem.objects.filter(
                    Q(created_by=user) | Q(assigned_to=user)
                ).order_by('-created_at')[:15]))()
            
            if not tasks:
                role_text = {
                    'admin': 'администратор',
                    'foreman': 'прораб',
                    'warehouse_keeper': 'кладовщик',
                    'supplier': 'снабженец',
                    'contractor': 'подрядчик'
                }.get(user_role, 'пользователь')
                
                await self.send_message(update, f"📭 У вас как {role_text} пока нет задач.")
                return
            
            user_role_display = await sync_to_async(lambda: user.get_role_display())()
            text = f"📋 Задачи ({user_role_display}):\n\n"
            keyboard = []
            
            # Подготавливаем данные для всех задач
            task_data = []
            for task in tasks:
                try:
                    task_status = task.status
                except:
                    task_status = 'unknown'
                
                status_emoji = {
                    'new': '🆕',
                    'todo': '📝',
                    'in_progress': '🚧',
                    'review': '👀',
                    'done': '✅',
                    'cancelled': '❌'
                }.get(task_status, '❓')
                
                # Получаем информацию о проекте
                project_name = "Без проекта"
                if hasattr(task, 'project') and task.project:
                    try:
                        project_name = task.project.name[:20] + "..." if len(task.project.name) > 20 else task.project.name
                    except:
                        project_name = "Проект"
                
                # Определяем роль в задаче
                task_role = "👤 Участник"
                if task.created_by == user:
                    task_role = "👑 Создатель"
                elif hasattr(task, 'assigned_to') and task.assigned_to == user:
                    task_role = "🎯 Исполнитель"
                
                task_data.append({
                    'task': task,
                    'status_emoji': status_emoji,
                    'project_name': project_name,
                    'task_role': task_role
                })
            
            # Теперь обрабатываем данные асинхронно
            for data in task_data:
                task = data['task']
                status_emoji = data['status_emoji']
                project_name = data['project_name']
                task_role = data['task_role']
                
                task_status_display = await sync_to_async(lambda: task.get_status_display())()
                task_created_date = await sync_to_async(lambda: task.created_at.strftime('%d.%m.%Y'))()
                
                task_description = await sync_to_async(lambda: task.description)()
                task_amount = await sync_to_async(lambda: task.amount)()
                task_id = await sync_to_async(lambda: task.id)()
                
                text += f"{status_emoji} {task_description[:35]}{'...' if len(task_description) > 35 else ''}\n"
                text += f"🏗️ {project_name} | 💰 {task_amount:,.0f}₽ | {task_status_display}\n\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"{status_emoji} {task_description[:25]}{'...' if len(task_description) > 25 else ''}",
                    callback_data=f"task_{task_id}"
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await self.send_message(update, text, reply_markup=reply_markup)
            
        except TelegramUser.DoesNotExist:
            await self.send_message(update, "❌ Сначала авторизуйтесь в веб-приложении.")
        except Exception as e:
            logger.error(f"Ошибка в tasks_command: {e}")
            await self.send_message(update, "❌ Произошла ошибка при получении задач.")
    
    async def show_project_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE, project_id: str):
        """Показать детали проекта"""
        try:
            print(f"[PROJECT_DETAILS] Получен project_id: {project_id}")
            telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=update.effective_user.id)
            user = await sync_to_async(lambda: telegram_user.user)()
            
            # Получаем проект
            project = await sync_to_async(Project.objects.get)(id=project_id)
            
            # Проверяем доступ к проекту
            has_access = False
            user_role = await sync_to_async(lambda: user.role)()
            
            # Администратор имеет доступ ко всем проектам
            if user_role == 'admin':
                has_access = True
            else:
                project_created_by = await sync_to_async(lambda: project.created_by)()
                project_foreman = await sync_to_async(lambda: project.foreman)()
                
                if project_created_by == user or project_foreman == user:
                    has_access = True
                elif await sync_to_async(ProjectMember.objects.filter(project=project, user=user).exists)():
                    has_access = True
            
            if not has_access:
                await self.send_message(update, "❌ У вас нет доступа к этому проекту.")
                return
            
            # Получаем статистику проекта
            total_tasks = await sync_to_async(ExpenseItem.objects.filter(project=project).count)()
            completed_tasks = await sync_to_async(ExpenseItem.objects.filter(project=project, status='done').count)()
            
            try:
                project_status = project.status
            except:
                project_status = 'unknown'
            
            status_emoji = {
                'planning': '📋',
                'in_progress': '🚧',
                'on_hold': '⏸️',
                'completed': '✅',
                'cancelled': '❌'
            }.get(project_status, '❓')
            
            project_status_display = await sync_to_async(lambda: project.get_status_display())()
            foreman_name = await sync_to_async(lambda: project.foreman.get_full_name() if project.foreman else 'Не назначен')()
            
            project_name = await sync_to_async(lambda: project.name)()
            project_budget = await sync_to_async(lambda: project.budget)()
            project_spent = await sync_to_async(lambda: project.spent_amount)()
            project_description = await sync_to_async(lambda: project.description)()
            
            if project_budget > 0:
                progress = (project_spent / project_budget) * 100
                text = f"🏗️ {project_name}\n{status_emoji} {project_status_display}\n💰 {project_budget:,.0f}₽ | 💸 {project_spent:,.0f}₽ | 📊 {progress:.0f}%\n📋 {total_tasks} задач ({completed_tasks} выполнено)\n👷 {foreman_name}\n"
            else:
                text = f"🏗️ {project_name}\n{status_emoji} {project_status_display}\n💰 {project_budget:,.0f}₽ | 💸 {project_spent:,.0f}₽\n📋 {total_tasks} задач ({completed_tasks} выполнено)\n👷 {foreman_name}\n"
            
            if project_description:
                text += f"\n📝 Описание:\n{project_description[:200]}{'...' if len(project_description) > 200 else ''}\n"
            
            # Кнопки действий
            keyboard = [
                [InlineKeyboardButton("📋 Задачи проекта", callback_data=f"project_tasks_{project_id}")],
                [InlineKeyboardButton("➕ Создать задачу", callback_data=f"create_task_project_{project_id}")],
                [InlineKeyboardButton("🔙 Назад к проектам", callback_data="projects")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await self.send_message(update, text, reply_markup=reply_markup)
            
        except Project.DoesNotExist:
            await self.send_message(update, "❌ Проект не найден.")
        except Exception as e:
            logger.error(f"Ошибка в show_project_details: {e}")
            await self.send_message(update, "❌ Произошла ошибка при получении проекта.")
    
    async def show_project_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE, project_id: str):
        """Показать задачи проекта"""
        try:
            telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=update.effective_user.id)
            user = await sync_to_async(lambda: telegram_user.user)()
            
            # Получаем проект
            project = await sync_to_async(Project.objects.get)(id=project_id)
            
            # Проверяем доступ к проекту
            user_role = await sync_to_async(lambda: user.role)()
            has_access = False
            
            # Администратор имеет доступ ко всем проектам
            if user_role == 'admin':
                has_access = True
            else:
                project_created_by = await sync_to_async(lambda: project.created_by)()
                project_foreman = await sync_to_async(lambda: project.foreman)()
                
                if project_created_by == user or project_foreman == user:
                    has_access = True
                elif await sync_to_async(ProjectMember.objects.filter(project=project, user=user).exists)():
                    has_access = True
            
            if not has_access:
                await self.send_message(update, "❌ У вас нет доступа к этому проекту.")
                return
            
            # Получаем задачи проекта
            tasks = await sync_to_async(list)(ExpenseItem.objects.filter(project=project).order_by('-created_at')[:10])
            
            project_name = await sync_to_async(lambda: project.name)()
            
            if not tasks:
                await self.send_message(update, f"📭 В проекте '{project_name}' пока нет задач.")
                return
            
            text = f"📋 Задачи: {project_name}\n\n"
            keyboard = []
            
            for task in tasks:
                try:
                    task_status = task.status
                except:
                    task_status = 'unknown'
                
                status_emoji = {
                    'new': '🆕',
                    'todo': '📝',
                    'in_progress': '🚧',
                    'review': '👀',
                    'done': '✅',
                    'cancelled': '❌'
                }.get(task_status, '❓')
                
                task_status_display = await sync_to_async(lambda: task.get_status_display())()
                task_creator_name = await sync_to_async(lambda: task.created_by.get_full_name())()
                
                try:
                    task_description = task.description
                    task_amount = task.amount
                    task_id = task.id
                except:
                    task_description = "Задача"
                    task_amount = 0
                    task_id = "unknown"
                
                text += f"{status_emoji} {task_description[:40]}{'...' if len(task_description) > 40 else ''}\n"
                text += f"💰 {task_amount:,.0f}₽ | {task_status_display} | 👤 {task_creator_name}\n\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"{status_emoji} {task_description[:25]}{'...' if len(task_description) > 25 else ''}",
                    callback_data=f"task_{task_id}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад к проекту", callback_data=f"project_{project_id}")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await self.send_message(update, text, reply_markup=reply_markup)
            
        except Project.DoesNotExist:
            await self.send_message(update, "❌ Проект не найден.")
        except Exception as e:
            logger.error(f"Ошибка в show_project_tasks: {e}")
            await self.send_message(update, "❌ Произошла ошибка при получении задач проекта.")
    
    async def show_project_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE, project_id: str):
        """Показать статистику проекта"""
        try:
            telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=update.effective_user.id)
            user = await sync_to_async(lambda: telegram_user.user)()
            
            # Получаем проект
            project = await sync_to_async(Project.objects.get)(id=project_id)
            
            # Получаем статистику
            total_tasks = await sync_to_async(ExpenseItem.objects.filter(project=project).count)()
            completed_tasks = await sync_to_async(ExpenseItem.objects.filter(project=project, status='done').count)()
            pending_tasks = await sync_to_async(ExpenseItem.objects.filter(project=project, status='todo').count)()
            in_progress_tasks = await sync_to_async(ExpenseItem.objects.filter(project=project, status='in_progress').count)()
            
            # Общая сумма задач
            total_amount = await sync_to_async(ExpenseItem.objects.filter(project=project).aggregate(
                total=models.Sum('amount')
            ))()
            total_amount = total_amount['total'] or 0
            
            project_name = await sync_to_async(lambda: project.name)()
            project_budget = await sync_to_async(lambda: project.budget)()
            project_spent = await sync_to_async(lambda: project.spent_amount)()
            
            text = f"📊 Статистика проекта '{project_name}':\n\n"
            text += f"📋 Всего задач: {total_tasks}\n"
            text += f"✅ Выполнено: {completed_tasks}\n"
            text += f"⏳ В ожидании: {pending_tasks}\n"
            text += f"🚧 В работе: {in_progress_tasks}\n\n"
            text += f"💰 Общая сумма задач: {total_amount:,.2f} ₽\n"
            text += f"💰 Бюджет проекта: {project_budget:,.2f} ₽\n"
            text += f"💸 Потрачено: {project_spent:,.2f} ₽\n"
            
            if project_budget > 0:
                budget_progress = (project_spent / project_budget) * 100
                text += f"📊 Использование бюджета: {budget_progress:.1f}%\n"
            
            if total_tasks > 0:
                task_progress = (completed_tasks / total_tasks) * 100
                text += f"📊 Прогресс задач: {task_progress:.1f}%\n"
            
            keyboard = [[InlineKeyboardButton("🔙 Назад к проекту", callback_data=f"project_{project_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await self.send_message(update, text, reply_markup=reply_markup)
            
        except Project.DoesNotExist:
            await self.send_message(update, "❌ Проект не найден.")
        except Exception as e:
            logger.error(f"Ошибка в show_project_stats: {e}")
            await self.send_message(update, "❌ Произошла ошибка при получении статистики проекта.")
    
    async def stages_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stages - показать этапы строительства"""
        try:
            stages = await sync_to_async(list)(ConstructionStage.objects.filter(is_active=True).order_by('order'))
            
            if not stages:
                await self.send_message(update, "📭 Этапы строительства не настроены.")
                return
            
            text = "🏗️ Этапы строительства:\n\n"
            
            for i, stage in enumerate(stages, 1):
                text += f"{i}. {stage.name}\n"
                if stage.description:
                    text += f"   {stage.description}\n"
                text += "\n"
            
            await self.send_message(update, text)
            
        except Exception as e:
            logger.error(f"Ошибка в stages_command: {e}")
            await self.send_message(update, "❌ Произошла ошибка при получении этапов.")
    
    async def create_task_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /create_task - создать новую задачу"""
        try:
            telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=update.effective_user.id)
            user = await sync_to_async(lambda: telegram_user.user)()
            
            # Получаем проекты через метод get_accessible_projects()
            projects = await sync_to_async(list)(user.get_accessible_projects().order_by('-created_at')[:10])
            
            if not projects:
                await self.send_message(update, "❌ У вас нет проектов для создания задач.")
                return
            
            text = "➕ Создание новой задачи\n\nВыберите проект:"
            keyboard = []
            
            for project in projects:
                try:
                    project_name = project.name
                    project_id = project.id
                except:
                    project_name = "Проект"
                    project_id = "unknown"
                
                keyboard.append([InlineKeyboardButton(
                    f"🏗️ {project_name}",
                    callback_data=f"create_task_project_{project_id}"
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await self.send_message(update, text, reply_markup=reply_markup)
            
        except TelegramUser.DoesNotExist:
            await self.send_message(update, "❌ Сначала авторизуйтесь в веб-приложении.")
        except Exception as e:
            logger.error(f"Ошибка в create_task_command: {e}")
            await self.send_message(update, "❌ Произошла ошибка при создании задачи.")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        print(f"[CALLBACK] Получен callback: {data}")
        
        if data == "my_tasks":
            # Создаем мок объект update для команд
            mock_update = Update(update_id=update.update_id, callback_query=query)
            await self.tasks_command(mock_update, context)
        elif data == "projects":
            mock_update = Update(update_id=update.update_id, callback_query=query)
            await self.projects_command(mock_update, context)
        elif data == "tasks":
            mock_update = Update(update_id=update.update_id, callback_query=query)
            await self.tasks_command(mock_update, context)
        elif data == "create_task":
            mock_update = Update(update_id=update.update_id, callback_query=query)
            await self.create_task_command(mock_update, context)
        elif data == "help":
            mock_update = Update(update_id=update.update_id, callback_query=query)
            await self.help_command(mock_update, context)
        elif data == "stages":
            mock_update = Update(update_id=update.update_id, callback_query=query)
            await self.stages_command(mock_update, context)
        elif data.startswith("create_task_project_"):
            project_id = data.replace("create_task_project_", "")
            mock_update = Update(update_id=update.update_id, callback_query=query)
            await self.start_create_task(mock_update, context, project_id)
        elif data.startswith("project_tasks_"):
            project_id = data.replace("project_tasks_", "")
            print(f"[CALLBACK] Обрабатываем project_tasks с ID: {project_id}")
            mock_update = Update(update_id=update.update_id, callback_query=query)
            await self.show_project_tasks(mock_update, context, project_id)
        elif data.startswith("project_"):
            project_id = data.replace("project_", "")
            mock_update = Update(update_id=update.update_id, callback_query=query)
            await self.show_project_details(mock_update, context, project_id)
        elif data.startswith("task_"):
            task_id = data.replace("task_", "")
            mock_update = Update(update_id=update.update_id, callback_query=query)
            await self.show_task_details(mock_update, context, task_id)
    
    
    async def show_task_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE, task_id):
        """Показать детали задачи"""
        try:
            task = await sync_to_async(ExpenseItem.objects.get)(id=task_id)
            
            try:
                task_status = task.status
            except:
                task_status = 'unknown'
            
            status_emoji = {
                'new': '🆕', 'todo': '📝', 'in_progress': '🚧',
                'review': '👀', 'done': '✅', 'cancelled': '❌'
            }.get(task_status, '📝')
            
            task_status_display = await sync_to_async(lambda: task.get_status_display())()
            task_creator_name = await sync_to_async(lambda: task.created_by.get_full_name())()
            task_assigned_name = await sync_to_async(lambda: task.assigned_to.get_full_name() if task.assigned_to else None)()
            
            task_project_name = await sync_to_async(lambda: task.project.name)()
            task_stage_name = await sync_to_async(lambda: task.stage.name if task.stage else None)()
            
            task_title = await sync_to_async(lambda: task.title)()
            task_created_date = await sync_to_async(lambda: task.created_at.strftime('%d.%m.%Y %H:%M'))()
            task_amount = await sync_to_async(lambda: task.amount)()
            task_description = await sync_to_async(lambda: task.description)()
            
            text = f"{status_emoji} {task_title}\n"
            text += f"📊 {task_status_display} | 💰 {task_amount:,.0f}₽\n"
            text += f"🏗️ {task_project_name}\n"
            text += f"👤 {task_creator_name}"
            if task_assigned_name:
                text += f" → {task_assigned_name}"
            text += f"\n📅 {task_created_date}\n"
            
            if task_description:
                text += f"\n📝 {task_description[:100]}{'...' if len(task_description) > 100 else ''}\n"
            
            if task_stage_name:
                text += f"🏗️ Этап: {task_stage_name}\n"
            
            task_project_id = await sync_to_async(lambda: task.project.id)()
            keyboard = [
                [InlineKeyboardButton("🔙 Назад к задачам", callback_data="my_tasks")],
                [InlineKeyboardButton("🏗️ Проект", callback_data=f"project_{task_project_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.send_message(update, text, reply_markup=reply_markup)
            
        except ExpenseItem.DoesNotExist:
            await self.send_message(update, "❌ Задача не найдена.")
        except Exception as e:
            logger.error(f"Ошибка в show_task_details: {e}")
            await self.send_message(update, "❌ Произошла ошибка.")
    
    async def start_create_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE, project_id):
        """Начать создание задачи"""
        try:
            project = await sync_to_async(Project.objects.get)(id=project_id)
            
            # Сохраняем project_id в контексте
            context.user_data['creating_task'] = {
                'project_id': project_id
            }
            
            project_name = await sync_to_async(lambda: project.name)()
            text = f"➕ Создание задачи для проекта: {project_name}\n\n"
            text += "📝 Напишите задачу в любом формате:\n"
            text += "• Название задачи. Описание. 1000₽\n"
            text += "• Нужно купить материалы. 5000 рублей\n"
            text += "• Сделать монтаж. Описание работы. 2 тыс\n\n"
            text += "📸 Можете прикрепить фото или файл!\n"
            text += "📎 Поддерживаются: JPG, PNG, PDF, DOC, XLS\n\n"
            text += "💡 СОВЕТ: Отправьте фото с подписью - бот сразу создаст задачу!\n"
            text += "Пример: 'Купить материалы. 5000₽' + фото\n\n"
            text += "Бот сам поймет название, описание и сумму!"
            
            await self.send_message(update, text)
            
        except Project.DoesNotExist:
            await self.send_message(update, "❌ Проект не найден.")
        except Exception as e:
            logger.error(f"Ошибка в start_create_task: {e}")
            await self.send_message(update, "❌ Произошла ошибка.")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений для создания задач"""
        try:
            # Проверяем, находится ли пользователь в процессе создания задачи
            if 'creating_task' not in context.user_data:
                return
            
            creating_task = context.user_data['creating_task']
            project_id = creating_task.get('project_id')
            
            if not project_id:
                return
            
            text = update.message.text.strip()
            
            # Умное понимание сообщения - извлекаем всю информацию сразу
            tasks_data = self.parse_task_message(text)
            
            # Создаем задачи с извлеченными данными
            await self.create_task_smart(update, context, project_id, tasks_data)
                
        except Exception as e:
            logger.error(f"Ошибка в handle_text_message: {e}")
            await self.send_message(update, "❌ Произошла ошибка при создании задачи.")
    
    def parse_task_message(self, text: str) -> list:
        """Умное извлечение информации о задачах из сообщения"""
        import re
        
        # Проверяем, есть ли нумерованный список задач
        numbered_tasks = re.findall(r'^\s*\d+\.\s*(.+)$', text, re.MULTILINE)
        
        if numbered_tasks:
            # Создаем отдельные задачи для каждого пункта
            tasks = []
            for task_text in numbered_tasks:
                task_data = self.parse_single_task(task_text.strip())
                tasks.append(task_data)
            
            # Ограничиваем количество задач (максимум 20)
            if len(tasks) > 20:
                tasks = tasks[:20]
            
            return tasks
        else:
            # Обрабатываем как одну задачу
            return [self.parse_single_task(text)]
    
    def parse_single_task(self, text: str) -> dict:
        """Извлечение информации об одной задаче"""
        import re
        
        # Инициализируем данные
        task_data = {
            'title': '',
            'description': '',
            'amount': 0.0
        }
        
        # Ищем сумму в тексте (различные форматы)
        amount_patterns = [
            r'(\d+(?:\.\d+)?)\s*₽',  # 1000₽
            r'(\d+(?:\.\d+)?)\s*руб',  # 1000 руб
            r'(\d+(?:\.\d+)?)\s*рублей',  # 1000 рублей
            r'(\d+(?:\.\d+)?)\s*р',  # 1000р
            r'(\d+(?:\.\d+)?)\s*тыс',  # 1000 тыс
            r'(\d+(?:\.\d+)?)\s*тысяч',  # 1000 тысяч
            r'(\d+(?:\.\d+)?)\s*к',  # 1000к
        ]
        
        amount = 0.0
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = float(match.group(1))
                # Если это тысячи, умножаем на 1000
                if 'тыс' in pattern or 'тысяч' in pattern or 'к' in pattern:
                    amount *= 1000
                break
        
        task_data['amount'] = amount
        
        # Убираем сумму из текста для извлечения названия и описания
        clean_text = text
        for pattern in amount_patterns:
            clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
        
        # Ищем название задачи (обычно в начале или после ключевых слов)
        title_patterns = [
            r'^([^.!?]+)[.!?]',  # До первой точки
            r'задача[:\s]+([^.!?]+)',  # После "задача:"
            r'нужно[:\s]+([^.!?]+)',  # После "нужно:"
            r'сделать[:\s]+([^.!?]+)',  # После "сделать:"
        ]
        
        title = ''
        for pattern in title_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                break
        
        # Если название не найдено, берем первые слова
        if not title:
            words = clean_text.split()
            if len(words) > 0:
                title = ' '.join(words[:5])  # Первые 5 слов
        
        task_data['title'] = title
        
        # Описание - остальной текст
        if title and title in clean_text:
            description = clean_text.replace(title, '').strip()
        else:
            description = clean_text.strip()
        
        # Очищаем описание от лишних символов
        description = re.sub(r'[^\w\s.,!?-]', '', description)
        task_data['description'] = description
        
        return task_data
    
    async def create_task_smart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, project_id: str, tasks_data: list):
        """Умное создание задач"""
        try:
            # Получаем пользователя
            telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=update.effective_user.id)
            user = await sync_to_async(lambda: telegram_user.user)()
            
            # Получаем проект
            project = await sync_to_async(Project.objects.get)(id=project_id)
            
            # Получаем первую колонку проекта (колонка "Новые")
            from kanban.models import KanbanColumn
            column = await sync_to_async(KanbanColumn.objects.filter(board__project=project).first)()
            
            if not column:
                # Создаем колонку если её нет
                from kanban.models import KanbanBoard
                board, created = await sync_to_async(KanbanBoard.objects.get_or_create)(
                    project=project,
                    defaults={'created_by': user}
                )
                column = await sync_to_async(KanbanColumn.objects.create)(
                    board=board,
                    name="Новые",
                    order=0
                )
            
            created_tasks = []
            
            # Создаем задачи
            for task_data in tasks_data:
                task = await sync_to_async(ExpenseItem.objects.create)(
                    title=task_data['title'],
                    description=task_data['description'],
                    amount=task_data['amount'],
                    project=project,
                    column=column,
                    created_by=user,
                    status='new'
                )
                created_tasks.append(task)
            
            # Обрабатываем вложения (прикрепляем к первой задаче)
            attachments = context.user_data['creating_task'].get('attachments', [])
            if attachments and created_tasks:
                # Сохраняем информацию о вложениях в описании первой задачи
                attachment_info = []
                for attachment in attachments:
                    if attachment['type'] == 'photo':
                        attachment_info.append(f"📸 {attachment['filename']}")
                    elif attachment['type'] == 'document':
                        attachment_info.append(f"📎 {attachment['original_filename']}")
                
                if attachment_info:
                    # Обновляем описание первой задачи с информацией о вложениях
                    first_task = created_tasks[0]
                    updated_description = first_task.description
                    if updated_description:
                        updated_description += f"\n\nВложения:\n" + "\n".join(attachment_info)
                    else:
                        updated_description = "Вложения:\n" + "\n".join(attachment_info)
                    
                    # Обновляем задачу
                    first_task.description = updated_description
                    await sync_to_async(first_task.save)()
            
            # Очищаем данные создания задачи
            del context.user_data['creating_task']
            
            # Формируем ответ
            if len(created_tasks) == 1:
                response = f"✅ Задача создана!\n\n"
                task_data = tasks_data[0]
                response += f"📋 {task_data['title']}\n"
                if task_data['description']:
                    response += f"📝 {task_data['description']}\n"
                if task_data['amount'] > 0:
                    response += f"💰 {task_data['amount']:,.0f}₽\n"
                if attachments:
                    response += f"📎 Вложений: {len(attachments)}\n"
            else:
                response = f"✅ Создано {len(created_tasks)} задач!\n\n"
                for i, task_data in enumerate(tasks_data[:5], 1):  # Показываем первые 5 задач
                    response += f"{i}. {task_data['title']}\n"
                    if task_data['amount'] > 0:
                        response += f"   💰 {task_data['amount']:,.0f}₽\n"
                
                if len(tasks_data) > 5:
                    response += f"\n... и еще {len(tasks_data) - 5} задач"
                
                if attachments:
                    response += f"\n📎 Вложений: {len(attachments)}\n"
            
            await self.send_message(update, response)
            
        except Exception as e:
            logger.error(f"Ошибка в create_task_smart: {e}")
            await self.send_message(update, "❌ Произошла ошибка при создании задач.")
    
    async def handle_photo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка фото для создания задач"""
        try:
            # Проверяем, находится ли пользователь в процессе создания задачи
            if 'creating_task' not in context.user_data:
                return
            
            creating_task = context.user_data['creating_task']
            project_id = creating_task.get('project_id')
            
            if not project_id:
                return
            
            # Получаем фото
            photo = update.message.photo[-1]  # Берем самое большое фото
            file_id = photo.file_id
            
            # Скачиваем фото
            file = await context.bot.get_file(file_id)
            file_path = file.file_path
            
            # Создаем уникальное имя файла
            import os
            import uuid
            from datetime import datetime
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            filename = f"task_photo_{timestamp}_{unique_id}.jpg"
            
            # Путь для сохранения
            media_dir = "media/expense_photos"
            os.makedirs(media_dir, exist_ok=True)
            local_path = os.path.join(media_dir, filename)
            
            # Скачиваем файл
            await file.download_to_drive(local_path)
            
            # Сохраняем информацию о файле в контексте
            if 'attachments' not in context.user_data['creating_task']:
                context.user_data['creating_task']['attachments'] = []
            
            context.user_data['creating_task']['attachments'].append({
                'type': 'photo',
                'file_path': local_path,
                'filename': filename,
                'file_id': file_id
            })
            
            # Проверяем, есть ли текст в подписи к фото
            caption = update.message.caption
            if caption and caption.strip():
                # Если есть текст в подписи, обрабатываем его как задачи
                tasks_data = self.parse_task_message(caption)
                await self.create_task_smart(update, context, project_id, tasks_data)
            else:
                await self.send_message(update, f"📸 Фото добавлено к задаче!\n\n📝 Теперь напишите описание задачи:")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_photo_message: {e}")
            await self.send_message(update, "❌ Произошла ошибка при обработке фото.")
    
    async def handle_document_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка файлов для создания задач"""
        try:
            # Проверяем, находится ли пользователь в процессе создания задачи
            if 'creating_task' not in context.user_data:
                return
            
            creating_task = context.user_data['creating_task']
            project_id = creating_task.get('project_id')
            
            if not project_id:
                return
            
            # Получаем документ
            document = update.message.document
            file_id = document.file_id
            filename = document.file_name
            
            # Скачиваем файл
            file = await context.bot.get_file(file_id)
            file_path = file.file_path
            
            # Создаем уникальное имя файла
            import os
            import uuid
            from datetime import datetime
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            file_extension = os.path.splitext(filename)[1]
            new_filename = f"task_file_{timestamp}_{unique_id}{file_extension}"
            
            # Путь для сохранения
            media_dir = "media/expense_photos"
            os.makedirs(media_dir, exist_ok=True)
            local_path = os.path.join(media_dir, new_filename)
            
            # Скачиваем файл
            await file.download_to_drive(local_path)
            
            # Сохраняем информацию о файле в контексте
            if 'attachments' not in context.user_data['creating_task']:
                context.user_data['creating_task']['attachments'] = []
            
            context.user_data['creating_task']['attachments'].append({
                'type': 'document',
                'file_path': local_path,
                'filename': new_filename,
                'original_filename': filename,
                'file_id': file_id
            })
            
            await self.send_message(update, f"📎 Файл '{filename}' добавлен к задаче!\n\n📝 Теперь напишите описание задачи:")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_document_message: {e}")
            await self.send_message(update, "❌ Произошла ошибка при обработке файла.")
    
    async def create_task_from_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE, project_id: str):
        """Создание задачи из собранных данных"""
        try:
            creating_task = context.user_data['creating_task']
            title = creating_task.get('title', '')
            description = creating_task.get('description', '')
            amount = creating_task.get('amount', 0.0)
            
            # Получаем пользователя
            telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=update.effective_user.id)
            user = await sync_to_async(lambda: telegram_user.user)()
            
            # Получаем проект
            project = await sync_to_async(Project.objects.get)(id=project_id)
            
            # Получаем первую колонку проекта (колонка "Новые")
            from kanban.models import KanbanColumn
            column = await sync_to_async(KanbanColumn.objects.filter(board__project=project).first)()
            
            if not column:
                # Создаем колонку если её нет
                from kanban.models import KanbanBoard
                board, created = await sync_to_async(KanbanBoard.objects.get_or_create)(
                    project=project,
                    defaults={'created_by': user}
                )
                column = await sync_to_async(KanbanColumn.objects.create)(
                    board=board,
                    name="Новые",
                    order=0
                )
            
            # Создаем задачу
            task = await sync_to_async(ExpenseItem.objects.create)(
                title=title,
                description=description,
                amount=amount,
                project=project,
                column=column,
                created_by=user,
                status='new'
            )
            
            # Очищаем данные создания задачи
            del context.user_data['creating_task']
            
            await self.send_message(update, f"✅ Задача '{title}' успешно создана!\n\n📋 Перейти к задачам: /tasks")
            
        except Exception as e:
            logger.error(f"Ошибка в create_task_from_data: {e}")
            await self.send_message(update, "❌ Произошла ошибка при создании задачи.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_data = context.user_data
        
        if 'creating_task' in user_data:
            await self.handle_task_creation(update, context)
        else:
            # Обычное сообщение
            await update.message.reply_text(
                "❓ Не понимаю. Используйте /help для списка команд."
            )
    
    async def handle_task_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка создания задачи пошагово"""
        user_data = context.user_data['creating_task']
        step = user_data['step']
        text = update.message.text
        
        if step == 'title':
            user_data['title'] = text
            user_data['step'] = 'description'
            await update.message.reply_text("📝 Введите описание задачи (или отправьте '-' для пропуска):")
        
        elif step == 'description':
            if text != '-':
                user_data['description'] = text
            user_data['step'] = 'type'
            
            # Показываем типы задач
            keyboard = [
                [InlineKeyboardButton("🛠️ Работа", callback_data="task_type_work")],
                [InlineKeyboardButton("🛒 Закупка", callback_data="task_type_purchase")],
                [InlineKeyboardButton("🚚 Поставка", callback_data="task_type_delivery")],
                [InlineKeyboardButton("🔧 Монтаж", callback_data="task_type_installation")],
                [InlineKeyboardButton("👀 Контроль", callback_data="task_type_control")],
                [InlineKeyboardButton("📄 Документация", callback_data="task_type_documentation")],
                [InlineKeyboardButton("❓ Прочее", callback_data="task_type_other")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text("🔧 Выберите тип задачи:", reply_markup=reply_markup)
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск Construction Bot...")
        try:
            self.application.run_polling()
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise


# Создаем глобальный экземпляр бота
_bot_instance = None

def get_bot_instance():
    """Получение экземпляра бота"""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = ConstructionBot()
    return _bot_instance

def send_message_to_user(user_id, text, reply_markup=None):
    """Синхронная обертка для отправки сообщения пользователю"""
    import asyncio
    
    async def _send():
        bot = get_bot_instance()
        return await bot.send_message_to_user(user_id, text, reply_markup)
    
    try:
        # Пытаемся использовать существующий event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Если loop уже запущен, создаем задачу
            import threading
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _send())
                return future.result()
        else:
            return loop.run_until_complete(_send())
    except RuntimeError:
        # Если нет event loop, создаем новый
        return asyncio.run(_send())

if __name__ == '__main__':
    bot = ConstructionBot()
    bot.run()
