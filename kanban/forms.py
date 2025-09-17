from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from .models import ExpenseItem, ExpenseDocument, ExpenseComment, ExpenseCommentAttachment, ExpenseCategory
from accounts.base_forms import BaseExpenseForm
from constants import (
    MAX_FILE_SIZE, MAX_COMMENT_LENGTH, ALLOWED_FILE_EXTENSIONS, 
    ALLOWED_MIME_TYPES, DANGEROUS_XSS_PATTERNS
)


class ExpenseItemForm(forms.ModelForm):
    """Форма создания и редактирования задачи"""
    
    class Meta:
        model = ExpenseItem
        fields = [
            'title', 'description', 'task_type', 'category',
            'estimated_hours', 'priority', 'assigned_to', 'due_date',
            'progress_percent', 'is_urgent', 'tags'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название задачи'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Описание задачи'
            }),
            'task_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.0',
                'step': '0.5',
                'min': '0'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'progress_percent': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100'
            }),
            'is_urgent': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Теги через запятую'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def __init__(self, project=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        
        # Настраиваем выбор категорий
        self.fields['category'].queryset = ExpenseCategory.objects.filter(is_active=True)
        self.fields['category'].empty_label = "Выберите категорию"
        
        # Настраиваем выбор исполнителя
        if project:
            # Показываем только участников проекта
            project_members = project.members.filter(is_active=True).values_list('user', flat=True)
            self.fields['assigned_to'].queryset = project.members.filter(
                is_active=True
            ).select_related('user')
        
        self.fields['assigned_to'].empty_label = "Не назначен"

    def clean_estimated_hours(self):
        hours = self.cleaned_data.get('estimated_hours')
        if hours and hours < 0:
            raise ValidationError(_('Количество часов не может быть отрицательным.'))
        return hours
    
    def clean_progress_percent(self):
        progress = self.cleaned_data.get('progress_percent')
        if progress and (progress < 0 or progress > 100):
            raise ValidationError(_('Прогресс должен быть от 0 до 100%.'))
        return progress

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise ValidationError(_('Название не может быть пустым.'))
        return title


class QuickExpenseForm(forms.Form):
    """Быстрая форма добавления расхода"""
    
    title = forms.CharField(
        label=_('Название'),
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Название расхода'
        })
    )
    estimated_hours = forms.DecimalField(
        label=_('Планируемые часы'),
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.0',
            'step': '0.5',
            'min': '0'
        })
    )
    task_type = forms.ChoiceField(
        label=_('Тип задачи'),
        choices=ExpenseItem.TaskType.choices,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    description = forms.CharField(
        label=_('Описание'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Описание расхода (необязательно)'
        })
    )

    def clean_estimated_hours(self):
        hours = self.cleaned_data.get('estimated_hours')
        if hours and hours < 0:
            raise ValidationError(_('Количество часов не может быть отрицательным.'))
        return hours
    
    def clean_progress_percent(self):
        progress = self.cleaned_data.get('progress_percent')
        if progress and (progress < 0 or progress > 100):
            raise ValidationError(_('Прогресс должен быть от 0 до 100%.'))
        return progress


class ExpenseDocumentForm(forms.ModelForm):
    """Форма загрузки документов к расходу"""
    
    class Meta:
        model = ExpenseDocument
        fields = ['name', 'file_type', 'file']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название документа'
            }),
            'file_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif'
            }),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Проверяем размер файла
            if file.size > MAX_FILE_SIZE:
                raise ValidationError(_('Размер файла не должен превышать 5 МБ.'))
            
            # Проверяем, что файл не пустой
            if file.size == 0:
                raise ValidationError(_('Файл не может быть пустым.'))
            
            # Проверяем расширение файла
            file_name = file.name.lower()
            if not any(file_name.endswith(ext) for ext in ALLOWED_FILE_EXTENSIONS):
                raise ValidationError(_(
                    'Недопустимый тип файла. Разрешены: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, GIF'
                ))
            
            # Проверяем MIME тип для дополнительной безопасности
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file.name)
            
            if mime_type and mime_type not in ALLOWED_MIME_TYPES:
                raise ValidationError(_('Недопустимый тип файла по содержимому.'))
        
        return file


class ExpenseCommentForm(forms.ModelForm):
    """Форма добавления комментария к расходу с возможностью прикрепления файлов"""
    
    attachments = forms.FileField(
        label=_('Вложения'),
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.xls,.xlsx,.mp4,.avi,.mov,.txt'
        }),
        help_text=_('Загрузите файл: фото, видео или документ')
    )
    
    class Meta:
        model = ExpenseComment
        fields = ['text', 'is_internal']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ваш комментарий...'
            }),
            'is_internal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_text(self):
        text = self.cleaned_data.get('text', '').strip()
        if not text:
            raise ValidationError(_('Комментарий не может быть пустым.'))
        
        # Защита от XSS - удаляем потенциально опасные теги
        import re
        for pattern in DANGEROUS_XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValidationError(_('Комментарий содержит недопустимое содержимое.'))
        
        # Ограничиваем длину комментария
        if len(text) > MAX_COMMENT_LENGTH:
            raise ValidationError(_('Комментарий слишком длинный (максимум 2000 символов).'))
        
        return text
    
    def clean_attachments(self):
        file = self.cleaned_data.get('attachments')
        if not file:
            return file
            
        # Проверяем размер файла (увеличиваем лимит для видео)
        max_size = MAX_FILE_SIZE * 10 if self._is_video_file(file.name) else MAX_FILE_SIZE
        if file.size > max_size:
            raise ValidationError(_(f'Размер файла {file.name} не должен превышать {max_size // (1024*1024)} МБ.'))
        
        # Проверяем расширение файла
        file_name = file.name.lower()
        allowed_extensions = ALLOWED_FILE_EXTENSIONS + ['.mp4', '.avi', '.mov', '.txt']
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise ValidationError(_(f'Недопустимый тип файла: {file.name}'))
        
        return file
    
    def _is_video_file(self, filename):
        """Проверяет, является ли файл видео"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        return any(filename.lower().endswith(ext) for ext in video_extensions)


class ExpenseCommentAttachmentForm(forms.ModelForm):
    """Форма для отдельной загрузки вложений к комментарию"""
    
    class Meta:
        model = ExpenseCommentAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.xls,.xlsx,.mp4,.avi,.mov,.txt'
            }),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Определяем тип файла по расширению
            file_name = file.name.lower()
            
            # Проверяем размер файла (больше для видео)
            max_size = MAX_FILE_SIZE * 10 if self._is_video_file(file_name) else MAX_FILE_SIZE
            if file.size > max_size:
                raise ValidationError(_(f'Размер файла не должен превышать {max_size // (1024*1024)} МБ.'))
            
            # Проверяем расширение файла
            allowed_extensions = ALLOWED_FILE_EXTENSIONS + ['.mp4', '.avi', '.mov', '.txt']
            if not any(file_name.endswith(ext) for ext in allowed_extensions):
                raise ValidationError(_('Недопустимый тип файла.'))
        
        return file
    
    def _is_video_file(self, filename):
        """Проверяет, является ли файл видео"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        return any(filename.lower().endswith(ext) for ext in video_extensions)


class ExpenseFilterForm(forms.Form):
    """Форма фильтрации расходов"""
    
    status = forms.ChoiceField(
        label=_('Статус'),
        choices=[('', 'Все статусы')] + ExpenseItem.Status.choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    task_type = forms.ChoiceField(
        label=_('Тип задачи'),
        choices=[('', 'Все типы')] + ExpenseItem.TaskType.choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    category = forms.ModelChoiceField(
        label=_('Категория'),
        queryset=ExpenseCategory.objects.filter(is_active=True),
        required=False,
        empty_label='Все категории',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    priority = forms.ChoiceField(
        label=_('Приоритет'),
        choices=[('', 'Все приоритеты'), ('low', 'Низкий'), ('medium', 'Средний'), ('high', 'Высокий')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    date_from = forms.DateField(
        label=_('Дата от'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        label=_('Дата до'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    amount_from = forms.DecimalField(
        label=_('Сумма от'),
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        })
    )
    amount_to = forms.DecimalField(
        label=_('Сумма до'),
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        amount_from = cleaned_data.get('amount_from')
        amount_to = cleaned_data.get('amount_to')

        if date_from and date_to and date_from > date_to:
            raise ValidationError(_('Дата "от" не может быть больше даты "до".'))

        if amount_from and amount_to and amount_from > amount_to:
            raise ValidationError(_('Сумма "от" не может быть больше суммы "до".'))

        return cleaned_data


class ExpenseCategoryForm(forms.ModelForm):
    """Форма создания и редактирования категории расходов"""
    
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'description', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название категории'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание категории'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError(_('Название категории не может быть пустым.'))
        return name


class BulkExpenseActionForm(forms.Form):
    """Форма для массовых действий с расходами"""
    
    ACTION_CHOICES = [
        ('approve', _('Одобрить')),
        ('reject', _('Отклонить')),
        ('change_category', _('Изменить категорию')),
        ('change_priority', _('Изменить приоритет')),
        ('delete', _('Удалить')),
    ]
    
    action = forms.ChoiceField(
        label=_('Действие'),
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    category = forms.ModelChoiceField(
        label=_('Новая категория'),
        queryset=ExpenseCategory.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    priority = forms.ChoiceField(
        label=_('Новый приоритет'),
        choices=[('low', 'Низкий'), ('medium', 'Средний'), ('high', 'Высокий')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    reason = forms.CharField(
        label=_('Причина (для отклонения)'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Укажите причину отклонения'
        })
    )
