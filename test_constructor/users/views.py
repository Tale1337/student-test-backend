import json
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from .models import CustomUser


# 1. РЕГИСТРАЦИЯ
@csrf_exempt
def register_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            email = data.get('email')
            password = data.get('password')
            role = data.get('role', 'student')
            first_name = data.get('first_name')
            last_name = data.get('last_name')

            # Проверка: занят ли email
            if CustomUser.objects.filter(email=email).exists():
                return JsonResponse({'error': 'Такой email уже зарегистрирован'}, status=400)

            # Создание пользователя
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                role=role,
                first_name=first_name,
                last_name=last_name
            )

            return JsonResponse({'message': 'Успешно зарегистрировались!'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)


# 2. ВХОД (LOGIN)
@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({
                'message': 'Вы вошли!',
                'user': {
                    'email': user.email,
                    'role': user.role,
                    'name': user.first_name
                }
            })
        else:
            return JsonResponse({'error': 'Неверный email или пароль'}, status=401)

    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)


def main_page_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Нет доступа'}, status=401)

    return JsonResponse({
        'message': f"Привет, {request.user.first_name} ({request.user.role})!",
        'email': request.user.email
    })


def logout_api(request):
    logout(request)
    return JsonResponse({'message': 'Вышли'})