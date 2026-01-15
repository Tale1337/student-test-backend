from django.urls import path
from . import views

urlpatterns = [
    # --- 1. БЛОК РАБОТОДАТЕЛЯ ---
    path('', views.test_list_create_view),  # Список и создание
    path('<int:test_id>/', views.test_detail_editor_view),  # Редактирование, Удаление
    path('<int:test_id>/questions/', views.question_list_editor_view),  # Управление вопросами

    # Эндпоинт, чтобы получить UUID-ссылку (зная ID)
    path('<int:test_id>/share/', views.share_test_view),

    # --- 2. БЛОК СТУДЕНТА ---
    # Обложка теста (публичная)
    path('<uuid:test_uuid>/', views.test_public_detail_view),
    # Вопросы для прохождения
    path('<uuid:test_uuid>/questions/', views.question_list_student_view),
    # Старт
    path('<uuid:test_uuid>/start/', views.start_test_view),

    # --- 3. Ответы и История ---
    path('my-attempts/', views.user_attempts_view),
    path('attempts/<int:attempt_id>/submit_answer/', views.submit_answer_view),
    path('attempts/<int:attempt_id>/finish/', views.finish_test_view),
    path('questions/<int:question_id>/', views.question_detail_view),  # Редактирование вопроса
]