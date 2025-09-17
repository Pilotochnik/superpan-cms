from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

class WarehouseCategory(models.Model):
    """Категории товаров на складе"""
    name = models.CharField(_('Название категории'), max_length=100, unique=True)
    description = models.TextField(_('Описание'), blank=True)
    is_active = models.BooleanField(_('Активна'), default=True)
    created_at = models.DateTimeField(_('Создана'), auto_now_add=True)

    class Meta:
        verbose_name = _('Категория склада')
        verbose_name_plural = _('Категории склада')
        db_table = 'warehouse_categories'
        ordering = ['name']

    def __str__(self):
        return self.name

class WarehouseItem(models.Model):
    """Товары на складе"""
    ITEM_TYPE_CHOICES = [
        ('MATERIAL', _('Материал')),
        ('EQUIPMENT', _('Оборудование')),
    ]
    
    name = models.CharField(_('Название'), max_length=200)
    description = models.TextField(_('Описание'), blank=True)
    item_type = models.CharField(_('Тип товара'), max_length=20, choices=ITEM_TYPE_CHOICES)
    category = models.ForeignKey(WarehouseCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='items', verbose_name=_('Категория'))
    
    # Основные характеристики
    unit = models.CharField(_('Единица измерения'), max_length=20, default='шт')
    current_quantity = models.DecimalField(
        _('Текущее количество'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00')
    )
    min_quantity = models.DecimalField(
        _('Минимальное количество'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00')
    )
    
    # Цены
    purchase_price = models.DecimalField(
        _('Цена закупки'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00')
    )
    selling_price = models.DecimalField(
        _('Цена продажи'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00')
    )
    
    # Для оборудования
    equipment_photo_before = models.ImageField(
        _('Фото оборудования до начала работ'),
        upload_to='warehouse/equipment/before/',
        null=True,
        blank=True
    )
    equipment_photo_after = models.ImageField(
        _('Фото оборудования после завершения работ'),
        upload_to='warehouse/equipment/after/',
        null=True,
        blank=True
    )
    
    # Системные поля
    is_active = models.BooleanField(_('Активен'), default=True)
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлен'), auto_now=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_warehouse_items', verbose_name=_('Создал'))

    class Meta:
        verbose_name = _('Товар склада')
        verbose_name_plural = _('Товары склада')
        db_table = 'warehouse_items'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_item_type_display()})"

    @property
    def is_low_stock(self):
        """Проверка на низкий остаток"""
        return self.current_quantity <= self.min_quantity

class WarehouseTransaction(models.Model):
    """Транзакции склада (приход/расход)"""
    TRANSACTION_TYPE_CHOICES = [
        ('IN', _('Приход')),
        ('OUT', _('Расход')),
        ('TRANSFER', _('Перемещение')),
        ('ADJUSTMENT', _('Корректировка')),
    ]
    
    item = models.ForeignKey(WarehouseItem, on_delete=models.CASCADE, related_name='transactions', verbose_name=_('Товар'))
    transaction_type = models.CharField(_('Тип операции'), max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    quantity = models.DecimalField(
        _('Количество'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    price = models.DecimalField(
        _('Цена'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00')
    )
    total_amount = models.DecimalField(
        _('Общая сумма'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00')
    )
    
    # Связь с проектом (если применимо)
    project = models.ForeignKey('projects.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='warehouse_transactions', verbose_name=_('Проект'))
    
    # Дополнительная информация
    description = models.TextField(_('Описание'), blank=True)
    reference_number = models.CharField(_('Номер документа'), max_length=100, blank=True)
    
    # Системные поля
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_warehouse_transactions', verbose_name=_('Создал'))

    class Meta:
        verbose_name = _('Транзакция склада')
        verbose_name_plural = _('Транзакции склада')
        db_table = 'warehouse_transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.item.name} - {self.quantity} {self.item.unit}"

    def save(self, *args, **kwargs):
        self.total_amount = (self.quantity * self.price).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)
        
        # Обновляем текущее количество товара
        if self.transaction_type == 'IN':
            self.item.current_quantity += self.quantity
        elif self.transaction_type == 'OUT':
            self.item.current_quantity -= self.quantity
        self.item.save()

class ProjectEquipment(models.Model):
    """Оборудование, используемое в проекте"""
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='equipment', verbose_name=_('Проект'))
    item = models.ForeignKey(WarehouseItem, on_delete=models.CASCADE, related_name='project_usage', verbose_name=_('Оборудование'))
    quantity_used = models.DecimalField(
        _('Количество использовано'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    start_date = models.DateTimeField(_('Дата начала использования'), null=True, blank=True)
    end_date = models.DateTimeField(_('Дата окончания использования'), null=True, blank=True)
    condition_before = models.TextField(_('Состояние до использования'), blank=True)
    condition_after = models.TextField(_('Состояние после использования'), blank=True)
    notes = models.TextField(_('Примечания'), blank=True)
    
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_project_equipment', verbose_name=_('Создал'))

    class Meta:
        verbose_name = _('Оборудование проекта')
        verbose_name_plural = _('Оборудование проектов')
        db_table = 'project_equipment'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.name} - {self.item.name}"
