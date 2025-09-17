from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class ExpenseCategory(models.Model):
    """Категории расходов"""
    
    name = models.CharField(_('Название категории'), max_length=100, unique=True)
    description = models.TextField(_('Описание'), blank=True)
    color = models.CharField(_('Цвет'), max_length=7, default='#007bff', help_text=_('HEX код цвета'))
    is_active = models.BooleanField(_('Активна'), default=True)
    created_at = models.DateTimeField(_('Создана'), auto_now_add=True)

    class Meta:
        verbose_name = _('Категория расходов')
        verbose_name_plural = _('Категории расходов')
        db_table = 'expense_categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class KanbanBoard(models.Model):
    """Канбан-доска проекта"""
    
    project = models.OneToOneField(
        'projects.Project',
        on_delete=models.CASCADE,
        verbose_name=_('Проект'),
        related_name='kanban_board'
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Создал'),
        related_name='created_boards'
    )
    created_at = models.DateTimeField(_('Создана'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлена'), auto_now=True)

    class Meta:
        verbose_name = _('Канбан-доска')
        verbose_name_plural = _('Канбан-доски')
        db_table = 'kanban_boards'

    def __str__(self):
        return f"Доска проекта {self.project.name}"


class KanbanColumn(models.Model):
    """Колонки канбан-доски"""
    
    class ColumnType(models.TextChoices):
        BACKLOG = 'backlog', _('Бэклог')
        TODO = 'todo', _('К выполнению')
        IN_PROGRESS = 'in_progress', _('В работе')
        REVIEW = 'review', _('На проверке')
        DONE = 'done', _('Выполнено')
        CANCELLED = 'cancelled', _('Отменено')
    
    board = models.ForeignKey(
        KanbanBoard,
        on_delete=models.CASCADE,
        verbose_name=_('Доска'),
        related_name='columns'
    )
    name = models.CharField(_('Название колонки'), max_length=100)
    column_type = models.CharField(
        _('Тип колонки'),
        max_length=20,
        choices=ColumnType.choices,
        default=ColumnType.TODO
    )
    position = models.PositiveIntegerField(_('Позиция'), default=0)
    color = models.CharField(_('Цвет'), max_length=7, default='#f8f9fa')
    is_active = models.BooleanField(_('Активна'), default=True)

    class Meta:
        verbose_name = _('Колонка канбан-доски')
        verbose_name_plural = _('Колонки канбан-доски')
        db_table = 'kanban_columns'
        ordering = ['position']
        unique_together = ['board', 'position']

    def __str__(self):
        return f"{self.board.project.name} - {self.name}"


class ConstructionStage(models.Model):
    """Этапы строительства"""
    
    name = models.CharField(_('Название этапа'), max_length=200)
    description = models.TextField(_('Описание'), blank=True)
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    color = models.CharField(_('Цвет'), max_length=7, default='#007bff')
    is_active = models.BooleanField(_('Активен'), default=True)
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Этап строительства')
        verbose_name_plural = _('Этапы строительства')
        db_table = 'construction_stages'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class ExpenseItem(models.Model):
    """Элемент задачи (карточка в канбан)"""
    
    class Status(models.TextChoices):
        NEW = 'new', _('Новая')
        TODO = 'todo', _('К выполнению')
        IN_PROGRESS = 'in_progress', _('В работе')
        REVIEW = 'review', _('На проверке')
        DONE = 'done', _('Выполнена')
        CANCELLED = 'cancelled', _('Отменена')
    
    class TaskType(models.TextChoices):
        PURCHASE = 'purchase', _('Закупка')
        WORK = 'work', _('Работа')
        DELIVERY = 'delivery', _('Поставка')
        INSTALLATION = 'installation', _('Монтаж')
        CONTROL = 'control', _('Контроль')
        DOCUMENTATION = 'documentation', _('Документация')
        MESSAGE = 'message', _('Сообщение')
        PHOTO_REPORT = 'photo_report', _('Фотоотчет')
        OTHER = 'other', _('Прочее')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        verbose_name=_('Проект'),
        related_name='expense_items'
    )
    stage = models.ForeignKey(
        ConstructionStage,
        on_delete=models.SET_NULL,
        verbose_name=_('Этап строительства'),
        related_name='tasks',
        null=True,
        blank=True
    )
    column = models.ForeignKey(
        KanbanColumn,
        on_delete=models.CASCADE,
        verbose_name=_('Колонка'),
        related_name='items'
    )
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        verbose_name=_('Категория'),
        related_name='expense_items',
        null=True,
        blank=True
    )
    
    title = models.CharField(_('Название'), max_length=200)
    description = models.TextField(_('Описание'), blank=True)
    task_type = models.CharField(
        _('Тип задачи'),
        max_length=20,
        choices=TaskType.choices,
        default=TaskType.OTHER
    )
    estimated_hours = models.DecimalField(
        _('Планируемые часы'),
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    amount = models.DecimalField(
        _('Сумма'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )
    
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Создал'),
        related_name='created_expense_items'
    )
    assigned_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        verbose_name=_('Назначен'),
        related_name='assigned_expense_items',
        null=True,
        blank=True
    )
    
    # Дополнительные поля для задач
    due_date = models.DateTimeField(_('Срок выполнения'), blank=True, null=True)
    progress_percent = models.PositiveIntegerField(
        _('Прогресс (%)'),
        default=0,
        validators=[MinValueValidator(0)]
    )
    is_urgent = models.BooleanField(_('Срочная'), default=False)
    tags = models.CharField(_('Теги'), max_length=500, blank=True, help_text=_('Через запятую'))
    
    position = models.PositiveIntegerField(_('Позиция в колонке'), default=0)
    priority = models.CharField(
        _('Приоритет'),
        max_length=10,
        choices=[
            ('low', _('Низкий')),
            ('medium', _('Средний')),
            ('high', _('Высокий')),
        ],
        default='medium'
    )
    
    due_date = models.DateField(_('Срок'), blank=True, null=True)
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        verbose_name=_('Одобрил'),
        related_name='approved_expense_items',
        null=True,
        blank=True
    )
    approved_at = models.DateTimeField(_('Дата одобрения'), blank=True, null=True)
    rejection_reason = models.TextField(_('Причина отклонения'), blank=True)
    
    # Поля для файлов
    receipt_file = models.FileField(
        _('Чек/Счет'),
        upload_to='expense_receipts/',
        blank=True,
        null=True,
        help_text=_('Загрузите чек, счет или другой документ')
    )
    photo_files = models.FileField(
        _('Фотографии'),
        upload_to='expense_photos/',
        blank=True,
        null=True,
        help_text=_('Загрузите фотографии (можно несколько файлов)')
    )
    
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлен'), auto_now=True)

    class Meta:
        verbose_name = _('Задача')
        verbose_name_plural = _('Задачи')
        db_table = 'expense_items'
        ordering = ['column__position', 'position', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Синхронизируем статус с типом колонки
        if self.column:
            self.status = self.column.column_type
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Просрочена ли задача"""
        if not self.due_date or self.status == 'done':
            return False
        from django.utils import timezone
        return self.due_date < timezone.now()
    
    def can_user_change_status(self, user):
        """Проверяет, может ли пользователь менять статус задачи"""
        # Админ может менять статус напрямую
        if user.is_admin_role():
            return True
        
        # Остальные пользователи могут только запрашивать изменение
        return False
    
    def has_pending_status_change(self):
        """Проверяет, есть ли ожидающий утверждения запрос на изменение статуса"""
        return self.status_change_requests.filter(status=StatusChangeRequest.Status.PENDING).exists()
    
    @property
    def pending_status_request(self):
        """Возвращает ожидающий утверждения запрос на изменение статуса"""
        return self.status_change_requests.filter(status=StatusChangeRequest.Status.PENDING).first()


class ExpenseDocument(models.Model):
    """Документы к расходам (чеки, счета и т.д.)"""
    
    expense_item = models.ForeignKey(
        ExpenseItem,
        on_delete=models.CASCADE,
        verbose_name=_('Элемент расхода'),
        related_name='documents'
    )
    name = models.CharField(_('Название документа'), max_length=200)
    file = models.FileField(_('Файл'), upload_to='expense_documents/')
    file_type = models.CharField(
        _('Тип документа'),
        max_length=20,
        choices=[
            ('receipt', _('Чек')),
            ('invoice', _('Счет')),
            ('contract', _('Договор')),
            ('photo', _('Фотография')),
            ('other', _('Другое')),
        ],
        default='receipt'
    )
    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Загрузил'),
        related_name='uploaded_expense_documents'
    )
    file_size = models.PositiveIntegerField(_('Размер файла'), blank=True, null=True)
    created_at = models.DateTimeField(_('Загружен'), auto_now_add=True)

    class Meta:
        verbose_name = _('Документ расхода')
        verbose_name_plural = _('Документы расходов')
        db_table = 'expense_documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.expense_item.title} - {self.name}"

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class ExpenseComment(models.Model):
    """Комментарии к задачам"""
    
    expense_item = models.ForeignKey(
        ExpenseItem,
        on_delete=models.CASCADE,
        verbose_name=_('Задача'),
        related_name='comments'
    )
    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Автор'),
        related_name='expense_comments'
    )
    text = models.TextField(_('Комментарий'))
    is_internal = models.BooleanField(_('Внутренний комментарий'), default=False)
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлен'), auto_now=True)

    class Meta:
        verbose_name = _('Комментарий к задаче')
        verbose_name_plural = _('Комментарии к задачам')
        db_table = 'expense_comments'
        ordering = ['created_at']

    def __str__(self):
        return f"Комментарий к {self.expense_item.title}"


class ExpenseCommentAttachment(models.Model):
    """Вложения к комментариям задач"""
    
    comment = models.ForeignKey(
        ExpenseComment,
        on_delete=models.CASCADE,
        verbose_name=_('Комментарий'),
        related_name='attachments'
    )
    file = models.FileField(
        _('Файл'),
        upload_to='task_comments/attachments/',
        help_text=_('Загрузите фото, видео или документ')
    )
    file_name = models.CharField(_('Название файла'), max_length=255)
    file_size = models.PositiveIntegerField(_('Размер файла'), blank=True, null=True)
    file_type = models.CharField(
        _('Тип файла'),
        max_length=50,
        choices=[
            ('image', _('Изображение')),
            ('video', _('Видео')),
            ('document', _('Документ')),
            ('other', _('Другое')),
        ],
        default='other'
    )
    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Загрузил'),
        related_name='uploaded_comment_attachments'
    )
    created_at = models.DateTimeField(_('Загружен'), auto_now_add=True)

    class Meta:
        verbose_name = _('Вложение к комментарию')
        verbose_name_plural = _('Вложения к комментариям')
        db_table = 'expense_comment_attachments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.comment.expense_item.title} - {self.file_name}"

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        if self.file and not self.file_name:
            self.file_name = self.file.name
        super().save(*args, **kwargs)

    @property
    def is_image(self):
        """Проверка, является ли файл изображением"""
        return self.file_type == 'image'

    @property
    def is_video(self):
        """Проверка, является ли файл видео"""
        return self.file_type == 'video'

    @property
    def is_document(self):
        """Проверка, является ли файл документом"""
        return self.file_type == 'document'


class ExpenseHistory(models.Model):
    """История изменений расходов"""
    
    expense_item = models.ForeignKey(
        ExpenseItem,
        on_delete=models.CASCADE,
        verbose_name=_('Элемент расхода'),
        related_name='history'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь'),
        related_name='expense_history'
    )
    action = models.CharField(_('Действие'), max_length=50)
    old_value = models.TextField(_('Старое значение'), blank=True)
    new_value = models.TextField(_('Новое значение'), blank=True)
    field_name = models.CharField(_('Поле'), max_length=50, blank=True)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)

    class Meta:
        verbose_name = _('История изменений расхода')
        verbose_name_plural = _('История изменений расходов')
        db_table = 'expense_history'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.expense_item.title} - {self.action}"


class StatusChangeRequest(models.Model):
    """Запросы на изменение статуса задач (ожидают утверждения)"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Ожидает утверждения')
        APPROVED = 'approved', _('Утверждено')
        REJECTED = 'rejected', _('Отклонено')
    
    expense_item = models.ForeignKey(
        ExpenseItem,
        on_delete=models.CASCADE,
        verbose_name=_('Задача'),
        related_name='status_change_requests'
    )
    requested_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Запросил'),
        related_name='requested_status_changes'
    )
    old_status = models.CharField(
        _('Старый статус'),
        max_length=20,
        choices=ExpenseItem.Status.choices
    )
    new_status = models.CharField(
        _('Новый статус'),
        max_length=20,
        choices=ExpenseItem.Status.choices
    )
    reason = models.TextField(_('Причина изменения'), blank=True)
    status = models.CharField(
        _('Статус запроса'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        verbose_name=_('Утвердил'),
        related_name='approved_status_changes',
        null=True,
        blank=True
    )
    approved_at = models.DateTimeField(_('Дата утверждения'), null=True, blank=True)
    rejection_reason = models.TextField(_('Причина отклонения'), blank=True)
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)

    class Meta:
        verbose_name = _('Запрос на изменение статуса')
        verbose_name_plural = _('Запросы на изменение статуса')
        db_table = 'status_change_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.expense_item.title}: {self.get_old_status_display()} → {self.get_new_status_display()}"
    
    @property
    def is_pending(self):
        """Проверяет, ожидает ли запрос утверждения"""
        return self.status == self.Status.PENDING
    
    @property
    def is_approved(self):
        """Проверяет, утвержден ли запрос"""
        return self.status == self.Status.APPROVED
    
    @property
    def is_rejected(self):
        """Проверяет, отклонен ли запрос"""
        return self.status == self.Status.REJECTED
