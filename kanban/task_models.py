from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class TaskCategory(models.Model):
    """Категории задач"""
    
    name = models.CharField(_('Название категории'), max_length=100, unique=True)
    description = models.TextField(_('Описание'), blank=True)
    color = models.CharField(_('Цвет'), max_length=7, default='#007bff', help_text=_('HEX код цвета'))
    icon = models.CharField(_('Иконка'), max_length=50, default='bi-list-task', help_text=_('Bootstrap Icons класс'))
    is_active = models.BooleanField(_('Активна'), default=True)
    created_at = models.DateTimeField(_('Создана'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Категория задач')
        verbose_name_plural = _('Категории задач')
        db_table = 'task_categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TaskPriority(models.Model):
    """Приоритеты задач"""
    
    name = models.CharField(_('Название'), max_length=50, unique=True)
    level = models.PositiveIntegerField(_('Уровень'), unique=True, help_text=_('Чем меньше число, тем выше приоритет'))
    color = models.CharField(_('Цвет'), max_length=7, default='#6c757d')
    icon = models.CharField(_('Иконка'), max_length=50, default='bi-circle')
    is_active = models.BooleanField(_('Активен'), default=True)
    
    class Meta:
        verbose_name = _('Приоритет задач')
        verbose_name_plural = _('Приоритеты задач')
        db_table = 'task_priorities'
        ordering = ['level']
    
    def __str__(self):
        return self.name


class TaskStatus(models.Model):
    """Статусы задач"""
    
    name = models.CharField(_('Название'), max_length=100, unique=True)
    description = models.TextField(_('Описание'), blank=True)
    color = models.CharField(_('Цвет'), max_length=7, default='#6c757d')
    icon = models.CharField(_('Иконка'), max_length=50, default='bi-circle')
    is_final = models.BooleanField(_('Финальный статус'), default=False, help_text=_('Задача завершена'))
    is_active = models.BooleanField(_('Активен'), default=True)
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    
    class Meta:
        verbose_name = _('Статус задач')
        verbose_name_plural = _('Статусы задач')
        db_table = 'task_statuses'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class ProjectTask(models.Model):
    """Задача проекта"""
    
    class TaskType(models.TextChoices):
        PURCHASE = 'purchase', _('Закупка')
        WORK = 'work', _('Работа')
        DELIVERY = 'delivery', _('Поставка')
        INSTALLATION = 'installation', _('Монтаж')
        CONTROL = 'control', _('Контроль')
        DOCUMENTATION = 'documentation', _('Документация')
        OTHER = 'other', _('Прочее')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        verbose_name=_('Проект'),
        related_name='tasks'
    )
    category = models.ForeignKey(
        TaskCategory,
        on_delete=models.SET_NULL,
        verbose_name=_('Категория'),
        related_name='tasks',
        null=True,
        blank=True
    )
    priority = models.ForeignKey(
        TaskPriority,
        on_delete=models.SET_NULL,
        verbose_name=_('Приоритет'),
        related_name='tasks',
        null=True,
        blank=True
    )
    status = models.ForeignKey(
        TaskStatus,
        on_delete=models.SET_NULL,
        verbose_name=_('Статус'),
        related_name='tasks',
        null=True,
        blank=True
    )
    
    title = models.CharField(_('Название задачи'), max_length=200)
    description = models.TextField(_('Описание'), blank=True)
    task_type = models.CharField(
        _('Тип задачи'),
        max_length=20,
        choices=TaskType.choices,
        default=TaskType.OTHER
    )
    
    # Назначение и ответственные
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Создал'),
        related_name='created_tasks'
    )
    assigned_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        verbose_name=_('Назначен'),
        related_name='assigned_tasks',
        null=True,
        blank=True
    )
    reviewed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        verbose_name=_('Проверил'),
        related_name='reviewed_tasks',
        null=True,
        blank=True
    )
    
    # Сроки
    due_date = models.DateTimeField(_('Срок выполнения'), blank=True, null=True)
    started_at = models.DateTimeField(_('Начато'), blank=True, null=True)
    completed_at = models.DateTimeField(_('Завершено'), blank=True, null=True)
    
    # Прогресс
    progress_percent = models.PositiveIntegerField(
        _('Прогресс (%)'),
        default=0,
        validators=[MinValueValidator(0)]
    )
    estimated_hours = models.DecimalField(
        _('Планируемые часы'),
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00')
    )
    actual_hours = models.DecimalField(
        _('Фактические часы'),
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Финансы (опционально)
    budget = models.DecimalField(
        _('Бюджет'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    actual_cost = models.DecimalField(
        _('Фактическая стоимость'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Позиция в канбан-доске
    column = models.ForeignKey(
        'KanbanColumn',
        on_delete=models.CASCADE,
        verbose_name=_('Колонка'),
        related_name='tasks',
        null=True,
        blank=True
    )
    position = models.PositiveIntegerField(_('Позиция в колонке'), default=0)
    
    # Дополнительные поля
    tags = models.CharField(_('Теги'), max_length=500, blank=True, help_text=_('Через запятую'))
    is_urgent = models.BooleanField(_('Срочная'), default=False)
    is_blocked = models.BooleanField(_('Заблокирована'), default=False)
    block_reason = models.TextField(_('Причина блокировки'), blank=True)
    
    # Файлы и документы
    attachment = models.FileField(
        _('Вложение'),
        upload_to='task_attachments/',
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(_('Создана'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлена'), auto_now=True)
    
    class Meta:
        verbose_name = _('Задача проекта')
        verbose_name_plural = _('Задачи проектов')
        db_table = 'project_tasks'
        ordering = ['column__position', 'position', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.project.name}"
    
    @property
    def is_overdue(self):
        """Просрочена ли задача"""
        if not self.due_date or self.status and self.status.is_final:
            return False
        from django.utils import timezone
        return self.due_date < timezone.now()
    
    @property
    def days_until_due(self):
        """Дней до срока"""
        if not self.due_date:
            return None
        from django.utils import timezone
        delta = self.due_date - timezone.now()
        return delta.days
    
    def can_user_edit(self, user):
        """Может ли пользователь редактировать задачу"""
        if user.is_superuser_role():
            return True
        if self.created_by == user:
            return True
        if self.assigned_to == user:
            return True
        if self.project.foreman == user:
            return True
        return False
    
    def can_user_assign(self, user):
        """Может ли пользователь назначать задачу"""
        if user.is_superuser_role():
            return True
        if self.project.created_by == user:
            return True
        if self.project.foreman == user:
            return True
        return False


class TaskComment(models.Model):
    """Комментарии к задачам"""
    
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        verbose_name=_('Задача'),
        related_name='comments'
    )
    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Автор'),
        related_name='task_comments'
    )
    text = models.TextField(_('Комментарий'))
    is_internal = models.BooleanField(_('Внутренний комментарий'), default=False)
    is_system = models.BooleanField(_('Системный комментарий'), default=False)
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлен'), auto_now=True)
    
    class Meta:
        verbose_name = _('Комментарий к задаче')
        verbose_name_plural = _('Комментарии к задачам')
        db_table = 'task_comments'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Комментарий к {self.task.title}"


class TaskAttachment(models.Model):
    """Вложения к задачам"""
    
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        verbose_name=_('Задача'),
        related_name='attachments'
    )
    file = models.FileField(_('Файл'), upload_to='task_attachments/')
    name = models.CharField(_('Название'), max_length=200)
    description = models.TextField(_('Описание'), blank=True)
    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Загрузил'),
        related_name='uploaded_task_attachments'
    )
    file_size = models.PositiveIntegerField(_('Размер файла'), blank=True, null=True)
    created_at = models.DateTimeField(_('Загружен'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Вложение к задаче')
        verbose_name_plural = _('Вложения к задачам')
        db_table = 'task_attachments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.task.title} - {self.name}"
    
    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class TaskHistory(models.Model):
    """История изменений задач"""
    
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        verbose_name=_('Задача'),
        related_name='history'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь'),
        related_name='task_history'
    )
    action = models.CharField(_('Действие'), max_length=50)
    old_value = models.TextField(_('Старое значение'), blank=True)
    new_value = models.TextField(_('Новое значение'), blank=True)
    field_name = models.CharField(_('Поле'), max_length=50, blank=True)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('История изменений задачи')
        verbose_name_plural = _('История изменений задач')
        db_table = 'task_history'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.task.title} - {self.action}"


class TaskDependency(models.Model):
    """Зависимости между задачами"""
    
    class DependencyType(models.TextChoices):
        BLOCKS = 'blocks', _('Блокирует')
        DEPENDS_ON = 'depends_on', _('Зависит от')
        RELATED = 'related', _('Связана с')
    
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        verbose_name=_('Задача'),
        related_name='dependencies'
    )
    depends_on = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        verbose_name=_('Зависит от'),
        related_name='dependents'
    )
    dependency_type = models.CharField(
        _('Тип зависимости'),
        max_length=20,
        choices=DependencyType.choices,
        default=DependencyType.DEPENDS_ON
    )
    created_at = models.DateTimeField(_('Создана'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Зависимость задач')
        verbose_name_plural = _('Зависимости задач')
        db_table = 'task_dependencies'
        unique_together = ['task', 'depends_on']
    
    def __str__(self):
        return f"{self.task.title} {self.get_dependency_type_display()} {self.depends_on.title}"
