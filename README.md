# Документация API (Student Test Constructor)

Базовый URL: `http://127.0.0.1:8000/`

## Авторизация
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
  "second_name": "Ivanovich"
}
```
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

## 5. Создать новый тест
URL: `/api/tests/`
Method: `POST`
Доступ: Работодатель, Админ.

Входные данные:
```json
{
  "title": "Тест с процентным подсчитыванием",
  "description": "Нужно набрать 80% за 1 час",
  "time_limit": 3600,
  "passing_score": 80,
  "evaluation_method": "percent"
}
```
ИЛИ
```json
{
    "title": "Тест с побальными подсчитыванием",
    "description": "Нужно набрать 6 баллов",
    "time_limit": 3600,
    "passing_score": 6,
    "evaluation_method": "points"
}
```

Ответ:
```json
{
    "message": "Тест создан",
    "id": 7
}
```

## 6. Добавить вопрос в тест
URL: `/api/tests/<test_id>/questions/`
Method: `POST`
Доступ: Только автор теста.

```json
{
    "text": "Текст вопроса",
    "type": "single",
    "points": 1,
    "answer_data": { ... } // Структура зависит от типа (см. ниже)
}
```

Примеры answer_data для разных типов:
А. Одиночный (single) / Множественный (multi):
```json
{
  "answer_data": {
    "options": [
      {
        "id": 1,
        "text": "Вариант 1",
        "is_correct": true
      },
      {
        "id": 2,
        "text": "Вариант 2",
        "is_correct": false
      }
    ]
  }
}
```

Б. Ввод текста (input):
```json
{
  "answer_data": {
    "correct_answers": [
      "Ответ",
      "ответ",
      "Answer"
    ],
    // Список правильных вариаций
    "case_sensitive": false
    // Учитывать ли регистр (false = нет)
  }
}
```

В. Соответствие (match):
```json
{
    "answer_data": {
        "keys": [ {"id": "ru", "content": "Россия"}, {"id": "de", "content": "Германия"} ],
        "values": [ {"id": "mos", "content": "Москва"}, {"id": "ber", "content": "Берлин"} ],
        "correct_matches": {
            "ru": "mos",  // ID ключа : ID значения
            "de": "ber"
        }
    }
}
```

Г. Последовательность (sequence):
```json
{
    "answer_data": {
        "items": [
            {"id": 1, "text": "Сначала это", "correct_order": 1},
            {"id": 2, "text": "Потом это", "correct_order": 2}
        ]
    }
}
```

## 7. Получить информацию о тесте, как создатель теста
URL: `/api/tests/<test_id>/`
Method: `GET`
```json
{
    "id": 1,
    "title": "Ещё один экзамен",
    "description": "Нужно набрать 80%",
    "time_limit": 3600,
    "passing_score": 80,
    "evaluation_method": "percent"
}
```

## 8. Поделиться тестом
URL: `/api/tests/<test_id>/share/`
Method: `GET`
Описание: для прохождения теста использовать этот uuid
```json
{
    "test_public_uuid": "83a54e70-8d0f-4734-a2a5-bff22a4d0eb0"
}
```

## 9. Получить информацию о тесте, как человек, проходящий тест
URL: `/api/tests/<test_public_uuid>/`
Method: `GET`
```json
{
    "title": "Ещё один экзамен",
    "description": "Нужно набрать 80%",
    "time_limit": 3600,
    "questions_count": 1
}
```

## 10. Начать тест (Создать попытку)
URL: `/api/tests/<test_public_uuid>/start/`
Method: `POST`

Ответ:
```json
{
    "message": "Тест начат",
    "attempt_id": 55  // Этот ID нужен для отправки ответов
}
```

## 11. Получить вопросы теста, как создатель теста
URL: `/api/tests/<test_id>/questions/`
Method: `GET`

## 12. Получить вопросы теста, как проходящий тест
URL: `/api/tests/<test_public_uuid>/questions/`
Method: `GET`

## 13. Отправить ответ на вопрос
URL: `/api/tests/attempts/<attempt_id>/submit_answer/`
Method: `POST`
```json
{
    "question_id": 10,
    "selected_answer": ... // Формат зависит от типа вопроса
}
```
Форматы selected_answer:
single: `1` (ID выбранного варианта, число)
multi: `[1, 3]` (Массив ID выбранных вариантов)
input: `"Текст ответа"` (Строка)
match: `{"ru": "mos", "de": "ber"}` (Объект: ID ключа -> ID значения)
sequence: `[2, 1]` (Массив ID вариантов в том порядке, как расставил студент)

## 14. Завершить тест
URL: `/api/tests/attempts/<attempt_id>/finish/`
Method: `POST`

Ответ:
```json
{
    "message": "Тест завершен",
    "total_score": 15,
    "passed": true,
    "feedback": "Поздравляем! Вы сдали тест."
}
```

## 15. Получить все мои тесты (для работодателя и админа)
URL: `/api/tests/`
Method: `GET`

```json
[
    {
        "id": 3,
        "title": "Ещё один экзамен"
    },
  ...
]
```
## 16. Удалить тест
URL: `/api/tests/<test_id/`
Method: `DELETE`

## 17. Удалить вопрос
URL: `/api/tests/questions/<question_id>/`
Method: `DELETE`

## 18. Изменить вопрос:
URL: `/api/tests/questions/<question_id>/`
Method: `PATCH`

```json
{
    "text": "Исправленный текст вопроса", // Опционально
    "points": 2,                          // Опционально
    "answer_data": {
        "options": [
            {"id": 1, "text": "Новый вариант ответа", "is_correct": true}, 
            {"id": 2, "text": "Старый вариант", "is_correct": false}
        ]
    }                                     // Опционально
}
```

## 19. Получить все мои попытки тестов
URl: `/api/tests/my-attempts/`
Method: `GET`
```json
[
    {
        "attempt_id": 1,
        "test_title": "Ещё один экзамен",
        "status": "finished",
        "score": 11,
        "max_score": 80,
        "date": "28.12.2025"
    },
  ...
]
```

## 20. Мой профиль
URL: `/api/profile/`
Method: `GET`
```json
{
    "first_name": "Петр",
    "last_name": "Петров",
    "second_name": "Петрович",
    "email": "21@test.com",
    "role": "student"
}
```

## 21. Редактировать мой профиль
URL: `/api/profile/`
Method: `PATCH`

```json
{
    "first_name": "Петр",        // Опционально
    "last_name": "Петров",       // Опционально
    "second_name": "Петрович",   // Опционально
    "email": "21@test.com",     // Опционально
    "password": "newpassword123" // Опционально
}
```

## Админка Django
URL: `/admin/`