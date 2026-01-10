from django.urls import path
from . import views

urlpatterns = [
    path('', views.test_list_create_view),
    path('<int:test_id>/questions/', views.question_list_create_view),
    path('<int:test_id>/', views.test_detail_view),
    path('<int:test_id>/start/', views.start_test_view),
    path('attempts/<int:attempt_id>/submit_answer/', views.submit_answer_view),
    path('attempts/<int:attempt_id>/finish/', views.finish_test_view),
    path('my-attempts/', views.user_attempts_view),  # История студента
]