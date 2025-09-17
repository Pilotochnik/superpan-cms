"""
Django settings for superpan project.
"""

from pathlib import Path
from decouple import config
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Безопасные настройки ALLOWED_HOSTS
if DEBUG:
    ALLOWED_HOSTS = [
        'localhost', 
        '127.0.0.1', 
        '0.0.0.0',
        '192.168.0.116',     # Локальный IP для доступа с телефона
        '*.ngrok-free.app',  # Для ngrok
        '*.ngrok.io',        # Для старых версий ngrok
        '*.serveo.net',      # Для serveo
    ]
else:
    # Для продакшена - только конкретные домены
    allowed_hosts_config = config('ALLOWED_HOSTS', default='')
    if allowed_hosts_config:
        ALLOWED_HOSTS = allowed_hosts_config.split(',')
    else:
        raise ValueError("ALLOWED_HOSTS must be set in production environment")

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    'crispy_forms',
    'crispy_bootstrap5',
    
    # Local apps
    'accounts',
    'projects',
    'kanban',
    'admin_panel',
    'warehouse',
    'construction',
    'telegram_bot',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'accounts.telegram_middleware.TelegramAuthMiddleware',  # Telegram авторизация
    'accounts.telegram_middleware.TelegramBotMiddleware',   # Telegram бот интеграция
    'accounts.middleware.DeviceTrackingMiddleware',  # Device binding security
    'accounts.middleware.SessionSecurityMiddleware',  # Session timeout
    'accounts.middleware.SingleSessionMiddleware',  # Single session per user
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'superpan.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'superpan.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Настройки для работы через HTTPS прокси (ngrok, serveo)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG  # Принудительный HTTPS в продакшене
USE_TLS = not DEBUG

# Дополнительные настройки для туннелей
CSRF_TRUSTED_ORIGINS = [
    'https://*.serveo.net',
    'https://*.ngrok-free.app',
    'https://*.ngrok.io',
]

# Telegram Bot настройки
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8367784150:AAF7m6ZWW9BcoV17YOqnkLp1ScPmYpssy_E')
TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME', 'projectpanell_bot').replace('@', '')
TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL', '')

# Настройки cookies - безопасные для продакшена
CSRF_COOKIE_SECURE = not DEBUG  # True для HTTPS в продакшене
SESSION_COOKIE_SECURE = not DEBUG  # True для HTTPS в продакшене
CSRF_COOKIE_HTTPONLY = True  # Защита от XSS
SESSION_COOKIE_HTTPONLY = True  # Защита от XSS
SESSION_COOKIE_SAMESITE = 'Lax'  # Разрешаем запросы с мобильных устройств
CSRF_COOKIE_SAMESITE = 'Lax'  # Разрешаем запросы с мобильных устройств

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Настройки для продакшена
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Защита от переполнения буфера
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Дополнительные заголовки безопасности
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Настройки для продакшена
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000  # 1 год
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Session settings for security
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'  # Изменено на Lax для мобильных устройств
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 8 * 60 * 60  # 8 hours

# CSRF settings
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'  # Изменено на Lax для мобильных устройств

# Authentication settings
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/projects/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Email settings (configure for production)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Base URL for notifications and links
BASE_URL = 'http://192.168.0.116:8000'

# Настройки для локальной разработки
CSRF_TRUSTED_ORIGINS = [
    'http://192.168.0.116:8000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Настройки сессий для локальной сети
SESSION_COOKIE_SECURE = False  # Для HTTP в локальной сети
CSRF_COOKIE_SECURE = False     # Для HTTP в локальной сети

# Дополнительные настройки для отладки
LOGGING['loggers']['django.security'] = {
    'handlers': ['file', 'console'],
    'level': 'DEBUG',
    'propagate': True,
}
