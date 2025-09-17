from django import forms
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from .estimate_models import (
    EstimateCategory, EstimateUnit, EstimateRate, EstimateTemplate,
    ProjectEstimateItem, EstimateImport, EstimateExport
)
from .models import ProjectEstimate


class EstimateCategoryForm(forms.ModelForm):
    """Форма для создания/редактирования категорий сметных работ"""
    
    class Meta:
        model = EstimateCategory
        fields = ['name', 'code', 'description', 'parent', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название категории'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Код категории'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание категории'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class EstimateUnitForm(forms.ModelForm):
    """Форма для создания/редактирования единиц измерения"""
    
    class Meta:
        model = EstimateUnit
        fields = ['name', 'short_name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название единицы измерения'
            }),
            'short_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Краткое название'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Описание единицы измерения'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class EstimateRateForm(forms.ModelForm):
    """Форма для создания/редактирования расценок"""
    
    class Meta:
        model = EstimateRate
        fields = [
            'code', 'name', 'description', 'category', 'unit',
            'base_price', 'labor_cost', 'material_cost', 'equipment_cost',
            'labor_hours', 'complexity_factor', 'region_factor', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Код расценки'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название работы'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание работы'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select'
            }),
            'base_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'labor_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'material_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'equipment_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'labor_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'complexity_factor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'max': '5.00'
            }),
            'region_factor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'max': '3.00'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class ProjectEstimateForm(forms.ModelForm):
    """Форма для создания/редактирования сметы проекта"""
    
    class Meta:
        model = ProjectEstimate
        fields = [
            'estimate_type', 'name', 'description',
            'total_amount', 'region_factor', 'overhead_percent', 'profit_percent'
        ]
        widgets = {
            'estimate_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название сметы'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание сметы'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'region_factor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'max': '3.00'
            }),
            'overhead_percent': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'profit_percent': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            })
        }


class ProjectEstimateItemForm(forms.ModelForm):
    """Форма для добавления позиции в смету"""
    
    class Meta:
        model = ProjectEstimateItem
        fields = [
            'rate', 'quantity', 'unit_price', 'region_factor', 
            'complexity_factor', 'notes'
        ]
        widgets = {
            'rate': forms.Select(attrs={
                'class': 'form-select',
                'data-live-search': 'true'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.001'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'region_factor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'max': '3.00'
            }),
            'complexity_factor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'max': '5.00'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Примечания к позиции'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем только активные расценки
        self.fields['rate'].queryset = EstimateRate.objects.filter(is_active=True)
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise forms.ValidationError('Количество должно быть больше 0')
        return quantity


class EstimateTemplateForm(forms.ModelForm):
    """Форма для создания/редактирования шаблона сметы"""
    
    class Meta:
        model = EstimateTemplate
        fields = ['name', 'description', 'category', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название шаблона'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание шаблона'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class EstimateImportForm(forms.ModelForm):
    """Форма для импорта сметы"""
    
    file = forms.FileField(
        label=_('Файл сметы'),
        help_text=_('Поддерживаемые форматы: Excel, АРПС, XML'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.xml,.arps'
        })
    )
    
    class Meta:
        model = EstimateImport
        fields = ['source', 'file']
        widgets = {
            'source': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Проверяем размер файла (максимум 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Размер файла не должен превышать 10MB')
            
            # Проверяем расширение файла
            allowed_extensions = ['.xlsx', '.xls', '.xml', '.arps']
            file_extension = file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError(
                    f'Неподдерживаемый формат файла. '
                    f'Разрешены: {", ".join(allowed_extensions)}'
                )
        
        return file


class EstimateExportForm(forms.Form):
    """Форма для экспорта сметы"""
    
    EXPORT_FORMATS = [
        ('excel', _('Excel файл (.xlsx)')),
        ('pdf', _('PDF документ (.pdf)')),
        ('word', _('Word документ (.docx)')),
        ('xml', _('XML файл (.xml)')),
        ('json', _('JSON файл (.json)'))
    ]
    
    format = forms.ChoiceField(
        label=_('Формат экспорта'),
        choices=EXPORT_FORMATS,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    include_items = forms.BooleanField(
        label=_('Включить позиции сметы'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_calculations = forms.BooleanField(
        label=_('Включить расчеты'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_notes = forms.BooleanField(
        label=_('Включить примечания'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class EstimateSearchForm(forms.Form):
    """Форма поиска расценок"""
    
    search_query = forms.CharField(
        label=_('Поиск'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите код или название работы...'
        })
    )
    
    category = forms.ModelChoiceField(
        label=_('Категория'),
        queryset=EstimateCategory.objects.filter(is_active=True),
        required=False,
        empty_label=_('Все категории'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    unit = forms.ModelChoiceField(
        label=_('Единица измерения'),
        queryset=EstimateUnit.objects.filter(is_active=True),
        required=False,
        empty_label=_('Все единицы'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    price_min = forms.DecimalField(
        label=_('Цена от'),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    
    price_max = forms.DecimalField(
        label=_('Цена до'),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )


class EstimateCalculationForm(forms.Form):
    """Форма для расчета стоимости работ"""
    
    rate_id = forms.IntegerField(
        label=_('ID расценки'),
        widget=forms.HiddenInput()
    )
    
    quantity = forms.DecimalField(
        label=_('Количество'),
        min_value=Decimal('0.001'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'min': '0.001'
        })
    )
    
    region_factor = forms.DecimalField(
        label=_('Региональный коэффициент'),
        min_value=Decimal('0.01'),
        max_value=Decimal('3.00'),
        initial=Decimal('1.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'max': '3.00'
        })
    )
    
    complexity_factor = forms.DecimalField(
        label=_('Коэффициент сложности'),
        min_value=Decimal('0.01'),
        max_value=Decimal('5.00'),
        initial=Decimal('1.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'max': '5.00'
        })
    )
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise forms.ValidationError('Количество должно быть больше 0')
        return quantity
