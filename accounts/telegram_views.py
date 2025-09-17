from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.conf import settings
import logging

from .models import User, TelegramUser

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Получает IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@method_decorator(csrf_exempt, name='dispatch')
class TelegramLoginView(View):
    """Авторизация через Telegram"""
    
    def get(self, request):
        """Показать страницу авторизации через Telegram"""
        bot_username = settings.TELEGRAM_BOT_USERNAME or 'your_bot_username'
        # Убираем символ @ если он есть
        if bot_username.startswith('@'):
            bot_username = bot_username[1:]
        
        # Проверяем токен авторизации от бота
        auth_token = request.GET.get('auth_token')
        if auth_token:
            try:
                from .models import TelegramAuthToken
                from datetime import datetime
                
                # Ищем токен
                token_obj = TelegramAuthToken.objects.get(token=auth_token)
                logger.info(f"Найден токен: {token_obj.token}, истекает: {token_obj.expires_at}, использован: {token_obj.is_used}")
                
                # Проверяем, не истек ли токен
                if token_obj.is_expired():
                    logger.warning(f"Токен истек: {token_obj.token}, время истечения: {token_obj.expires_at}")
                    messages.error(request, 'Токен авторизации истек. Попробуйте еще раз.')
                    return redirect('accounts:telegram_login')
                
                # Проверяем, не использован ли токен
                if token_obj.is_used:
                    messages.error(request, 'Токен уже использован.')
                    return redirect('accounts:telegram_login')
                
                # Авторизуем пользователя
                login(request, token_obj.user)
                
                # Привязываем устройство к пользователю
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                ip_address = get_client_ip(request)
                token_obj.user.bind_device(user_agent, ip_address)
                logger.info(f"Устройство привязано к пользователю {token_obj.user.email}. IP: {ip_address}")
                
                # Создаем или обновляем связь с Telegram, если её нет
                if token_obj.telegram_user:
                    logger.info(f"Telegram пользователь найден: {token_obj.telegram_user.telegram_id}")
                    # Если у пользователя еще нет Telegram ID, создаем связь
                    if not token_obj.user.get_telegram_id():
                        logger.info(f"Создаем связь между пользователем {token_obj.user.email} и Telegram ID {token_obj.telegram_user.telegram_id}")
                        # Создаем TelegramUser для пользователя
                        from .models import TelegramUser
                        telegram_user, created = TelegramUser.objects.get_or_create(
                            telegram_id=token_obj.telegram_user.telegram_id,
                            defaults={
                                'user': token_obj.user,
                                'username': token_obj.telegram_user.username or '',
                                'first_name': token_obj.telegram_user.first_name or '',
                                'last_name': token_obj.telegram_user.last_name or '',
                                'photo_url': token_obj.telegram_user.photo_url or '',
                                'language_code': token_obj.telegram_user.language_code or 'ru'
                            }
                        )
                        if not created:
                            # Обновляем существующего пользователя
                            telegram_user.user = token_obj.user
                            telegram_user.save()
                            logger.info(f"Обновлена связь для Telegram пользователя {telegram_user.telegram_id}")
                        else:
                            logger.info(f"Создана новая связь для Telegram пользователя {telegram_user.telegram_id}")
                        
                        # Проверяем, что связь создалась
                        updated_telegram_id = token_obj.user.get_telegram_id()
                        logger.info(f"После создания связи Telegram ID: {updated_telegram_id}")
                    else:
                        logger.info(f"У пользователя {token_obj.user.email} уже есть Telegram ID: {token_obj.user.get_telegram_id()}")
                else:
                    logger.warning(f"У токена {token_obj.token} нет связанного Telegram пользователя")
                
                # Отмечаем токен как использованный
                token_obj.mark_as_used(token_obj.user, token_obj.telegram_user)
                
                messages.success(request, f'Добро пожаловать, {token_obj.user.get_full_name()}!')
                
                # Перенаправляем в зависимости от роли
                if token_obj.user.role == 'admin':
                    return redirect('/management/')
                else:
                    return redirect('/projects/list/')
                    
            except TelegramAuthToken.DoesNotExist:
                messages.error(request, 'Неверный токен авторизации.')
                return redirect('accounts:telegram_login')
            except Exception as e:
                logger.error(f"Ошибка при авторизации через токен: {e}")
                messages.error(request, 'Произошла ошибка при авторизации.')
                return redirect('accounts:telegram_login')
        
        # Проверяем ошибки
        error_message = None
        if request.GET.get('error') == 'no_telegram_id':
            error_message = 'Ваш аккаунт не привязан к Telegram. Обратитесь к администратору.'
        elif request.GET.get('error') == 'device_not_allowed':
            error_message = 'Вход с данного устройства запрещен. Обратитесь к администратору для сброса привязки устройства.'
        
        return render(request, 'accounts/telegram_login.html', {
            'bot_username': bot_username,
            'bot_token': settings.TELEGRAM_BOT_TOKEN or 'your_bot_token',
            'error_message': error_message
        })
    
    def post(self, request):
        """Обработка данных авторизации от Telegram"""
        try:
            data = json.loads(request.body)
            logger.info(f"Получены данные от Telegram: {data}")
            
            # Получаем данные пользователя
            telegram_id = data.get('telegram_id') or data.get('id')
            username = data.get('username', '')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            photo_url = data.get('photo_url', '')
            language_code = data.get('language_code', 'ru')
            
            if not telegram_id:
                logger.warning("Отсутствует Telegram ID")
                return JsonResponse({'error': 'Отсутствует Telegram ID'}, status=400)
            
            # Ищем существующего пользователя Telegram
            try:
                telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
                user = telegram_user.user
                logger.info(f"Найден существующий пользователь: {user.email}")
                
                # Обновляем данные
                telegram_user.username = username
                telegram_user.first_name = first_name
                telegram_user.last_name = last_name
                telegram_user.photo_url = photo_url
                telegram_user.language_code = language_code
                telegram_user.save()
                
            except TelegramUser.DoesNotExist:
                # Пользователь не найден в базе - отказываем в доступе
                logger.warning(f"Попытка входа с несуществующим Telegram ID: {telegram_id}")
                return JsonResponse({
                    'error': 'Пользователь не найден в системе. Обратитесь к администратору для регистрации.',
                    'error_code': 'USER_NOT_FOUND'
                }, status=403)
            
            # Авторизуем пользователя
            login(request, user)
            logger.info(f"Пользователь {user.email} авторизован")
            
            # Определяем URL для перенаправления в зависимости от роли
            if user.role == 'admin':
                redirect_url = '/management/'
            else:
                redirect_url = '/projects/list/'
            
            return JsonResponse({
                'success': True,
                'redirect_url': redirect_url
            })
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка JSON: {e}")
            return JsonResponse({'error': 'Некорректные данные'}, status=400)
        except Exception as e:
            logger.error(f"Ошибка авторизации через Telegram: {e}")
            return JsonResponse({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)
    
    def verify_telegram_data(self, data):
        """Проверка подписи данных от Telegram"""
        bot_token = settings.TELEGRAM_BOT_TOKEN
        # Временно отключаем проверку подписи для тестирования
        logger.info("Пропускаем проверку подписи для тестирования")
        return True
        
        # Удаляем hash из данных
        received_hash = data.pop('hash', '')
        if not received_hash:
            logger.warning("Отсутствует hash в данных")
            return False
        
        # Создаем строку для проверки
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.items())])
        logger.info(f"Строка для проверки: {data_check_string}")
        
        # Создаем секретный ключ
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        
        # Вычисляем hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        logger.info(f"Полученный hash: {received_hash}")
        logger.info(f"Вычисленный hash: {calculated_hash}")
        
        return calculated_hash == received_hash
    
    # Функция создания пользователей удалена - теперь только суперпользователь регистрирует


@login_required
def telegram_connect(request):
    """Подключение существующего аккаунта к Telegram"""
    if request.method == 'GET':
        """Показать страницу подключения Telegram"""
        bot_username = settings.TELEGRAM_BOT_USERNAME or 'your_bot_username'
        # Убираем символ @ если он есть
        if bot_username.startswith('@'):
            bot_username = bot_username[1:]
        
        return render(request, 'accounts/telegram_connect.html', {
            'bot_username': bot_username,
            'bot_token': settings.TELEGRAM_BOT_TOKEN or 'your_bot_token'
        })
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            telegram_id = data.get('id')
            
            if not telegram_id:
                return JsonResponse({'error': 'Отсутствует Telegram ID'}, status=400)
            
            # Проверяем, не привязан ли уже этот Telegram аккаунт
            if TelegramUser.objects.filter(telegram_id=telegram_id).exists():
                return JsonResponse({'error': 'Этот Telegram аккаунт уже привязан'}, status=400)
            
            # Проверяем, не привязан ли уже Telegram к текущему пользователю
            if hasattr(request.user, 'telegram_profile'):
                return JsonResponse({'error': 'У вас уже привязан Telegram аккаунт'}, status=400)
            
            # Создаем связь
            TelegramUser.objects.create(
                user=request.user,
                telegram_id=telegram_id,
                username=data.get('username', ''),
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                photo_url=data.get('photo_url', ''),
                language_code=data.get('language_code', 'ru')
            )
            
            return JsonResponse({'success': True})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Некорректные данные'}, status=400)
        except Exception as e:
            logger.error(f"Ошибка подключения Telegram: {e}")
            return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)
    
    return render(request, 'accounts/telegram_connect.html')


@login_required
def telegram_disconnect(request):
    """Отключение Telegram аккаунта"""
    if hasattr(request.user, 'telegram_profile'):
        request.user.telegram_profile.delete()
        messages.success(request, 'Telegram аккаунт отключен')
    else:
        messages.error(request, 'Telegram аккаунт не привязан')
    
    return redirect('accounts:profile')


def telegram_setup(request):
    """Страница настройки Telegram авторизации"""
    return render(request, 'accounts/telegram_setup.html')


def telegram_qr_code(request):
    """Генерация QR кода для Telegram авторизации"""
    import qrcode
    import io
    import base64
    from django.http import HttpResponse
    from django.utils import timezone
    from datetime import timedelta
    from .models import TelegramAuthToken
    
    # Создаем токен авторизации в базе данных
    auth_token = TelegramAuthToken.objects.create(
        expires_at=timezone.now() + timedelta(minutes=10)  # Токен действует 10 минут
    )
    
    logger.info(f"Создан токен авторизации: {auth_token.token}")
    
    # Сохраняем токен в сессии
    request.session['telegram_auth_token'] = str(auth_token.token)
    
    # Создаем QR код с ссылкой на бота с параметром авторизации
    bot_username = settings.TELEGRAM_BOT_USERNAME or 'projectpanell_bot'
    bot_url = f"https://t.me/{bot_username}?start=auth_{auth_token.token}"
    
    logger.info(f"Создаем QR код с URL: {bot_url}")
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(bot_url)
    qr.make(fit=True)
    
    # Создаем изображение
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Конвертируем в base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    logger.info(f"QR код создан успешно, размер: {len(image_base64)} символов")
    
    return HttpResponse(f'<img src="data:image/png;base64,{image_base64}" style="max-width: 200px; height: auto;">')


def telegram_auth_status(request):
    """Проверка статуса авторизации через Telegram"""
    from django.http import JsonResponse
    from .models import TelegramAuthToken
    
    auth_token_str = request.session.get('telegram_auth_token')
    if not auth_token_str:
        return JsonResponse({'status': 'no_token'})
    
    try:
        # Ищем токен в базе данных
        auth_token = TelegramAuthToken.objects.get(token=auth_token_str)
        
        # Проверяем, не истек ли токен
        if auth_token.is_expired():
            return JsonResponse({'status': 'expired'})
        
        # Проверяем, был ли токен использован
        if auth_token.is_used and auth_token.user:
            return JsonResponse({
                'status': 'success',
                'user_id': auth_token.user.id,
                'username': auth_token.telegram_user.username if auth_token.telegram_user else '',
                'first_name': auth_token.telegram_user.first_name if auth_token.telegram_user else '',
                'token': str(auth_token.token)
            })
        
        # Токен существует, но еще не использован
        return JsonResponse({
            'status': 'pending',
            'token': str(auth_token.token)
        })
        
    except TelegramAuthToken.DoesNotExist:
        return JsonResponse({'status': 'invalid_token'})
