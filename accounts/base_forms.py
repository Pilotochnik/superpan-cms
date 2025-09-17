"""
Базовые классы форм для проекта SuperPan
"""
from django import forms


class BaseForm(forms.Form):
    """Базовый класс для всех форм"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_bootstrap_classes()
    
    def _add_bootstrap_classes(self):
        """Добавляет Bootstrap классы ко всем полям"""
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.EmailInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.NumberInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.DateTimeInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})


class BaseModelForm(forms.ModelForm):
    """Базовый класс для всех ModelForm"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_bootstrap_classes()
    
    def _add_bootstrap_classes(self):
        """Добавляет Bootstrap классы ко всем полям"""
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.EmailInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.NumberInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.DateTimeInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})


class BaseExpenseForm(BaseModelForm):
    """Базовый класс для форм расходов"""
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError(_('Сумма должна быть больше нуля.'))
        return amount
    
    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError(_('Название обязательно для заполнения.'))
        if len(title) > 200:
            raise forms.ValidationError(_('Название слишком длинное (максимум 200 символов).'))
        return title


class BaseProjectForm(BaseModelForm):
    """Базовый класс для форм проектов"""
    
    def clean_budget(self):
        budget = self.cleaned_data.get('budget')
        if budget and budget <= 0:
            raise forms.ValidationError(_('Бюджет должен быть больше нуля.'))
        return budget
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(_('Дата окончания не может быть раньше даты начала.'))

        return cleaned_data
