from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Project(models.Model):
    """Модель строительного проекта"""
    
    class Status(models.TextChoices):
        PLANNING = 'planning', _('Планирование')
        IN_PROGRESS = 'in_progress', _('В работе')
        ON_HOLD = 'on_hold', _('Приостановлен')
        COMPLETED = 'completed', _('Завершен')
        CANCELLED = 'cancelled', _('Отменен')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Название проекта'), max_length=200)
    description = models.TextField(_('Описание'), blank=True)
    budget = models.DecimalField(
        _('Бюджет'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    spent_amount = models.DecimalField(
        _('Потрачено'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNING
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Создал'),
        related_name='created_projects'
    )
    foreman = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        verbose_name=_('Прораб'),
        related_name='managed_projects',
        null=True,
        blank=True,
        limit_choices_to={'role': 'foreman'}
    )
    start_date = models.DateField(_('Дата начала'), blank=True, null=True)
    end_date = models.DateField(_('Дата окончания'), blank=True, null=True)
    address = models.TextField(_('Адрес объекта'), blank=True)
    avatar = models.ImageField(
        _('Аватарка проекта'),
        upload_to='project_avatars/',
        null=True,
        blank=True,
        help_text=_('Фото объекта для проекта')
    )
    is_active = models.BooleanField(_('Активен'), default=True)
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлен'), auto_now=True)

    class Meta:
        verbose_name = _('Проект')
        verbose_name_plural = _('Проекты')
        db_table = 'projects'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def remaining_budget(self):
        """Оставшийся бюджет"""
        return self.budget - self.spent_amount

    @property
    def budget_utilization_percent(self):
        """Процент использования бюджета"""
        if self.budget > 0:
            return (self.spent_amount / self.budget * 100)
        return 0

    def get_team_members(self):
        """Получить всех участников проекта"""
        from accounts.models import ProjectAccessKey
        return ProjectAccessKey.objects.filter(
            project_id=self.id,
            is_active=True,
            assigned_to__isnull=False
        ).select_related('assigned_to')

    def can_user_access(self, user):
        """Проверить, может ли пользователь получить доступ к проекту"""
        if user.is_admin_role():
            return True
        
        if self.created_by == user or self.foreman == user:
            return True
            
        from accounts.models import ProjectAccessKey
        return ProjectAccessKey.objects.filter(
            project_id=self.id,
            assigned_to=user,
            is_active=True
        ).exists()

    def update_spent_amount(self):
        """Обновить потраченную сумму на основе расходов"""
        from kanban.models import ExpenseItem
        
        total_spent = ExpenseItem.objects.filter(
            project=self,
            status='approved'
        ).aggregate(
            total=models.Sum('estimated_hours')
        )['total'] or Decimal('0.00')
        
        self.spent_amount = total_spent
        self.save(update_fields=['spent_amount'])


class ProjectMember(models.Model):
    """Участники проекта"""
    
    class Role(models.TextChoices):
        FOREMAN = 'foreman', _('Прораб')
        CONTRACTOR = 'contractor', _('Подрядчик')
        OBSERVER = 'observer', _('Наблюдатель')
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_('Проект'),
        related_name='members'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь'),
        related_name='project_memberships'
    )
    role = models.CharField(
        _('Роль в проекте'),
        max_length=20,
        choices=Role.choices,
        default=Role.CONTRACTOR
    )
    can_add_expenses = models.BooleanField(_('Может добавлять расходы'), default=True)
    can_view_budget = models.BooleanField(_('Может видеть бюджет'), default=False)
    joined_at = models.DateTimeField(_('Присоединился'), auto_now_add=True)
    is_active = models.BooleanField(_('Активен'), default=True)

    class Meta:
        verbose_name = _('Участник проекта')
        verbose_name_plural = _('Участники проекта')
        db_table = 'project_members'
        unique_together = ['project', 'user']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.project.name}"


class ProjectActivity(models.Model):
    """Журнал активности проекта"""
    
    class ActivityType(models.TextChoices):
        PROJECT_CREATED = 'project_created', _('Проект создан')
        PROJECT_UPDATED = 'project_updated', _('Проект обновлен')
        MEMBER_ADDED = 'member_added', _('Участник добавлен')
        MEMBER_REMOVED = 'member_removed', _('Участник удален')
        EXPENSE_ADDED = 'expense_added', _('Расход добавлен')
        EXPENSE_APPROVED = 'expense_approved', _('Расход одобрен')
        EXPENSE_REJECTED = 'expense_rejected', _('Расход отклонен')
        BUDGET_UPDATED = 'budget_updated', _('Бюджет обновлен')
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_('Проект'),
        related_name='activities'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь'),
        related_name='project_activities'
    )
    activity_type = models.CharField(
        _('Тип активности'),
        max_length=20,
        choices=ActivityType.choices
    )
    description = models.TextField(_('Описание'))
    metadata = models.JSONField(_('Метаданные'), blank=True, null=True)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)

    class Meta:
        verbose_name = _('Активность проекта')
        verbose_name_plural = _('Активности проекта')
        db_table = 'project_activities'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.name} - {self.get_activity_type_display()}"


class ProjectDocument(models.Model):
    """Документы проекта"""
    
    class DocumentType(models.TextChoices):
        CONTRACT = 'contract', _('Договор')
        ESTIMATE = 'estimate', _('Смета')
        INVOICE = 'invoice', _('Счет')
        RECEIPT = 'receipt', _('Чек')
        PHOTO = 'photo', _('Фотография')
        OTHER = 'other', _('Другое')
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_('Проект'),
        related_name='documents'
    )
    name = models.CharField(_('Название документа'), max_length=200)
    document_type = models.CharField(
        _('Тип документа'),
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.OTHER
    )
    file = models.FileField(_('Файл'), upload_to='project_documents/')
    description = models.TextField(_('Описание'), blank=True)
    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Загрузил'),
        related_name='uploaded_documents'
    )
    file_size = models.PositiveIntegerField(_('Размер файла'), blank=True, null=True)
    created_at = models.DateTimeField(_('Загружен'), auto_now_add=True)

    class Meta:
        verbose_name = _('Документ проекта')
        verbose_name_plural = _('Документы проекта')
        db_table = 'project_documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class ProjectEstimate(models.Model):
    """Смета проекта"""
    
    class EstimateType(models.TextChoices):
        SIMPLE = 'simple', _('Простая смета')
        DETAILED = 'detailed', _('Детализированная смета')
        TEMPLATE = 'template', _('Смета по шаблону')
        IMPORTED = 'imported', _('Импортированная смета')
    
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_('Проект'),
        related_name='estimate'
    )
    estimate_type = models.CharField(
        _('Тип сметы'),
        max_length=20,
        choices=EstimateType.choices,
        default=EstimateType.SIMPLE
    )
    name = models.CharField(_('Название сметы'), max_length=200, blank=True)
    description = models.TextField(_('Описание'), blank=True)
    
    # Суммы
    total_amount = models.DecimalField(
        _('Общая сумма сметы'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    spent_amount = models.DecimalField(
        _('Потрачено'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Детализированные суммы
    labor_amount = models.DecimalField(
        _('Стоимость труда'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    material_amount = models.DecimalField(
        _('Стоимость материалов'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    equipment_amount = models.DecimalField(
        _('Стоимость оборудования'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Параметры расчета
    region_factor = models.DecimalField(
        _('Региональный коэффициент'),
        max_digits=3,
        decimal_places=2,
        default=Decimal('1.00')
    )
    overhead_percent = models.DecimalField(
        _('Накладные расходы (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('15.00')
    )
    profit_percent = models.DecimalField(
        _('Прибыль (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00')
    )
    
    # Статус и версии
    version = models.PositiveIntegerField(_('Версия'), default=1)
    is_approved = models.BooleanField(_('Утверждена'), default=False)
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        verbose_name=_('Утвердил'),
        related_name='approved_estimates',
        null=True,
        blank=True
    )
    approved_at = models.DateTimeField(_('Дата утверждения'), blank=True, null=True)
    
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Создал'),
        related_name='created_estimates'
    )
    created_at = models.DateTimeField(_('Создана'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлена'), auto_now=True)
    is_active = models.BooleanField(_('Активна'), default=True)

    class Meta:
        verbose_name = _('Смета проекта')
        verbose_name_plural = _('Сметы проектов')
        db_table = 'project_estimates'

    def __str__(self):
        return f"Смета проекта {self.project.name}"

    @property
    def remaining_amount(self):
        """Оставшаяся сумма"""
        return self.total_amount - self.spent_amount

    @property
    def utilization_percent(self):
        """Процент использования сметы"""
        if self.total_amount > 0:
            return (self.spent_amount / self.total_amount * 100)
        return 0
    
    @property
    def overhead_amount(self):
        """Сумма накладных расходов"""
        base_amount = self.labor_amount + self.material_amount + self.equipment_amount
        return (base_amount * self.overhead_percent / 100).quantize(Decimal('0.01'))
    
    @property
    def profit_amount(self):
        """Сумма прибыли"""
        base_amount = self.labor_amount + self.material_amount + self.equipment_amount + self.overhead_amount
        return (base_amount * self.profit_percent / 100).quantize(Decimal('0.01'))
    
    @property
    def calculated_total(self):
        """Рассчитанная общая сумма"""
        return (self.labor_amount + self.material_amount + self.equipment_amount + 
                self.overhead_amount + self.profit_amount).quantize(Decimal('0.01'))

    def update_spent_amount(self):
        """Обновить потраченную сумму на основе одобренных расходов"""
        from kanban.models import ExpenseItem
        
        total_spent = ExpenseItem.objects.filter(
            project=self.project,
            status='approved'
        ).aggregate(
            total=models.Sum('estimated_hours')
        )['total'] or Decimal('0.00')
        
        self.spent_amount = total_spent
        self.save(update_fields=['spent_amount'])