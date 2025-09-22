from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import User


class LoginForm(forms.Form):
    """Форма входа в систему"""
    
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label=_('Пароль'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class UserRegistrationForm(UserCreationForm):
    """Форма регистрации нового пользователя"""
    
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )
    first_name = forms.CharField(
        label=_('Имя'),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Имя'
        })
    )
    last_name = forms.CharField(
        label=_('Фамилия'),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Фамилия'
        })
    )
    phone = forms.CharField(
        label=_('Телефон'),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (999) 123-45-67'
        })
    )
    role = forms.ChoiceField(
        label=_('Роль'),
        choices=User.Role.choices,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Настраиваем стили для полей паролей
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Минимум 8 символов'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('Пользователь с таким email уже существует.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']  # Используем email как username
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """Форма редактирования профиля"""
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'role')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Фамилия'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 123-45-67'
            }),
            'role': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Делаем поля обязательными
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['role'].required = True
    


class AccessKeyForm(forms.Form):
    """Форма для ввода ключа доступа к проекту"""
    
    key = forms.CharField(
        label=_('Ключ доступа'),
        max_length=36,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ключ доступа к проекту',
            'maxlength': 36
        })
    )

    def clean_key(self):
        key = self.cleaned_data.get('key', '').strip()
        if not key:
            raise ValidationError(_('Ключ доступа обязателен для заполнения.'))
        
        # Валидация UUID формата
        import uuid
        try:
            uuid.UUID(key)
        except ValueError:
            raise ValidationError(_('Неверный формат ключа доступа. Ключ должен быть в формате UUID.'))
        
        # Проверяем существование ключа в базе данных
        from .models import ProjectAccessKey
        try:
            access_key = ProjectAccessKey.objects.get(key=key)
            if not access_key.is_active:
                raise ValidationError(_('Ключ доступа неактивен.'))
            if access_key.expires_at and access_key.expires_at < timezone.now():
                raise ValidationError(_('Ключ доступа истек.'))
        except ProjectAccessKey.DoesNotExist:
            raise ValidationError(_('Ключ доступа не найден.'))
        
        return key


class PasswordChangeForm(forms.Form):
    """Форма смены пароля"""
    
    old_password = forms.CharField(
        label=_('Текущий пароль'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите текущий пароль'
        })
    )
    new_password1 = forms.CharField(
        label=_('Новый пароль'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Минимум 8 символов'
        })
    )
    new_password2 = forms.CharField(
        label=_('Подтверждение нового пароля'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите новый пароль'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError(_('Неверный текущий пароль.'))
        return old_password

    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        if password1:
            # Проверяем длину пароля
            if len(password1) < 8:
                raise ValidationError(_('Пароль должен содержать минимум 8 символов.'))
            # Проверяем, что пароль не слишком простой
            if password1.isdigit():
                raise ValidationError(_('Пароль не может состоять только из цифр.'))
            if password1.lower() in ['password', '12345678', 'qwerty123']:
                raise ValidationError(_('Пароль слишком простой.'))
        return password1
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError(_('Пароли не совпадают.'))
            # Проверяем, что новый пароль отличается от старого
            if self.user.check_password(password1):
                raise ValidationError(_('Новый пароль должен отличаться от текущего.'))
        return password2

    def save(self):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user
