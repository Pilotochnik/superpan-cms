from django.urls import path
from . import views, telegram_views

app_name = 'accounts'

urlpatterns = [
    # Стандартная авторизация отключена - только Telegram
    # path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    # path('register/', views.register_view, name='register'),  # Регистрация только через админку
    path('use-access-key/', views.use_access_key, name='use_access_key'),
    path('activity/', views.user_activity, name='activity'),
    path('reset-device/', views.reset_device_binding, name='reset_device'),
    path('roles/', views.role_info_view, name='role_info'),
    path('reset-device-binding/', views.reset_device_binding, name='reset_device_binding'),
    
    # Telegram авторизация - основной способ входа
    path('telegram-login/', telegram_views.TelegramLoginView.as_view(), name='telegram_login'),
    path('telegram-auth/', telegram_views.TelegramLoginView.as_view(), name='telegram_auth'),
    path('telegram/connect/', telegram_views.telegram_connect, name='telegram_connect'),
    path('telegram/disconnect/', telegram_views.telegram_disconnect, name='telegram_disconnect'),
    path('telegram/setup/', telegram_views.telegram_setup, name='telegram_setup'),
    path('telegram/qr/', telegram_views.telegram_qr_code, name='telegram_qr'),
    path('telegram/auth-status/', telegram_views.telegram_auth_status, name='telegram_auth_status'),
]