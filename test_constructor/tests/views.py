import json
import copy
import uuid  # Нужно для share
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.db.models import Max, Sum
from django.utils import timezone
from .models import Test, Question, TestAttempt, UserAnswer


# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================

def clean_answers_for_student(q_type, answers_json):
    """ Очищает JSON от правильных ответов """
    clean_json = copy.deepcopy(answers_json)
    if q_type in ['single', 'multi']:
        for opt in clean_json.get('options', []):
            if 'is_correct' in opt: del opt['is_correct']
    elif q_type == 'input':
        if 'correct_answers' in clean_json: del clean_json['correct_answers']
    elif q_type == 'sequence':
        for item in clean_json.get('items', []):
            if 'correct_order' in item: del item['correct_order']
    elif q_type == 'match':
        if 'correct_matches' in clean_json: del clean_json['correct_matches']
    return clean_json


def check_user_answer(question, user_answer_json):
    """ Проверяет ответ и начисляет баллы """
    q_type = question.question_type
    db_data = question.answer_data

    if q_type == 'single':
        for opt in db_data.get('options', []):
            if opt['id'] == user_answer_json and opt.get('is_correct'):
                return True, question.points
    elif q_type == 'multi':
        if not isinstance(user_answer_json, list): return False, 0
        user_ids = set(user_answer_json)
        correct_ids = {opt['id'] for opt in db_data.get('options', []) if opt.get('is_correct')}
        if user_ids == correct_ids: return True, question.points
    elif q_type == 'input':
        user_text = str(user_answer_json).strip()
        correct_list = db_data.get('correct_answers', [])
        is_strict = db_data.get('case_sensitive', False)
        if is_strict:
            if user_text in correct_list: return True, question.points
        else:
            if user_text.lower() in [c.lower() for c in correct_list]: return True, question.points
    elif q_type == 'match':
        if user_answer_json == db_data.get('correct_matches', {}):
            return True, question.points
    elif q_type == 'sequence':
        correct_order_ids = [i['id'] for i in sorted(db_data.get('items', []), key=lambda x: x['correct_order'])]
        if user_answer_json == correct_order_ids:
            return True, question.points

    return False, 0


# ==========================================
# 1. БЛОК РАБОТОДАТЕЛЯ
# ==========================================

@csrf_exempt
def test_list_create_view(request):
    """ GET: Список тестов автора. POST: Создать тест. """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    if request.method == 'GET':
        user = request.user
        if user.role == 'student':
            return JsonResponse([], safe=False)

        tests = Test.objects.filter(author=user)
        data = []
        for t in tests:
            data.append({
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'questions_count': t.questions.count(),
                'created_at': t.created_at.strftime('%Y-%m-%d %H:%M'),
                'uuid': t.public_uuid,
            })
        return JsonResponse(data, safe=False)

    if request.method == 'POST':
        if request.user.role not in ['employer', 'admin']:
            return JsonResponse({'error': 'Нет прав'}, status=403)
        try:
            body = json.loads(request.body)
            new_test = Test.objects.create(
                author=request.user,
                title=body.get('title'),
                description=body.get('description', ''),
                time_limit=body.get('time_limit', 0),
                passing_score=body.get('passing_score', 0),
                evaluation_method=body.get('evaluation_method', 'points')
            )
            return JsonResponse({'message': 'Тест создан', 'id': new_test.id}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)


@csrf_exempt
def test_detail_editor_view(request, test_id):
    """ Управление тестом (Редактирование/Удаление) по ID """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    test_obj = get_object_or_404(Test, id=test_id)

    if test_obj.author != request.user and request.user.role != 'admin':
        return JsonResponse({'error': 'Нет прав'}, status=403)

    if request.method == 'GET':
        return JsonResponse({
            'id': test_obj.id,
            'title': test_obj.title,
            'description': test_obj.description,
            'time_limit': test_obj.time_limit,
            'passing_score': test_obj.passing_score,
            'evaluation_method': test_obj.evaluation_method
        })

    if request.method == 'PATCH':
        try:
            body = json.loads(request.body)
            if 'title' in body: test_obj.title = body['title']
            if 'description' in body: test_obj.description = body['description']
            if 'time_limit' in body: test_obj.time_limit = body['time_limit']
            if 'passing_score' in body: test_obj.passing_score = body['passing_score']
            test_obj.save()
            return JsonResponse({'message': 'Тест обновлен'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    if request.method == 'DELETE':
        test_obj.delete()
        return JsonResponse({'message': 'Тест удален'})

    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)


@csrf_exempt
def question_list_editor_view(request, test_id):
    """ Управление вопросами (Добавление) по ID """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    test_obj = get_object_or_404(Test, id=test_id)

    if test_obj.author != request.user and request.user.role != 'admin':
        return JsonResponse({'error': 'Нет прав'}, status=403)

    if request.method == 'GET':
        questions = test_obj.questions.all().order_by('order_num')
        data = [{'id': q.id, 'text': q.text, 'type': q.question_type, 'points': q.points, 'answers': q.answer_data} for
                q in questions]
        return JsonResponse(data, safe=False)

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            current_max = test_obj.questions.aggregate(Max('order_num'))['order_num__max']
            new_order = (current_max or 0) + 1

            new_q = Question.objects.create(
                test=test_obj,
                text=body.get('text'),
                question_type=body.get('type', 'single'),
                points=body.get('points', 1),
                answer_data=body.get('answer_data', {}),
                order_num=new_order
            )
            return JsonResponse({'message': 'Вопрос добавлен', 'id': new_q.id}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)


@csrf_exempt
def question_detail_view(request, question_id):
    """ Редактирование/Удаление конкретного вопроса """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    question = get_object_or_404(Question, id=question_id)
    if question.test.author != request.user and request.user.role != 'admin':
        return JsonResponse({'error': 'Нет прав'}, status=403)

    if request.method == 'DELETE':
        question.delete()
        return JsonResponse({'message': 'Вопрос удален'})

    if request.method == 'PATCH':
        try:
            body = json.loads(request.body)
            if 'text' in body: question.text = body['text']
            if 'points' in body: question.points = body['points']
            if 'answer_data' in body: question.answer_data = body['answer_data']
            question.save()
            return JsonResponse({'message': 'Вопрос обновлен'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)


@csrf_exempt
def share_test_view(request, test_id):
    """ Получить публичную ссылку (для Работодателя) """
    if not request.user.is_authenticated: return JsonResponse({'error': 'Auth required'}, status=401)
    test_obj = get_object_or_404(Test, id=test_id)
    if test_obj.author != request.user:
        return JsonResponse({'error': 'У вас нет прав делиться этим тестом'}, status=403)
    return JsonResponse({'test_public_uuid': f"{test_obj.public_uuid}"})


# ==========================================
# 2. БЛОК СТУДЕНТА
# ==========================================

@csrf_exempt
def test_public_detail_view(request, test_uuid):
    """ Обложка теста по ссылке """
    if not request.user.is_authenticated: return JsonResponse({'error': 'Auth required'}, status=401)
    test_obj = get_object_or_404(Test, public_uuid=test_uuid)
    return JsonResponse({
        'title': test_obj.title,
        'description': test_obj.description,
        'time_limit': test_obj.time_limit,
        'questions_count': test_obj.questions.count()
    })


@csrf_exempt
def start_test_view(request, test_uuid):
    """ Начать тест по ссылке """
    if not request.user.is_authenticated: return JsonResponse({'error': 'Auth required'}, status=401)
    if request.method == 'POST':
        test_obj = get_object_or_404(Test, public_uuid=test_uuid)

        attempt = TestAttempt.objects.create(
            user=request.user,
            test=test_obj,
            status='in_progress'
        )
        return JsonResponse({'message': 'Тест начат', 'attempt_id': attempt.id}, status=201)
    return JsonResponse({'error': 'Только POST'}, status=405)


@csrf_exempt
def question_list_student_view(request, test_uuid):
    """ Получить вопросы по ссылке (Без ответов!) """
    if not request.user.is_authenticated: return JsonResponse({'error': 'Auth required'}, status=401)

    test_obj = get_object_or_404(Test, public_uuid=test_uuid)

    if request.method == 'GET':
        has_active = TestAttempt.objects.filter(user=request.user, test=test_obj, status='in_progress').exists()
        if not has_active:
            return JsonResponse({'error': 'Нет активной попытки'}, status=403)

        questions = test_obj.questions.all().order_by('order_num')
        data = []
        for q in questions:
            data.append({
                'id': q.id,
                'text': q.text,
                'type': q.question_type,
                'points': q.points,
                'order_num': q.order_num,
                'answers': clean_answers_for_student(q.question_type, q.answer_data)  # Чистим!
            })
        return JsonResponse(data, safe=False)
    return JsonResponse({'error': 'Только GET'}, status=405)


# ==========================================
# 3. Ответы и История
# ==========================================

@csrf_exempt
def submit_answer_view(request, attempt_id):
    """ Сохранить ответ """
    if not request.user.is_authenticated: return JsonResponse({'error': 'Auth required'}, status=401)
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            question_id = body.get('question_id')
            selected_answer = body.get('selected_answer')

            attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
            if attempt.status != 'in_progress':
                return JsonResponse({'error': 'Тест завершен'}, status=400)

            question = get_object_or_404(Question, id=question_id)
            if question.test_id != attempt.test_id:
                return JsonResponse({'error': 'Чужой вопрос'}, status=400)

            is_correct, points = check_user_answer(question, selected_answer)

            UserAnswer.objects.update_or_create(
                attempt=attempt, question=question,
                defaults={'selected_answer': selected_answer, 'is_correct': is_correct, 'points_awarded': points}
            )
            return JsonResponse({'message': 'Принято'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Только POST'}, status=405)


@csrf_exempt
def finish_test_view(request, attempt_id):
    """ Завершить тест """
    if not request.user.is_authenticated: return JsonResponse({'error': 'Auth required'}, status=401)
    if request.method == 'POST':
        attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
        if attempt.status == 'finished':
            return JsonResponse({'error': 'Уже завершен'}, status=400)

        total_score = attempt.answers.aggregate(Sum('points_awarded'))['points_awarded__sum'] or 0
        attempt.total_score = total_score
        attempt.finished_at = timezone.now()
        attempt.status = 'finished'
        attempt.save()

        test = attempt.test
        passed = False
        if test.evaluation_method == 'points':
            passed = total_score >= test.passing_score
        elif test.evaluation_method == 'percent':
            max_score = test.questions.aggregate(Sum('points'))['points__sum'] or 0
            if max_score > 0:
                passed = (total_score / max_score * 100) >= test.passing_score

        return JsonResponse({
            'message': 'Тест завершен',
            'total_score': total_score,
            'passed': passed,
            'feedback': test.success_message if passed else test.failure_message
        })
    return JsonResponse({'error': 'Только POST'}, status=405)


@csrf_exempt
def user_attempts_view(request):
    """ История прохождений """
    if not request.user.is_authenticated: return JsonResponse({'error': 'Auth required'}, status=401)
    if request.method == 'GET':
        attempts = TestAttempt.objects.filter(user=request.user).select_related('test').order_by('-started_at')
        data = []
        for attempt in attempts:
            data.append({
                'attempt_id': attempt.id,
                'test_title': attempt.test.title,
                'status': attempt.status,
                'score': attempt.total_score,
                'max_score': attempt.test.passing_score,
                'date': attempt.finished_at.strftime(
                    '%d.%m.%Y') if attempt.finished_at else attempt.started_at.strftime('%d.%m.%Y')
            })
        return JsonResponse(data, safe=False)
    return JsonResponse({'error': 'Только GET'}, status=405)