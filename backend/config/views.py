# views.py
import json
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from rest_framework.views import APIView

class CsrfExemptAPIView(APIView):
    """Базовый класс для APIView без CSRF защиты"""
    def dispatch(self, request, *args, **kwargs):
        # Отключаем CSRF проверку для этого view
        request._dont_enforce_csrf_checks = True
        return super().dispatch(request, *args, **kwargs)

@ensure_csrf_cookie
def get_csrf(request):
    """Устанавливает CSRF cookie и возвращает токен"""
    return JsonResponse({
        'csrfToken': get_token(request)
    })


@require_http_methods(["POST"])
def login_view(request):
    """Вход пользователя по email"""
    try:
        data = json.loads(request.body)
        email = data.get('username', '').lower().strip()
        password = data.get('password', '')
        remember = data.get('remember', False)

        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            return JsonResponse(
                {'detail': 'Неверный email или пароль'},
                status=401
            )

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            login(request, user)

            if remember:
                request.session.set_expiry(1209600)
            else:
                request.session.set_expiry(0)

            return JsonResponse({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser
            })
        else:
            return JsonResponse(
                {'detail': 'Неверный email или пароль'},
                status=401
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {'detail': 'Неверный формат JSON'},
            status=400
        )


@require_http_methods(["POST"])
def register_view(request):
    """Регистрация нового пользователя"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        password2 = data.get('password2', '')
        first_name = data.get('first_name', '').strip()

        errors = {}

        if not email:
            errors['email'] = ['Введите email']
        elif User.objects.filter(email=email).exists():
            errors['email'] = ['Пользователь с таким email уже существует']

        if not password:
            errors['password'] = ['Введите пароль']
        elif len(password) < 8:
            errors['password'] = ['Пароль должен быть не менее 8 символов']

        if password != password2:
            errors['password2'] = ['Пароли не совпадают']

        if errors:
            return JsonResponse(errors, status=400)

        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name
        )

        login(request, user)

        return JsonResponse({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'message': 'Регистрация успешна'
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse(
            {'detail': 'Неверный формат JSON'},
            status=400
        )


@require_http_methods(["POST"])
def logout_view(request):
    """Выход пользователя"""
    logout(request)
    return JsonResponse({'detail': 'Выход выполнен'})


def me_view(request):
    """Текущий авторизованный пользователь"""
    if request.user.is_authenticated:
        return JsonResponse({
            'id': request.user.id,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser
        })
    return JsonResponse(
        {'detail': 'Не авторизован'},
        status=401
    )