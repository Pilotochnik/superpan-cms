from django import forms
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from .task_models import (
    TaskCategory, TaskPriority, TaskStatus, ProjectTask, TaskComment
)
from projects.models import Project


class ProjectTaskForm(forms.ModelForm):
    """Форма для создания/редактирования задач"""
    
    class Meta:
        model = ProjectTask
        fields = [
            'title', 'description', 'category', 'priority', 'status',
            'assigned_to', 'task_type', 'due_date', 'estimated_hours',
            'budget', 'tags', 'is_urgent', 'is_blocked', 'block_reason'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название задачи'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Подробное описание задачи'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
            'task_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Теги через запятую'
            }),
            'is_urgent': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_blocked': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'block_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Причина блокировки задачи'
            })
        }
    
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # Фильтруем только активные категории, приоритеты и статусы
        self.fields['category'].queryset = TaskCategory.objects.filter(is_active=True)
        self.fields['priority'].queryset = TaskPriority.objects.filter(is_active=True)
        self.fields['status'].queryset = TaskStatus.objects.filter(is_active=True)
        
        # Фильтруем пользователей проекта
        if project:
            self.fields['assigned_to'].queryset = project.get_team_members().values_list('assigned_to', flat=True)
        else:
            self.fields['assigned_to'].queryset = self.fields['assigned_to'].queryset.none()
    
    def clean_estimated_hours(self):
        hours = self.cleaned_data.get('estimated_hours')
        if hours and hours < 0:
            raise forms.ValidationError('Количество часов не может быть отрицательным')
        return hours
    
    def clean_budget(self):
        budget = self.cleaned_data.get('budget')
        if budget and budget < 0:
            raise forms.ValidationError('Бюджет не может быть отрицательным')
        return budget


class TaskCommentForm(forms.ModelForm):
    """Форма для добавления комментариев к задачам"""
    
    class Meta:
        model = TaskComment
        fields = ['text', 'is_internal']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Добавить комментарий...'
            }),
            'is_internal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].required = True


class TaskSearchForm(forms.Form):
    """Форма поиска задач"""
    
    search_query = forms.CharField(
        label=_('Поиск'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию или описанию...'
        })
    )
    
    category = forms.ModelChoiceField(
        label=_('Категория'),
        queryset=TaskCategory.objects.filter(is_active=True),
        required=False,
        empty_label=_('Все категории'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    priority = forms.ModelChoiceField(
        label=_('Приоритет'),
        queryset=TaskPriority.objects.filter(is_active=True),
        required=False,
        empty_label=_('Все приоритеты'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = forms.ModelChoiceField(
        label=_('Статус'),
        queryset=TaskStatus.objects.filter(is_active=True),
        required=False,
        empty_label=_('Все статусы'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    assigned_to = forms.ModelChoiceField(
        label=_('Исполнитель'),
        queryset=None,  # Будет установлен в представлении
        required=False,
        empty_label=_('Все исполнители'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    task_type = forms.ChoiceField(
        label=_('Тип задачи'),
        choices=[('', _('Все типы'))] + ProjectTask.TaskType.choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_urgent = forms.BooleanField(
        label=_('Только срочные'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    is_overdue = forms.BooleanField(
        label=_('Только просроченные'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class TaskFilterForm(forms.Form):
    """Форма фильтрации задач для канбан-доски"""
    
    category = forms.ModelChoiceField(
        label=_('Категория'),
        queryset=TaskCategory.objects.filter(is_active=True),
        required=False,
        empty_label=_('Все категории'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'this.form.submit()'
        })
    )
    
    priority = forms.ModelChoiceField(
        label=_('Приоритет'),
        queryset=TaskPriority.objects.filter(is_active=True),
        required=False,
        empty_label=_('Все приоритеты'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'this.form.submit()'
        })
    )
    
    assigned_to = forms.ModelChoiceField(
        label=_('Исполнитель'),
        queryset=None,  # Будет установлен в представлении
        required=False,
        empty_label=_('Все исполнители'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'this.form.submit()'
        })
    )
    
    show_archived = forms.BooleanField(
        label=_('Показать завершенные'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'onchange': 'this.form.submit()'
        })
    )


class TaskProgressForm(forms.Form):
    """Форма для обновления прогресса задачи"""
    
    progress_percent = forms.IntegerField(
        label=_('Прогресс (%)'),
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '100'
        })
    )
    
    actual_hours = forms.DecimalField(
        label=_('Фактические часы'),
        min_value=Decimal('0'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.5',
            'min': '0'
        })
    )
    
    comment = forms.CharField(
        label=_('Комментарий'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Описание выполненной работы...'
        })
    )


class TaskAssignmentForm(forms.Form):
    """Форма для назначения задач"""
    
    assigned_to = forms.ModelChoiceField(
        label=_('Назначить'),
        queryset=None,  # Будет установлен в представлении
        required=False,
        empty_label=_('Не назначено'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    due_date = forms.DateTimeField(
        label=_('Срок выполнения'),
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    priority = forms.ModelChoiceField(
        label=_('Приоритет'),
        queryset=TaskPriority.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    comment = forms.CharField(
        label=_('Комментарий к назначению'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Дополнительные инструкции...'
        })
    )
