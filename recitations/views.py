import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Count, Q
from django.http import JsonResponse, HttpResponseForbidden

from .models import Deck, Question, PracticeSession, PracticeAttempt, PracticeReminder, Notification
from .forms import DeckForm, QuestionForm, JoinDeckForm, PracticeSetupForm, PracticeReminderForm


# ==========================================
# QUESTION BANK & DECK MANAGEMENT
# ==========================================

@login_required
def deck_list_view(request):
    """
    Question Bank: Displays user's personal decks and public community decks.
    Supports search query and quick import by share code.
    """
    search_query = request.GET.get('q', '').strip()
    my_decks = Deck.objects.filter(owner=request.user)
    public_decks = Deck.objects.filter(is_public=True).exclude(owner=request.user)

    if search_query:
        my_decks = my_decks.filter(
            Q(title__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(description__icontains=search_query)
        )
        public_decks = public_decks.filter(
            Q(title__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    join_form = JoinDeckForm()

    context = {
        'my_decks': my_decks,
        'public_decks': public_decks,
        'search_query': search_query,
        'join_form': join_form,
        'total_user_questions': Question.objects.filter(deck__owner=request.user).count(),
    }
    return render(request, 'recitations/deck_list.html', context)


@login_required
def deck_create_view(request):
    """
    Creates a new recitation Question Deck.
    """
    if request.method == 'POST':
        form = DeckForm(request.POST)
        if form.is_valid():
            deck = form.save(commit=False)
            deck.owner = request.user
            deck.save()
            messages.success(request, f'Deck "{deck.title}" created! Now add your first recitation questions.')
            return redirect('deck_detail', deck_id=deck.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DeckForm()

    return render(request, 'recitations/deck_form.html', {
        'form': form,
        'title': 'Create New Question Deck',
        'btn_text': 'Create Deck'
    })


@login_required
def deck_detail_view(request, deck_id):
    """
    Displays questions in a deck, difficulty distribution, and action options.
    """
    deck = get_object_or_404(Deck, id=deck_id)
    # Check permissions: owner or public
    if not deck.is_public and deck.owner != request.user and not request.user.is_staff:
        messages.error(request, 'This deck is private.')
        return redirect('deck_list')

    questions = deck.questions.all().order_by('id')
    recent_sessions = PracticeSession.objects.filter(deck=deck, user=request.user).order_by('-started_at')[:3]

    context = {
        'deck': deck,
        'questions': questions,
        'is_owner': deck.owner == request.user,
        'recent_sessions': recent_sessions,
        'share_url': request.build_absolute_uri(f'/decks/join/?code={deck.share_code}'),
    }
    return render(request, 'recitations/deck_detail.html', context)


@login_required
def deck_edit_view(request, deck_id):
    """
    Updates an existing Question Deck (owner only).
    """
    deck = get_object_or_404(Deck, id=deck_id)
    if deck.owner != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this deck.')
        return redirect('deck_list')

    if request.method == 'POST':
        form = DeckForm(request.POST, instance=deck)
        if form.is_valid():
            form.save()
            messages.success(request, f'Deck "{deck.title}" updated successfully!')
            return redirect('deck_detail', deck_id=deck.id)
    else:
        form = DeckForm(instance=deck)

    return render(request, 'recitations/deck_form.html', {
        'form': form,
        'deck': deck,
        'title': f'Edit Deck: {deck.title}',
        'btn_text': 'Save Changes'
    })


@login_required
def deck_delete_view(request, deck_id):
    """
    Deletes a Question Deck (owner only).
    """
    deck = get_object_or_404(Deck, id=deck_id)
    if deck.owner != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete this deck.')
        return redirect('deck_list')

    if request.method == 'POST':
        title = deck.title
        deck.delete()
        messages.success(request, f'Deck "{title}" and all its questions have been deleted.')
        return redirect('deck_list')

    return render(request, 'recitations/deck_confirm_delete.html', {'deck': deck})


@login_required
def deck_join_view(request):
    """
    Deck Sharing: Allows students to join or inspect a shared deck using its share code.
    """
    code = request.GET.get('code') or request.POST.get('share_code')
    if request.method == 'POST':
        form = JoinDeckForm(request.POST)
        if form.is_valid():
            share_code = form.cleaned_data['share_code']
            deck = Deck.objects.get(share_code=share_code)
            messages.success(request, f'Found shared deck: "{deck.title}" by {deck.owner.username}!')
            return redirect('deck_detail', deck_id=deck.id)
    else:
        initial = {'share_code': code} if code else {}
        form = JoinDeckForm(initial=initial)

    return render(request, 'recitations/deck_join.html', {'form': form})


@login_required
def deck_clone_view(request, deck_id):
    """
    Deck Sharing: Clones a public or shared deck into user's own library.
    """
    source_deck = get_object_or_404(Deck, id=deck_id)
    if not source_deck.is_public and source_deck.owner != request.user:
        messages.error(request, "Cannot clone a private deck.")
        return redirect('deck_list')

    new_deck = Deck.objects.create(
        owner=request.user,
        title=f"{source_deck.title} (Copy)",
        description=source_deck.description,
        subject=source_deck.subject,
        is_public=False
    )

    for q in source_deck.questions.all():
        Question.objects.create(
            deck=new_deck,
            prompt=q.prompt,
            expected_answer=q.expected_answer,
            difficulty=q.difficulty,
            tags=q.tags
        )

    messages.success(request, f'Successfully cloned "{source_deck.title}" with {new_deck.question_count} questions into your library!')
    return redirect('deck_detail', deck_id=new_deck.id)


# ==========================================
# QUESTION CREATION & MANAGEMENT
# ==========================================

@login_required
def question_create_view(request, deck_id):
    """
    Adds a new recitation question with difficulty tag to a deck.
    """
    deck = get_object_or_404(Deck, id=deck_id)
    if deck.owner != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to add questions to this deck.')
        return redirect('deck_detail', deck_id=deck.id)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.deck = deck
            question.save()
            messages.success(request, 'Question added successfully!')
            if 'add_another' in request.POST:
                return redirect('question_create', deck_id=deck.id)
            return redirect('deck_detail', deck_id=deck.id)
    else:
        form = QuestionForm()

    return render(request, 'recitations/question_form.html', {
        'form': form,
        'deck': deck,
        'title': f'Add Question to {deck.title}',
        'btn_text': 'Add Question'
    })


@login_required
def question_edit_view(request, question_id):
    """
    Edits an existing recitation question.
    """
    question = get_object_or_404(Question, id=question_id)
    if question.deck.owner != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this question.')
        return redirect('deck_detail', deck_id=question.deck.id)

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully!')
            return redirect('deck_detail', deck_id=question.deck.id)
    else:
        form = QuestionForm(instance=question)

    return render(request, 'recitations/question_form.html', {
        'form': form,
        'deck': question.deck,
        'question': question,
        'title': 'Edit Question',
        'btn_text': 'Save Changes'
    })


@login_required
def question_delete_view(request, question_id):
    """
    Deletes a recitation question.
    """
    question = get_object_or_404(Question, id=question_id)
    deck_id = question.deck.id
    if question.deck.owner != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete this question.')
        return redirect('deck_detail', deck_id=deck_id)

    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully.')
        return redirect('deck_detail', deck_id=deck_id)

    return render(request, 'recitations/question_confirm_delete.html', {
        'question': question,
        'deck': question.deck
    })


# ==========================================
# PRACTICE MANAGEMENT (RANDOM PRACTICE & SCORING)
# ==========================================

@login_required
def practice_setup_view(request, deck_id):
    """
    Practice Setup: Configures randomized practice session (question count, difficulty, countdown timer).
    """
    deck = get_object_or_404(Deck, id=deck_id)
    available_count = deck.question_count

    if available_count == 0:
        messages.warning(request, 'This deck has no questions yet. Please add questions before practicing.')
        return redirect('deck_detail', deck_id=deck.id)

    if request.method == 'POST':
        form = PracticeSetupForm(request.POST)
        if form.is_valid():
            difficulty = form.cleaned_data['difficulty']
            time_limit = form.cleaned_data['time_limit']
            count = form.cleaned_data['question_count']
            randomize = form.cleaned_data['randomize']

            questions_qs = deck.questions.all()
            if difficulty and difficulty != 'ALL':
                questions_qs = questions_qs.filter(difficulty=difficulty)

            question_ids = list(questions_qs.values_list('id', flat=True))

            if not question_ids:
                messages.error(request, f'No questions found matching difficulty "{difficulty}".')
                return render(request, 'recitations/practice_setup.html', {'deck': deck, 'form': form})

            if randomize:
                random.shuffle(question_ids)

            selected_ids = question_ids[:count]

            # Create session
            session = PracticeSession.objects.create(
                user=request.user,
                deck=deck,
                time_limit_per_question=time_limit,
                difficulty_filter=difficulty,
                total_questions=len(selected_ids),
                status='IN_PROGRESS'
            )

            # Store queue in user session
            request.session[f'practice_{session.id}_queue'] = selected_ids
            request.session[f'practice_{session.id}_index'] = 0

            return redirect('practice_session', session_id=session.id)
    else:
        form = PracticeSetupForm(initial={'question_count': min(10, available_count)})

    return render(request, 'recitations/practice_setup.html', {
        'deck': deck,
        'form': form,
        'available_count': available_count,
    })


@login_required
def practice_session_view(request, session_id):
    """
    Interactive Randomized Practice Interface:
    - Countdown timer per question
    - Audio recitation simulation (Speech Recognition Web API) / Text response
    - Reveal expected answer
    - Self-scoring rubric (Mastered / Partially Correct / Needs Practice)
    """
    practice_session = get_object_or_404(PracticeSession, id=session_id, user=request.user)

    queue = request.session.get(f'practice_{practice_session.id}_queue', [])
    index = request.session.get(f'practice_{practice_session.id}_index', 0)

    # If completed or queue exhausted
    if index >= len(queue) or practice_session.status == 'COMPLETED':
        practice_session.status = 'COMPLETED'
        practice_session.completed_at = timezone.now()
        practice_session.calculate_score()
        practice_session.save()
        return redirect('practice_results', session_id=practice_session.id)

    current_question_id = queue[index]
    question = get_object_or_404(Question, id=current_question_id)

    progress_percent = int(((index) / len(queue)) * 100) if queue else 0

    context = {
        'practice_session': practice_session,
        'question': question,
        'current_number': index + 1,
        'total_in_session': len(queue),
        'progress_percent': progress_percent,
        'time_limit': practice_session.time_limit_per_question,
    }
    return render(request, 'recitations/practice_session.html', context)


@login_required
def practice_submit_answer_view(request, session_id):
    """
    Handles recording student's recitation answer, self-rating rubric, and elapsed time.
    Advances to next question.
    """
    if request.method != 'POST':
        return redirect('practice_session', session_id=session_id)

    practice_session = get_object_or_404(PracticeSession, id=session_id, user=request.user)
    question_id = request.POST.get('question_id')
    question = get_object_or_404(Question, id=question_id)

    user_answer = request.POST.get('user_answer', '').strip()
    self_rating = request.POST.get('self_rating', 'NEEDS_PRACTICE')
    time_spent = int(request.POST.get('time_spent', 0))

    # Save attempt
    PracticeAttempt.objects.create(
        session=practice_session,
        question=question,
        user_answer=user_answer,
        self_rating=self_rating,
        time_spent_seconds=time_spent
    )

    # Advance queue index
    current_index = request.session.get(f'practice_{practice_session.id}_index', 0)
    request.session[f'practice_{practice_session.id}_index'] = current_index + 1

    return redirect('practice_session', session_id=practice_session.id)


@login_required
def practice_results_view(request, session_id):
    """
    Scoring & Attempt Summary:
    Calculates final recitation grade, lists mastered vs weak questions, and allows retry.
    """
    practice_session = get_object_or_404(PracticeSession, id=session_id, user=request.user)
    practice_session.calculate_score()

    attempts = practice_session.attempts.select_related('question').all()
    total_time = sum(a.time_spent_seconds for a in attempts)
    avg_time = round(total_time / attempts.count(), 1) if attempts.count() > 0 else 0

    context = {
        'session': practice_session,
        'attempts': attempts,
        'total_time': total_time,
        'avg_time': avg_time,
    }
    return render(request, 'recitations/practice_results.html', context)


# ==========================================
# PERFORMANCE ANALYTICS & DASHBOARD
# ==========================================

@login_required
def analytics_dashboard_view(request):
    """
    Performance Analytics: Tracks user scores, attempt history, mastery rate,
    and identifies weak questions to revisit.
    """
    sessions = PracticeSession.objects.filter(user=request.user, status='COMPLETED')
    total_sessions = sessions.count()

    total_attempts = PracticeAttempt.objects.filter(session__user=request.user)
    total_questions_attempted = total_attempts.count()

    mastered_count = total_attempts.filter(self_rating='MASTERED').count()
    partial_count = total_attempts.filter(self_rating='PARTIAL').count()
    needs_practice_count = total_attempts.filter(self_rating='NEEDS_PRACTICE').count()

    avg_score = sessions.aggregate(Avg('score_percentage'))['score_percentage__avg'] or 0.0

    # Weak areas: Questions that received 'NEEDS_PRACTICE'
    weak_attempts = (
        PracticeAttempt.objects.filter(session__user=request.user, self_rating='NEEDS_PRACTICE')
        .values('question__id', 'question__prompt', 'question__difficulty', 'question__deck__title', 'question__deck__id')
        .annotate(fail_count=Count('id'))
        .order_by('-fail_count')[:5]
    )

    recent_history = sessions.select_related('deck').order_by('-completed_at')[:10]

    context = {
        'total_sessions': total_sessions,
        'total_questions_attempted': total_questions_attempted,
        'mastered_count': mastered_count,
        'partial_count': partial_count,
        'needs_practice_count': needs_practice_count,
        'avg_score': round(avg_score, 1),
        'readiness_score': min(100, int(avg_score * 1.05)) if avg_score > 0 else 0,
        'weak_questions': weak_attempts,
        'recent_history': recent_history,
    }
    return render(request, 'recitations/analytics_dashboard.html', context)


# ==========================================
# NOTIFICATIONS & PRACTICE REMINDERS
# ==========================================

@login_required
def reminders_view(request):
    """
    Notifications: Configure practice reminders and manage notification alerts.
    """
    if request.method == 'POST':
        if 'create_reminder' in request.POST:
            form = PracticeReminderForm(request.POST)
            if form.is_valid():
                reminder = form.save(commit=False)
                reminder.user = request.user
                reminder.save()
                messages.success(request, f'Practice reminder "{reminder.title}" set for {reminder.reminder_time}!')
                return redirect('reminders')
        elif 'toggle_reminder' in request.POST:
            reminder_id = request.POST.get('reminder_id')
            reminder = get_object_or_404(PracticeReminder, id=reminder_id, user=request.user)
            reminder.is_active = not reminder.is_active
            reminder.save()
            status_text = "activated" if reminder.is_active else "paused"
            messages.info(request, f'Reminder "{reminder.title}" has been {status_text}.')
            return redirect('reminders')
        elif 'delete_reminder' in request.POST:
            reminder_id = request.POST.get('reminder_id')
            reminder = get_object_or_404(PracticeReminder, id=reminder_id, user=request.user)
            reminder.delete()
            messages.success(request, 'Practice reminder deleted.')
            return redirect('reminders')
        elif 'send_test_notification' in request.POST:
            Notification.objects.create(
                user=request.user,
                title="Time for your Recitation Drill!",
                message="Consistent practice builds confidence. Take 5 minutes to test yourself on a question deck.",
                notification_type='REMINDER'
            )
            messages.success(request, 'Test notification sent to your notification center!')
            return redirect('reminders')
        elif 'mark_read' in request.POST:
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            messages.info(request, 'All notifications marked as read.')
            return redirect('reminders')

    form = PracticeReminderForm()
    reminders = PracticeReminder.objects.filter(user=request.user)
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:15]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        'form': form,
        'reminders': reminders,
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'recitations/reminders.html', context)
