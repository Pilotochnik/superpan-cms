from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import hashlib
import uuid
import logging

logger = logging.getLogger(__name__)


class UserManager(BaseUserManager):
    """Кастомный менеджер пользователей"""
    
    def create_user(self, email=None, password=None, **extra_fields):
        if email:
            email = self.normalize_email(email)
            extra_fields.setdefault('username', email)
        else:
            # Генерируем временный email если не указан
            import uuid
            email = f"temp_{uuid.uuid4().hex[:8]}@superpan.com"
            extra_fields.setdefault('username', email)
        
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Кастомная модель пользователя с ролями и привязкой к устройству"""
    
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Администратор-суперпользователь')
        CHIEF_ENGINEER = 'chief_engineer', _('Главный инженер')
        FOREMAN = 'foreman', _('Прораб')
        WAREHOUSE_KEEPER = 'warehouse_keeper', _('Кладовщик')
        SUPPLIER = 'supplier', _('Снабженец')
        ECONOMIST = 'economist', _('Экономист/Начальник коммерческого отдела')
        CONTRACTOR = 'contractor', _('Подрядчик')
    
    email = models.EmailField(_('Email адрес'), unique=True, blank=True, null=True)
    role = models.CharField(
        _('Роль'),
        max_length=20,
        choices=Role.choices,
        default=Role.CONTRACTOR
    )
    phone = models.CharField(_('Телефон'), max_length=20, blank=True)
    is_active_session = models.BooleanField(_('Активная сессия'), default=False)
    device_fingerprint = models.CharField(
        _('Отпечаток устройства'),
        max_length=128,
        blank=True,
        help_text=_('Уникальный идентификатор устройства пользователя')
    )
    last_login_ip = models.GenericIPAddressField(_('Последний IP'), blank=True, null=True)
    failed_login_attempts = models.PositiveIntegerField(_('Неудачные попытки входа'), default=0)
    locked_until = models.DateTimeField(_('Заблокирован до'), blank=True, null=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        db_table = 'users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        if full_name:
            return full_name
        elif self.email:
            return self.email
        else:
            return f"User {self.id}"

    def is_admin_role(self):
        """Проверяет, является ли пользователь администратором"""
        return self.role == self.Role.ADMIN or self.is_superuser
    
    def is_chief_engineer_role(self):
        """Проверяет, является ли пользователь главным инженером"""
        return self.role == self.Role.CHIEF_ENGINEER
    
    def is_foreman_role(self):
        """Проверяет, является ли пользователь прорабом"""
        return self.role == self.Role.FOREMAN
    
    def is_warehouse_keeper_role(self):
        """Проверяет, является ли пользователь кладовщиком"""
        return self.role == self.Role.WAREHOUSE_KEEPER
    
    def is_supplier_role(self):
        """Проверяет, является ли пользователь снабженцем"""
        return self.role == self.Role.SUPPLIER
    
    def is_economist_role(self):
        """Проверяет, является ли пользователь экономистом"""
        return self.role == self.Role.ECONOMIST
    
    def is_contractor_role(self):
        """Проверяет, является ли пользователь подрядчиком"""
        return self.role == self.Role.CONTRACTOR
    
    @classmethod
    def get_by_telegram_id(cls, telegram_id):
        """Получает пользователя по Telegram ID"""
        try:
            telegram_user = TelegramUser.objects.select_related('user').get(telegram_id=telegram_id)
            return telegram_user.user
        except TelegramUser.DoesNotExist:
            return None
    
    def get_telegram_id(self):
        """Получает Telegram ID пользователя"""
        try:
            from .models import TelegramUser
            telegram_user = TelegramUser.objects.filter(user=self).first()
            return telegram_user.telegram_id if telegram_user else None
        except:
            return None

    def can_manage_users(self):
        """Может ли пользователь управлять пользователями"""
        return self.is_admin_role()
    
    def can_manage_projects(self):
        """Может ли пользователь управлять проектами"""
        return self.is_admin_role() or self.is_chief_engineer_role()
    
    def can_manage_warehouse(self):
        """Может ли пользователь управлять складом"""
        return self.is_admin_role() or self.is_chief_engineer_role() or self.is_warehouse_keeper_role() or self.is_supplier_role()
    
    def can_view_finances(self):
        """Может ли пользователь видеть финансовую информацию"""
        return self.is_admin_role() or self.is_chief_engineer_role()
    
    def can_control_foremen(self):
        """Может ли пользователь контролировать прорабов"""
        return self.is_admin_role() or self.is_chief_engineer_role()
    
    def can_manage_prices(self):
        """Может ли пользователь управлять ценами"""
        return self.is_admin_role() or self.is_chief_engineer_role()
    
    def can_view_all_projects(self):
        """Может ли пользователь видеть все проекты"""
        return self.is_admin_role() or self.is_chief_engineer_role()
    
    def can_create_projects(self):
        """Может ли пользователь создавать проекты"""
        return self.is_admin_role()
    
    def can_edit_projects(self):
        """Может ли пользователь редактировать проекты"""
        return self.is_admin_role() or self.is_chief_engineer_role()
    
    def can_manage_project_tasks(self):
        """Может ли пользователь управлять задачами проекта"""
        return self.is_admin_role() or self.is_chief_engineer_role() or self.is_foreman_role()
    
    def can_view_project_schedule(self):
        """Может ли пользователь видеть сроки проекта"""
        return self.is_admin_role() or self.is_chief_engineer_role() or self.is_foreman_role()
    
    def can_control_warehouse(self):
        """Может ли пользователь контролировать склад"""
        return self.is_admin_role() or self.is_chief_engineer_role()
    
    def can_view_project_budget(self):
        """Может ли пользователь видеть бюджет проекта"""
        return self.is_admin_role() or self.is_chief_engineer_role() or self.is_economist_role()
    
    def can_view_prices(self):
        """Может ли пользователь видеть цены"""
        return self.is_admin_role() or self.is_chief_engineer_role() or self.is_supplier_role() or self.is_economist_role()
    
    def can_manage_warehouse_items(self):
        """Может ли пользователь управлять товарами склада"""
        return self.is_admin_role() or self.is_chief_engineer_role() or self.is_warehouse_keeper_role() or self.is_supplier_role()
    
    def can_view_warehouse_reports(self):
        """Может ли пользователь видеть отчеты склада"""
        return self.is_admin_role() or self.is_chief_engineer_role() or self.is_warehouse_keeper_role() or self.is_supplier_role()
    
    def can_manage_equipment_photos(self):
        """Может ли пользователь управлять фото оборудования"""
        return self.is_admin_role() or self.is_chief_engineer_role() or self.is_warehouse_keeper_role()
    
    def can_approve_changes(self):
        """Может ли пользователь одобрять изменения"""
        return self.is_admin_role()
    
    def can_edit_project_status(self):
        """Может ли пользователь редактировать статус проекта"""
        return self.is_admin_role()
    
    def can_confirm_tasks(self):
        """Может ли пользователь подтверждать задачи"""
        return self.is_admin_role()
    
    def can_view_projects(self):
        """Может ли пользователь просматривать проекты"""
        return self.is_admin_role() or self.is_chief_engineer_role() or self.is_foreman_role() or self.is_contractor_role()
    
    def can_view_estimates(self):
        """Может ли пользователь просматривать сметы"""
        return self.is_admin_role() or self.is_chief_engineer_role() or self.is_foreman_role()
    
    def can_manage_tasks(self):
        """Может ли пользователь управлять задачами"""
        return self.is_admin_role() or self.is_chief_engineer_role() or self.is_foreman_role()
    
    def can_view_tasks(self):
        """Может ли пользователь просматривать задачи"""
        return self.is_admin_role() or self.is_chief_engineer_role() or self.is_foreman_role() or self.is_contractor_role()
    
    def can_view_finances(self):
        """Может ли пользователь видеть финансовую информацию"""
        return self.is_admin_role() or self.is_chief_engineer_role()
    
    def can_view_project_budget(self):
        """Может ли пользователь видеть бюджет проекта"""
        return self.is_admin_role() or self.is_chief_engineer_role()

    def generate_device_fingerprint(self, user_agent, ip_address):
        """Генерирует отпечаток устройства на основе user-agent и IP"""
        data = f"{user_agent}_{ip_address}_{self.email}"
        return hashlib.sha256(data.encode()).hexdigest()

    def is_device_allowed(self, user_agent, ip_address):
        """Проверяет, разрешено ли устройство для этого пользователя"""
        if not self.device_fingerprint:
            return True  # Первый вход
        
        current_fingerprint = self.generate_device_fingerprint(user_agent, ip_address)
        return self.device_fingerprint == current_fingerprint

    def bind_device(self, user_agent, ip_address):
        """Привязывает пользователя к устройству"""
        self.device_fingerprint = self.generate_device_fingerprint(user_agent, ip_address)
        self.last_login_ip = ip_address
        self.save(update_fields=['device_fingerprint', 'last_login_ip'])
    
    def get_accessible_projects(self):
        """Получить все доступные пользователю проекты"""
        from projects.models import Project
        from django.db.models import Q
        
        # Получаем проекты через ключи доступа для всех ролей
        access_keys = ProjectAccessKey.objects.filter(
            assigned_to=self,
            is_active=True
        ).values_list('project_id', flat=True)
        
        if self.is_admin_role():
            # Администраторы видят все проекты + проекты через ключи доступа
            return Project.objects.filter(
                Q(is_active=True) | Q(id__in=access_keys)
            ).distinct()
        elif self.is_foreman_role():
            # Прорабы видят свои проекты + проекты через ключи доступа
            return Project.objects.filter(
                Q(created_by=self) | Q(foreman=self) | Q(id__in=access_keys),
                is_active=True
            ).distinct()
        else:
            # Остальные роли видят только проекты через ключи доступа
            return Project.objects.filter(
                id__in=access_keys,
                is_active=True
            ).distinct()


class UserSession(models.Model):
    """Модель для отслеживания активных сессий пользователей"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь'),
        related_name='active_session'
    )
    session_key = models.CharField(_('Ключ сессии'), max_length=40, unique=True)
    device_info = models.TextField(_('Информация об устройстве'), blank=True)
    ip_address = models.GenericIPAddressField(_('IP адрес'))
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    last_activity = models.DateTimeField(_('Последняя активность'), auto_now=True)

    class Meta:
        verbose_name = _('Сессия пользователя')
        verbose_name_plural = _('Сессии пользователей')
        db_table = 'user_sessions'

    def __str__(self):
        return f"Сессия {self.user.email}"


class ProjectAccessKey(models.Model):
    """Модель для ключей доступа к проектам"""
    
    key = models.UUIDField(_('Ключ доступа'), default=uuid.uuid4, unique=True)
    project_id = models.UUIDField(_('ID проекта'))
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Создал'),
        related_name='created_access_keys'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Назначен'),
        related_name='assigned_access_keys',
        blank=True,
        null=True
    )
    description = models.TextField(_('Описание'), blank=True, help_text=_('Описание цели предоставления доступа'))
    is_active = models.BooleanField(_('Активен'), default=True)
    expires_at = models.DateTimeField(_('Истекает'), blank=True, null=True)
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)
    used_at = models.DateTimeField(_('Использован'), blank=True, null=True)

    class Meta:
        verbose_name = _('Ключ доступа к проекту')
        verbose_name_plural = _('Ключи доступа к проектам')
        db_table = 'project_access_keys'
        # Убираем unique_together чтобы можно было создавать несколько ключей
        # но логика в коде будет контролировать активные ключи

    def __str__(self):
        try:
            from projects.models import Project
            project = Project.objects.get(id=self.project_id)
            return f"Ключ для {project.name}"
        except Project.DoesNotExist:
            return f"Ключ доступа {str(self.key)[:8]}... (проект не найден)"
        except Exception as e:
            logger.error(f"Ошибка при получении проекта для ключа {self.key}: {e}")
            return f"Ключ доступа {str(self.key)[:8]}... (ошибка)"

    def is_valid(self):
        """Проверяет, действителен ли ключ"""
        if not self.is_active:
            return False
        
        if self.expires_at and self.expires_at < timezone.now():
            return False
            
        return True


class ApprovalRequest(models.Model):
    """Модель для запросов на одобрение изменений"""
    
    class RequestType(models.TextChoices):
        PROJECT_STATUS = 'project_status', _('Изменение статуса проекта')
        TASK_CONFIRMATION = 'task_confirmation', _('Подтверждение задачи')
        BUDGET_CHANGE = 'budget_change', _('Изменение бюджета')
        WAREHOUSE_ITEM = 'warehouse_item', _('Изменение товара склада')
        EQUIPMENT_PHOTO = 'equipment_photo', _('Фото оборудования')
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Ожидает одобрения')
        APPROVED = 'approved', _('Одобрено')
        REJECTED = 'rejected', _('Отклонено')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_type = models.CharField(
        _('Тип запроса'),
        max_length=20,
        choices=RequestType.choices
    )
    status = models.CharField(
        _('Статус'),
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Запросил'),
        related_name='requested_approvals'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name=_('Одобрил'),
        related_name='approved_requests',
        null=True,
        blank=True
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        verbose_name=_('Проект'),
        related_name='approval_requests',
        null=True,
        blank=True
    )
    task = models.ForeignKey(
        'kanban.ProjectTask',
        on_delete=models.CASCADE,
        verbose_name=_('Задача'),
        related_name='approval_requests',
        null=True,
        blank=True
    )
    description = models.TextField(_('Описание изменений'))
    old_data = models.JSONField(_('Старые данные'), blank=True, null=True)
    new_data = models.JSONField(_('Новые данные'), blank=True, null=True)
    rejection_reason = models.TextField(_('Причина отклонения'), blank=True)
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлен'), auto_now=True)
    approved_at = models.DateTimeField(_('Одобрен'), blank=True, null=True)

    class Meta:
        verbose_name = _('Запрос на одобрение')
        verbose_name_plural = _('Запросы на одобрение')
        db_table = 'approval_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.get_status_display()}"


class EquipmentPhoto(models.Model):
    """Модель для фото оборудования до и после"""
    
    class PhotoType(models.TextChoices):
        BEFORE = 'before', _('До')
        AFTER = 'after', _('После')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    equipment_name = models.CharField(_('Название оборудования'), max_length=200)
    photo_type = models.CharField(
        _('Тип фото'),
        max_length=10,
        choices=PhotoType.choices
    )
    photo = models.ImageField(_('Фото'), upload_to='equipment_photos/')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Загрузил'),
        related_name='uploaded_equipment_photos'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        verbose_name=_('Проект'),
        related_name='equipment_photos',
        null=True,
        blank=True
    )
    description = models.TextField(_('Описание'), blank=True)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)

    class Meta:
        verbose_name = _('Фото оборудования')
        verbose_name_plural = _('Фото оборудования')
        db_table = 'equipment_photos'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.equipment_name} - {self.get_photo_type_display()}"


class LoginAttempt(models.Model):
    """Модель для отслеживания попыток входа"""
    
    email = models.EmailField(_('Email'))
    ip_address = models.GenericIPAddressField(_('IP адрес'))
    user_agent = models.TextField(_('User Agent'), blank=True)
    success = models.BooleanField(_('Успешно'), default=False)
    failure_reason = models.CharField(_('Причина неудачи'), max_length=100, blank=True)
    created_at = models.DateTimeField(_('Время попытки'), auto_now_add=True)

    class Meta:
        verbose_name = _('Попытка входа')
        verbose_name_plural = _('Попытки входа')
        db_table = 'login_attempts'
        ordering = ['-created_at']

    def __str__(self):
        status = "Успешно" if self.success else "Неудачно"
        return f"{self.email} - {status} ({self.created_at})"


class TelegramUser(models.Model):
    """Связь пользователя с Telegram аккаунтом"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь'),
        related_name='telegram_profile'
    )
    telegram_id = models.BigIntegerField(
        _('Telegram ID'),
        unique=True,
        help_text=_('Уникальный ID пользователя в Telegram')
    )
    username = models.CharField(
        _('Telegram Username'),
        max_length=100,
        blank=True,
        help_text=_('@username в Telegram')
    )
    first_name = models.CharField(
        _('Имя в Telegram'),
        max_length=100,
        blank=True
    )
    last_name = models.CharField(
        _('Фамилия в Telegram'),
        max_length=100,
        blank=True
    )
    language_code = models.CharField(
        _('Код языка'),
        max_length=10,
        default='ru'
    )
    is_bot = models.BooleanField(
        _('Это бот'),
        default=False
    )
    is_premium = models.BooleanField(
        _('Telegram Premium'),
        default=False
    )
    photo_url = models.URLField(
        _('URL фото профиля'),
        blank=True
    )
    is_active = models.BooleanField(
        _('Активен'),
        default=True
    )
    created_at = models.DateTimeField(
        _('Создан'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Обновлен'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('Telegram профиль')
        verbose_name_plural = _('Telegram профили')
        db_table = 'telegram_users'

    def __str__(self):
        return f"@{self.username or self.telegram_id} - {self.user.get_full_name()}"

    @property
    def full_name(self):
        """Полное имя из Telegram"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return f"User {self.telegram_id}"


class TelegramAuthToken(models.Model):
    """Токен авторизации для Telegram"""
    token = models.UUIDField(
        _('Токен'),
        primary_key=True,
        default=uuid.uuid4,
        help_text=_('Уникальный токен для авторизации')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь'),
        null=True,
        blank=True,
        help_text=_('Пользователь, который авторизовался через этот токен')
    )
    telegram_user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        verbose_name=_('Telegram пользователь'),
        null=True,
        blank=True,
        help_text=_('Telegram пользователь, который авторизовался')
    )
    created_at = models.DateTimeField(
        _('Создан'),
        auto_now_add=True
    )
    expires_at = models.DateTimeField(
        _('Истекает'),
        help_text=_('Время истечения токена')
    )
    is_used = models.BooleanField(
        _('Использован'),
        default=False,
        help_text=_('Был ли токен использован для авторизации')
    )

    class Meta:
        verbose_name = _('Токен авторизации Telegram')
        verbose_name_plural = _('Токены авторизации Telegram')
        db_table = 'telegram_auth_tokens'

    def __str__(self):
        return f"Token {self.token} - {self.user or 'Not used'}"

    def is_expired(self):
        """Проверка истечения токена"""
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def mark_as_used(self, user, telegram_user):
        """Отметить токен как использованный"""
        self.user = user
        self.telegram_user = telegram_user
        self.is_used = True
        self.save()