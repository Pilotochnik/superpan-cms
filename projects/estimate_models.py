from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class EstimateCategory(models.Model):
    """Категории сметных работ"""
    
    name = models.CharField(_('Название категории'), max_length=200, unique=True)
    code = models.CharField(_('Код категории'), max_length=20, unique=True)
    description = models.TextField(_('Описание'), blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        verbose_name=_('Родительская категория'),
        related_name='children',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(_('Активна'), default=True)
    created_at = models.DateTimeField(_('Создана'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Категория сметных работ')
        verbose_name_plural = _('Категории сметных работ')
        db_table = 'estimate_categories'
        ordering = ['code', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class EstimateUnit(models.Model):
    """Единицы измерения для сметных работ"""
    
    name = models.CharField(_('Название'), max_length=50, unique=True)
    short_name = models.CharField(_('Краткое название'), max_length=10, unique=True)
    description = models.TextField(_('Описание'), blank=True)
    is_active = models.BooleanField(_('Активна'), default=True)
    
    class Meta:
        verbose_name = _('Единица измерения')
        verbose_name_plural = _('Единицы измерения')
        db_table = 'estimate_units'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.short_name})"


class EstimateRate(models.Model):
    """Справочник расценок"""
    
    code = models.CharField(_('Код расценки'), max_length=50, unique=True)
    name = models.CharField(_('Название работы'), max_length=500)
    description = models.TextField(_('Описание'), blank=True)
    category = models.ForeignKey(
        EstimateCategory,
        on_delete=models.CASCADE,
        verbose_name=_('Категория'),
        related_name='rates'
    )
    unit = models.ForeignKey(
        EstimateUnit,
        on_delete=models.CASCADE,
        verbose_name=_('Единица измерения'),
        related_name='rates'
    )
    
    # Стоимость
    base_price = models.DecimalField(
        _('Базовая цена'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    labor_cost = models.DecimalField(
        _('Стоимость труда'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    material_cost = models.DecimalField(
        _('Стоимость материалов'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    equipment_cost = models.DecimalField(
        _('Стоимость оборудования'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Нормы времени
    labor_hours = models.DecimalField(
        _('Трудозатраты (часы)'),
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Дополнительные параметры
    complexity_factor = models.DecimalField(
        _('Коэффициент сложности'),
        max_digits=3,
        decimal_places=2,
        default=Decimal('1.00')
    )
    region_factor = models.DecimalField(
        _('Региональный коэффициент'),
        max_digits=3,
        decimal_places=2,
        default=Decimal('1.00')
    )
    
    is_active = models.BooleanField(_('Активна'), default=True)
    created_at = models.DateTimeField(_('Создана'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлена'), auto_now=True)
    
    class Meta:
        verbose_name = _('Расценка')
        verbose_name_plural = _('Расценки')
        db_table = 'estimate_rates'
        ordering = ['code', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def total_cost(self):
        """Общая стоимость расценки"""
        return self.labor_cost + self.material_cost + self.equipment_cost
    
    def calculate_price(self, quantity=1, region_factor=None):
        """Рассчитать стоимость для заданного количества"""
        factor = region_factor or self.region_factor
        return (self.base_price * self.complexity_factor * factor * Decimal(str(quantity))).quantize(Decimal('0.01'))


class EstimateTemplate(models.Model):
    """Шаблоны смет"""
    
    name = models.CharField(_('Название шаблона'), max_length=200)
    description = models.TextField(_('Описание'), blank=True)
    category = models.ForeignKey(
        EstimateCategory,
        on_delete=models.CASCADE,
        verbose_name=_('Категория'),
        related_name='templates'
    )
    is_public = models.BooleanField(_('Публичный'), default=False)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Создал'),
        related_name='created_templates'
    )
    created_at = models.DateTimeField(_('Создана'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлена'), auto_now=True)
    
    class Meta:
        verbose_name = _('Шаблон сметы')
        verbose_name_plural = _('Шаблоны смет')
        db_table = 'estimate_templates'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class EstimateTemplateItem(models.Model):
    """Позиции шаблона сметы"""
    
    template = models.ForeignKey(
        EstimateTemplate,
        on_delete=models.CASCADE,
        verbose_name=_('Шаблон'),
        related_name='items'
    )
    rate = models.ForeignKey(
        EstimateRate,
        on_delete=models.CASCADE,
        verbose_name=_('Расценка'),
        related_name='template_items'
    )
    quantity = models.DecimalField(
        _('Количество'),
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )
    position = models.PositiveIntegerField(_('Позиция'), default=0)
    
    class Meta:
        verbose_name = _('Позиция шаблона')
        verbose_name_plural = _('Позиции шаблона')
        db_table = 'estimate_template_items'
        ordering = ['position']
    
    def __str__(self):
        return f"{self.template.name} - {self.rate.name}"


class ProjectEstimateItem(models.Model):
    """Позиции сметы проекта"""
    
    estimate = models.ForeignKey(
        'ProjectEstimate',
        on_delete=models.CASCADE,
        verbose_name=_('Смета'),
        related_name='items'
    )
    rate = models.ForeignKey(
        EstimateRate,
        on_delete=models.CASCADE,
        verbose_name=_('Расценка'),
        related_name='estimate_items'
    )
    quantity = models.DecimalField(
        _('Количество'),
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )
    unit_price = models.DecimalField(
        _('Цена за единицу'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    total_price = models.DecimalField(
        _('Общая стоимость'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    position = models.PositiveIntegerField(_('Позиция'), default=0)
    notes = models.TextField(_('Примечания'), blank=True)
    
    # Дополнительные параметры
    region_factor = models.DecimalField(
        _('Региональный коэффициент'),
        max_digits=3,
        decimal_places=2,
        default=Decimal('1.00')
    )
    complexity_factor = models.DecimalField(
        _('Коэффициент сложности'),
        max_digits=3,
        decimal_places=2,
        default=Decimal('1.00')
    )
    
    created_at = models.DateTimeField(_('Создана'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлена'), auto_now=True)
    
    class Meta:
        verbose_name = _('Позиция сметы')
        verbose_name_plural = _('Позиции сметы')
        db_table = 'project_estimate_items'
        ordering = ['position']
    
    def __str__(self):
        return f"{self.estimate.project.name} - {self.rate.name}"
    
    def save(self, *args, **kwargs):
        """Автоматический расчет общей стоимости"""
        if not self.unit_price:
            self.unit_price = self.rate.calculate_price(
                quantity=1,
                region_factor=self.region_factor
            ) * self.complexity_factor
        
        self.total_price = (self.unit_price * self.quantity).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)


class EstimateImport(models.Model):
    """Импорт смет из внешних источников"""
    
    class ImportSource(models.TextChoices):
        EXCEL = 'excel', _('Excel файл')
        GRAND_SMETA = 'grand_smeta', _('ГрандСмета')
        SMETA_RU = 'smeta_ru', _('Смета.ру')
        RIK = 'rik', _('РИК')
        ARPS = 'arps', _('АРПС')
        OTHER = 'other', _('Другое')
    
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        verbose_name=_('Проект'),
        related_name='estimate_imports'
    )
    source = models.CharField(
        _('Источник'),
        max_length=20,
        choices=ImportSource.choices,
        default=ImportSource.EXCEL
    )
    file_name = models.CharField(_('Имя файла'), max_length=255)
    file_path = models.CharField(_('Путь к файлу'), max_length=500)
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=[
            ('pending', _('Ожидает')),
            ('processing', _('Обрабатывается')),
            ('completed', _('Завершен')),
            ('failed', _('Ошибка')),
        ],
        default='pending'
    )
    imported_items = models.PositiveIntegerField(_('Импортировано позиций'), default=0)
    errors = models.TextField(_('Ошибки'), blank=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Импортировал'),
        related_name='estimate_imports'
    )
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Завершен'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Импорт сметы')
        verbose_name_plural = _('Импорты смет')
        db_table = 'estimate_imports'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Импорт {self.file_name} для {self.project.name}"


class EstimateExport(models.Model):
    """Экспорт смет в различные форматы"""
    
    class ExportFormat(models.TextChoices):
        EXCEL = 'excel', _('Excel файл')
        PDF = 'pdf', _('PDF документ')
        WORD = 'word', _('Word документ')
        XML = 'xml', _('XML файл')
        JSON = 'json', _('JSON файл')
    
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        verbose_name=_('Проект'),
        related_name='estimate_exports'
    )
    format = models.CharField(
        _('Формат'),
        max_length=20,
        choices=ExportFormat.choices,
        default=ExportFormat.EXCEL
    )
    file_name = models.CharField(_('Имя файла'), max_length=255)
    file_path = models.CharField(_('Путь к файлу'), max_length=500)
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=[
            ('pending', _('Ожидает')),
            ('processing', _('Обрабатывается')),
            ('completed', _('Завершен')),
            ('failed', _('Ошибка')),
        ],
        default='pending'
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('Экспортировал'),
        related_name='estimate_exports'
    )
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Завершен'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Экспорт сметы')
        verbose_name_plural = _('Экспорты смет')
        db_table = 'estimate_exports'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Экспорт {self.file_name} для {self.project.name}"
