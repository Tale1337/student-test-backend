# Документация API (Student Test Constructor)

Базовый URL: `http://127.0.0.1:8000/`

## 🔐 Авторизация
Проект использует Session-based authentication(Куки).

## 1. Регистрация
URL: `/api/register/`
Method: `POST`

Body (JSON):
```json
{
  "email": "student@example.com",
  "password": "strongpassword",  
  "first_name": "Ivan",
  "last_name": "Ivanov",
  "role": "student"
}
```
Варианты роли: "student", "employer", "admin". По дефолту: "student"

Ответ (201 Created):
```json
{
  "message": "Успешно зарегистрировались!"
}
```

Ошибка (400 Bad Request):
```json
{
  "error": "Такой email уже зарегистрирован"
}
```

---

## 2. Вход в систему (Login)
URL: `/api/login/`
Method: `POST`

При успешном входе сервер устанавливает куку `sessionid`.

Body (JSON):
```json
{
  "email": "student@example.com",
  "password": "strongpassword"
}
```

Ответ (200 OK):
```json
{
  "message": "Вы вошли!",
  "user": {
      "email": "student@example.com",
      "role": "student",
      "name": "Ivan"
  }
}
```

Ошибка (401 Unauthorized):
```json
{
  "error": "Неверный email или пароль"
}
```

---

## 3. Главная страница
URL: `/api/main/`
Method: `GET`
Доступ: Только для авторизованных пользователей.

Ответ (200 OK):
```json
{
  "message": "Привет, Ivan (student)!",
  "email": "student@example.com"
}
```

Ошибка (401 Unauthorized):
```json
{
  "error": "Нет доступа"
}
```

---

## 4. Выход (Logout)
URL: `/api/logout/`
Method: `GET` (или POST)

Удаляет сессию пользователя.

Ответ (200 OK):
```json
{
  "message": "Вышли"
}
```
