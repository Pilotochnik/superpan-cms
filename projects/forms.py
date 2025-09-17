from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Project, ProjectMember, ProjectDocument
from accounts.models import User


class ProjectForm(forms.ModelForm):
    """Форма создания и редактирования проекта"""
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'budget', 'status', 
            'foreman', 'start_date', 'end_date', 'address'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название проекта'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Описание проекта'
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1000000.00',
                'step': '0.01'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'foreman': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Адрес объекта'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ограничиваем выбор прорабов только пользователями с соответствующей ролью
        self.fields['foreman'].queryset = User.objects.filter(
            role='foreman',
            is_active=True
        )
        self.fields['foreman'].empty_label = "Выберите прораба"

    def clean_budget(self):
        budget = self.cleaned_data.get('budget')
        if budget and budget <= 0:
            raise ValidationError(_('Бюджет должен быть больше нуля.'))
        return budget

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise ValidationError(_('Дата окончания не может быть раньше даты начала.'))

        return cleaned_data


class ProjectMemberForm(forms.ModelForm):
    """Форма для добавления участника проекта"""
    
    class Meta:
        model = ProjectMember
        fields = ['user', 'role', 'can_add_expenses', 'can_view_budget']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select'
            }),
            'role': forms.Select(attrs={
                'class': 'form-select'
            }),
            'can_add_expenses': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_view_budget': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, project=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        
        if project:
            # Исключаем пользователей, которые уже являются участниками
            existing_members = project.members.filter(is_active=True).values_list('user_id', flat=True)
            self.fields['user'].queryset = User.objects.filter(
                is_active=True
            ).exclude(id__in=existing_members)
        else:
            self.fields['user'].queryset = User.objects.filter(is_active=True)

    def clean_user(self):
        user = self.cleaned_data.get('user')
        if self.project and ProjectMember.objects.filter(
            project=self.project,
            user=user,
            is_active=True
        ).exists():
            raise ValidationError(_('Этот пользователь уже является участником проекта.'))
        return user


class ProjectDocumentForm(forms.ModelForm):
    """Форма для загрузки документов проекта"""
    
    class Meta:
        model = ProjectDocument
        fields = ['name', 'document_type', 'file', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название документа'
            }),
            'document_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание документа'
            }),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Проверяем размер файла (максимум 10 МБ)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError(_('Размер файла не должен превышать 10 МБ.'))
            
            # Проверяем расширение файла
            allowed_extensions = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                '.jpg', '.jpeg', '.png', '.gif', '.txt'
            ]
            file_name = file.name.lower()
            if not any(file_name.endswith(ext) for ext in allowed_extensions):
                raise ValidationError(_(
                    'Недопустимый тип файла. Разрешены: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, GIF, TXT'
                ))
        
        return file


class ProjectSearchForm(forms.Form):
    """Форма поиска проектов"""
    
    search = forms.CharField(
        label=_('Поиск'),
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию, описанию или адресу...'
        })
    )
    status = forms.ChoiceField(
        label=_('Статус'),
        choices=[('', 'Все статусы')] + Project.Status.choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    foreman = forms.ModelChoiceField(
        label=_('Прораб'),
        queryset=User.objects.filter(role='foreman', is_active=True),
        required=False,
        empty_label='Все прорабы',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class AccessKeyGenerationForm(forms.Form):
    """Форма для генерации ключа доступа"""
    
    user_email = forms.EmailField(
        label=_('Email пользователя'),
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'user@example.com (необязательно)'
        }),
        help_text=_('Если не указан, ключ может использовать любой пользователь')
    )
    expires_days = forms.IntegerField(
        label=_('Срок действия (дни)'),
        initial=30,
        min_value=1,
        max_value=365,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '30'
        }),
        help_text=_('Оставьте пустым для бессрочного ключа')
    )

    def clean_user_email(self):
        email = self.cleaned_data.get('user_email')
        if email:
            try:
                User.objects.get(email=email, is_active=True)
            except User.DoesNotExist:
                raise ValidationError(_('Пользователь с таким email не найден или неактивен.'))
        return email


class BudgetUpdateForm(forms.Form):
    """Форма для обновления бюджета проекта"""
    
    new_budget = forms.DecimalField(
        label=_('Новый бюджет'),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1000000.00',
            'step': '0.01'
        })
    )
    reason = forms.CharField(
        label=_('Причина изменения'),
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Укажите причину изменения бюджета'
        })
    )

    def clean_new_budget(self):
        budget = self.cleaned_data.get('new_budget')
        if budget and budget <= 0:
            raise ValidationError(_('Бюджет должен быть больше нуля.'))
        return budget
