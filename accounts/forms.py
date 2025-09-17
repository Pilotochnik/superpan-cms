from django import forms
from django.contrib.auth.forms import UserCreationForm
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
        fields = ('first_name', 'last_name', 'phone')
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


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

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError(_('Пароли не совпадают.'))
        return password2

    def save(self):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user
