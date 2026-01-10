import json
import copy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.db.models import Max
from django.utils import timezone
from .models import Test, Question, TestAttempt, UserAnswer



def clean_answers_for_student(q_type, answers_json):
    """
    Убирает поля 'is_correct', 'correct_matches' и т.д.
    """
    clean_json = copy.deepcopy(answers_json)

    if q_type in ['single', 'multi']:
        options = clean_json.get('options', [])
        for opt in options:
            if 'is_correct' in opt:
                del opt['is_correct']

    elif q_type == 'input':
        if 'correct_answers' in clean_json:
            del clean_json['correct_answers']

    elif q_type == 'sequence':
        items = clean_json.get('items', [])
        for item in items:
            if 'correct_order' in item:
                del item['correct_order']

    elif q_type == 'match':
        if 'correct_matches' in clean_json:
            del clean_json['correct_matches']

    return clean_json


def check_user_answer(question, user_answer_json):
    """
    Сравнивает ответ пользователя с правильным из БД.
    """
    q_type = question.question_type
    db_data = question.answer_data

    if q_type == 'single':
        user_id = user_answer_json
        for opt in db_data.get('options', []):
            if opt['id'] == user_id:
                if opt.get('is_correct'):
                    return True, question.points
        return False, 0

    elif q_type == 'multi':
        if not isinstance(user_answer_json, list):
            return False, 0
        user_ids = set(user_answer_json)
        correct_ids = set()
        for opt in db_data.get('options', []):
            if opt.get('is_correct'):
                correct_ids.add(opt['id'])
        if user_ids == correct_ids:
            return True, question.points
        return False, 0

    elif q_type == 'input':
        user_text = str(user_answer_json).strip()
        correct_list = db_data.get('correct_answers', [])
        is_strict = db_data.get('case_sensitive', False)
        if is_strict:
            if user_text in correct_list:
                return True, question.points
        else:
            user_lower = user_text.lower()
            correct_lower = [c.lower() for c in correct_list]
            if user_lower in correct_lower:
                return True, question.points
        return False, 0

    elif q_type == 'match':
        user_matches = user_answer_json
        correct_matches = db_data.get('correct_matches', {})

        if user_matches == correct_matches:
            return True, question.points
        return False, 0

    elif q_type == 'sequence':
        user_order = user_answer_json
        sorted_items = sorted(db_data.get('items', []), key=lambda x: x['correct_order'])
        correct_ids_order = [item['id'] for item in sorted_items]
        if user_order == correct_ids_order:
            return True, question.points
        return False, 0

    return False, 0



@csrf_exempt
def test_list_create_view(request):
    """
    GET: Получить список всех тестов
    POST: Создать новый тест
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    if request.method == 'GET':
        user = request.user

        if user.role == 'student':
            # tests = Test.objects.filter(status='published')
            return JsonResponse({'error': 'Только у работодателей и админов есть тесты.'}, status=403)

        else:
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
                # 'is_owner': user == t.author
            })
        return JsonResponse(data, safe=False)

    # СОЗДАНИЕ ТЕСТА
    if request.method == 'POST':

        ALLOWED_ROLES = ['employer', 'admin']

        if request.user.role not in ALLOWED_ROLES:
            return JsonResponse({'error': 'Только работодатели и админы могут создавать тесты'}, status=403)

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
def test_detail_view(request, test_id):
    """
    GET: Получить информацию о тесте (Название, Описание) БЕЗ вопросов.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    test_obj = get_object_or_404(Test, id=test_id)

    # if request.user.role == 'student' and test_obj.status != 'published':
    #    return JsonResponse({'error': 'Тест не опубликован'}, status=403)

    return JsonResponse({
        'id': test_obj.id,
        'title': test_obj.title,
        'description': test_obj.description,
        'time_limit': test_obj.time_limit,
        # 'passing_score': test_obj.passing_score,
        # 'questions_count': test_obj.questions.count(),
        # 'status': test_obj.status
    })


@csrf_exempt
def question_list_create_view(request, test_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    test_obj = get_object_or_404(Test, id=test_id)

    if request.method == 'GET':
        if request.user.role == 'student':
            has_active_attempt = TestAttempt.objects.filter(
                user=request.user,
                test=test_obj,
                status='in_progress'
            ).exists()

            if not has_active_attempt:
                return JsonResponse({
                    'error': 'Сначала начните тест, чтобы увидеть вопросы.'
                }, status=403)

        questions = test_obj.questions.all().order_by('order_num')
        data = []

        is_owner = (request.user == test_obj.author) or (request.user.role == 'admin')

        for q in questions:
            question_data = {
                'id': q.id,
                'text': q.text,
                'type': q.question_type,
                'points': q.points,
                'order_num': q.order_num
            }

            if is_owner:
                question_data['answers'] = q.answer_data
            else:
                question_data['answers'] = clean_answers_for_student(q.question_type, q.answer_data)

            data.append(question_data)

        return JsonResponse(data, safe=False)

    if request.method == 'POST':
        if request.user.role == 'student':
            return JsonResponse({'error': 'Нет прав'}, status=403)

        if test_obj.author != request.user and request.user.role != 'admin':
            return JsonResponse({'error': 'Вы не автор этого теста'}, status=403)

        try:
            body = json.loads(request.body)

            current_max = test_obj.questions.aggregate(Max('order_num'))['order_num__max']
            new_order = (current_max or 0) + 1

            new_question = Question.objects.create(
                test=test_obj,
                text=body.get('text'),
                question_type=body.get('type', 'single'),
                points=body.get('points', 1),
                answer_data=body.get('answer_data', {}),
                order_num=new_order
            )
            return JsonResponse({'message': 'Вопрос добавлен', 'id': new_question.id}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)



@csrf_exempt
def start_test_view(request, test_id):
    """ POST: Начать тест (создать попытку) """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    if request.method == 'POST':
        test = get_object_or_404(Test, id=test_id)

        attempt = TestAttempt.objects.create(
            user=request.user,
            test=test,
            status='in_progress'
        )
        return JsonResponse({'message': 'Тест начат', 'attempt_id': attempt.id}, status=201)

    return JsonResponse({'error': 'Только POST'}, status=405)


@csrf_exempt
def submit_answer_view(request, attempt_id):
    """ POST: Сохранить ответ на конкретный вопрос """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            question_id = body.get('question_id')
            selected_answer = body.get('selected_answer')

            attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)

            if attempt.status != 'in_progress':
                return JsonResponse({'error': 'Тест уже завершен'}, status=400)

            question = get_object_or_404(Question, id=question_id)

            if question.test_id != attempt.test_id:
                return JsonResponse({'error': 'Этот вопрос не относится к текущему тесту!'}, status=400)

            is_correct, points = check_user_answer(question, selected_answer)

            UserAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'selected_answer': selected_answer,
                    'is_correct': is_correct,
                    'points_awarded': points
                }
            )

            return JsonResponse(
                {'message': 'Ответ принят', 'is_correct': is_correct})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Только POST'}, status=405)


@csrf_exempt
def finish_test_view(request, attempt_id):
    """ POST: Завершить тест и подсчитать итоги """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    if request.method == 'POST':
        attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)

        if attempt.status == 'finished':
            return JsonResponse({'error': 'Тест уже был завершен ранее'}, status=400)

        from django.db.models import Sum
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
                user_percent = (total_score / max_score) * 100
                passed = user_percent >= test.passing_score

        result_message = test.success_message if passed else test.failure_message

        return JsonResponse({
            'message': 'Тест завершен',
            'total_score': total_score,
            'passed': passed,
            'feedback': result_message
        })

    return JsonResponse({'error': 'Только POST'}, status=405)


@csrf_exempt
def user_attempts_view(request):
    """
    GET: Возвращает список всех попыток текущего пользователя (История)
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    if request.method == 'GET':
        attempts = TestAttempt.objects.filter(user=request.user).select_related('test').order_by('-started_at')

        data = []
        for attempt in attempts:
            # Вычисляем, сдал или нет (та же логика, что при завершении)
            test = attempt.test
            passed = False

            if attempt.status == 'finished':
                if test.evaluation_method == 'points':
                    passed = attempt.total_score >= test.passing_score
                elif test.evaluation_method == 'percent':
                    pass

            data.append({
                'attempt_id': attempt.id,
                'test_title': test.title,
                'status': attempt.status,
                'score': attempt.total_score,
                'max_score': test.passing_score,
                # 'started_at': attempt.started_at.strftime('%Y-%m-%d %H:%M'),
                # 'finished_at': attempt.finished_at.strftime('%Y-%m-%d %H:%M') if attempt.finished_at else None,
                'date': attempt.finished_at.strftime('%d.%m.%Y') if attempt.finished_at else None
            })

        return JsonResponse(data, safe=False)

    return JsonResponse({'error': 'Только GET'}, status=405)