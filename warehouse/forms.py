from django import forms
from django.utils.translation import gettext_lazy as _

from .models import WarehouseCategory, WarehouseItem, WarehouseTransaction, ProjectEquipment

class WarehouseCategoryForm(forms.ModelForm):
    """Форма для создания/редактирования категории склада"""
    class Meta:
        model = WarehouseCategory
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Название категории')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Описание категории')}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class WarehouseItemForm(forms.ModelForm):
    """Форма для создания/редактирования товара склада"""
    class Meta:
        model = WarehouseItem
        fields = [
            'name', 'description', 'item_type', 'category', 'unit',
            'current_quantity', 'min_quantity', 'purchase_price', 'selling_price',
            'equipment_photo_before', 'equipment_photo_after', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Название товара')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Описание товара')}),
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('шт, м, кг и т.д.')}),
            'current_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'min_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'equipment_photo_before': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'equipment_photo_after': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_current_quantity(self):
        quantity = self.cleaned_data.get('current_quantity')
        if quantity and quantity < 0:
            raise ValidationError(_('Количество не может быть отрицательным.'))
        return quantity

    def clean_min_quantity(self):
        quantity = self.cleaned_data.get('min_quantity')
        if quantity and quantity < 0:
            raise ValidationError(_('Минимальное количество не может быть отрицательным.'))
        return quantity

    def clean_purchase_price(self):
        price = self.cleaned_data.get('purchase_price')
        if price and price < 0:
            raise ValidationError(_('Цена закупки не может быть отрицательной.'))
        return price

    def clean_selling_price(self):
        price = self.cleaned_data.get('selling_price')
        if price and price < 0:
            raise ValidationError(_('Цена продажи не может быть отрицательной.'))
        return price

class WarehouseTransactionForm(forms.ModelForm):
    """Форма для создания транзакции склада"""
    class Meta:
        model = WarehouseTransaction
        fields = [
            'item', 'transaction_type', 'quantity', 'price', 
            'project', 'description', 'reference_number'
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Описание операции')}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Номер документа')}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError(_('Количество должно быть больше нуля.'))
        return quantity

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price < 0:
            raise ValidationError(_('Цена не может быть отрицательной.'))
        return price

class ProjectEquipmentForm(forms.ModelForm):
    """Форма для добавления оборудования к проекту"""
    class Meta:
        model = ProjectEquipment
        fields = [
            'item', 'quantity_used', 'start_date', 'end_date',
            'condition_before', 'condition_after', 'notes'
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity_used': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'condition_before': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Состояние до использования')}),
            'condition_after': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Состояние после использования')}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Примечания')}),
        }

    def clean_quantity_used(self):
        quantity = self.cleaned_data.get('quantity_used')
        if quantity and quantity <= 0:
            raise ValidationError(_('Количество должно быть больше нуля.'))
        return quantity

class WarehouseSearchForm(forms.Form):
    """Форма поиска товаров на складе"""
    search_query = forms.CharField(
        label=_('Поиск'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Название товара')})
    )
    item_type = forms.ChoiceField(
        label=_('Тип товара'),
        choices=[('', _('Все типы'))] + WarehouseItem.ITEM_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        label=_('Категория'),
        queryset=WarehouseCategory.objects.filter(is_active=True),
        required=False,
        empty_label=_('Все категории'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    low_stock_only = forms.BooleanField(
        label=_('Только товары с низким остатком'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
