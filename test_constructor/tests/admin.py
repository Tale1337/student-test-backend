import json
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from .models import Test, Question, TestAttempt, UserAnswer


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ('display_id', 'order_num', 'text', 'question_type', 'points', 'json_preview', 'edit_link')
    readonly_fields = ('display_id', 'json_preview', 'edit_link')

    # Функция, которая просто показывает ID
    def display_id(self, obj):
        return obj.id if obj.id else "-"

    display_id.short_description = "ID"

    def json_preview(self, obj):
        if not obj.answer_data:
            return "-"
        json_str = json.dumps(obj.answer_data, indent=2, ensure_ascii=False)
        return mark_safe(f'<pre style="max-height: 200px; overflow: auto;">{json_str}</pre>')

    json_preview.short_description = "Структура JSON"

    def edit_link(self, obj):
        if not obj.pk:
            return "-"
        url = reverse('admin:tests_question_change', args=[obj.pk])
        return mark_safe(f'<a href="{url}" class="button" style="padding:5px 10px;">Редактировать</a>')

    edit_link.short_description = "Действие"


# --- ADMIN ДЛЯ ТЕСТОВ ---
class TestAdmin(admin.ModelAdmin):
    # Тут ID у нас уже был
    list_display = ('id', 'title', 'author', 'status', 'created_at')
    list_display_links = ('id', 'title')
    list_filter = ('status', 'author', 'evaluation_method')
    inlines = [QuestionInline]


# --- ADMIN ДЛЯ ВОПРОСОВ ---
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'test', 'text', 'question_type', 'json_preview')
    list_filter = ('test', 'question_type')
    ordering = ('test', 'order_num')
    readonly_fields = ('json_preview',)

    def json_preview(self, obj):
        if not obj.answer_data:
            return "-"
        json_str = json.dumps(obj.answer_data, indent=2, ensure_ascii=False)
        return mark_safe(f'<pre>{json_str}</pre>')

    json_preview.short_description = "Состав вопроса (JSON)"


class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    fields = ('question', 'get_user_answer', 'is_correct', 'points_awarded')
    readonly_fields = ('question', 'get_user_answer', 'is_correct', 'points_awarded')
    can_delete = False

    def get_user_answer(self, obj):
        return mark_safe(f'<pre>{json.dumps(obj.selected_answer, ensure_ascii=False)}</pre>')
    get_user_answer.short_description = "Ответ студента"


class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'test', 'status', 'total_score', 'started_at', 'finished_at')
    list_filter = ('status', 'test', 'user')
    search_fields = ('user__email', 'test__title')
    inlines = [UserAnswerInline]
    readonly_fields = ('started_at', 'finished_at')


admin.site.register(TestAttempt, TestAttemptAdmin)
admin.site.register(UserAnswer)
admin.site.register(Test, TestAdmin)
admin.site.register(Question, QuestionAdmin)
