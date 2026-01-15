from django.db import models
from django.conf import settings
import uuid


class Test(models.Model):
    """
    Модель самого теста.
    """
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('published', 'Опубликован'),
        ('closed', 'Закрыт'),
    )

    EVALUATION_CHOICES = (
        ('points', 'По сумме баллов'),
        ('percent', 'По проценту правильных'),
    )

    evaluation_method = models.CharField(
        max_length=10,
        choices=EVALUATION_CHOICES,
        default='points',
        verbose_name="Метод оценивания"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tests'
    )

    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")

    time_limit = models.PositiveIntegerField(
        default=0,
        help_text="Время на прохождение в секундах (0 = без ограничений)"
    )
    passing_score = models.PositiveIntegerField(
        default=0,
        help_text="Минимальный балл для зачета"
    )

    success_message = models.TextField(blank=True, default="Поздравляем! Вы сдали тест.")
    failure_message = models.TextField(blank=True, default="К сожалению, тест не сдан.")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    public_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичная ссылка")

    def __str__(self):
        return self.title


class Question(models.Model):
    TYPE_CHOICES = (
        ('single', 'Один правильный ответ'),
        ('multi', 'Несколько правильных ответов'),
        ('input', 'Ввод текста'),
        ('match', 'Соответствие'),
        ('sequence', 'Последовательность'),
    )

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    text = models.TextField(verbose_name="Текст вопроса")
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='single')

    order_num = models.PositiveIntegerField(default=0)

    points = models.PositiveIntegerField(default=1)

    answer_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['order_num']

    def __str__(self):
        return f"{self.text[:50]}..."


class TestAttempt(models.Model):
    """
    Попытка прохождения теста конкретным пользователем.
    Создается, когда студент нажимает "Начать тест".
    """
    STATUS_CHOICES = (
        ('in_progress', 'В процессе'),
        ('finished', 'Завершен'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='test_attempts'
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='attempts'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    total_score = models.PositiveIntegerField(default=0, verbose_name="Набранный балл")

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.test} ({self.status})"


class UserAnswer(models.Model):
    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )

    selected_answer = models.JSONField(default=dict)

    is_correct = models.BooleanField(default=False)
    points_awarded = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Ответ на {self.question_id}"