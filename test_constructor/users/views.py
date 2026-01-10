import json
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt

from .models import CustomUser


@csrf_exempt
def register_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            email = data.get('email')
            password = data.get('password')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            second_name = data.get('second_name', '')
            role = 'student'

            if CustomUser.objects.filter(email=email).exists():
                return JsonResponse({'error': 'Такой email уже зарегистрирован'}, status=400)

            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                role=role,
                first_name=first_name,
                last_name=last_name,
                second_name=second_name
            )

            return JsonResponse({'message': 'Успешно зарегистрировались!'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)


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


@csrf_exempt
def profile_view(request):
    """
    GET: Получить данные профиля (ФИО, почта).
    PATCH: Обновить данные (ФИО, почта, пароль).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    user = request.user

    # --- ПРОСМОТР ДАННЫХ ---
    if request.method == 'GET':
        return JsonResponse({
            'first_name': user.first_name,
            'last_name': user.last_name,
            'second_name': user.second_name,  # Наше поле "Отчество"
            'email': user.email,
            'role': user.role
        })

    # --- ОБНОВЛЕНИЕ ДАННЫХ ---
    if request.method == 'PATCH' or request.method == 'PUT':
        try:
            data = json.loads(request.body)

            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'second_name' in data:
                user.second_name = data['second_name']

            new_email = data.get('email')
            if new_email and new_email != user.email:
                if CustomUser.objects.filter(email=new_email).exists():
                    return JsonResponse({'error': 'Этот email уже занят другим пользователем'}, status=400)
                user.email = new_email

            new_password = data.get('password')
            if new_password:
                user.set_password(new_password)
                user.save()
                # ВАЖНО: Обновление сессии, чтобы не разлогинило после смены пароля
                update_session_auth_hash(request, user)
            else:
                user.save()

            return JsonResponse({'message': 'Данные успешно сохранены'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)