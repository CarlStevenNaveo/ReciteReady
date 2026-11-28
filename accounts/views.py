from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import UserRegistrationForm, UserLoginForm, UserProfileUpdateForm, CustomPasswordChangeForm
from .decorators import role_required


def landing_page_view(request):
    """
    Public landing page for ReciteReady.
    If the user is already authenticated, redirect directly to their dashboard.
    """
    if request.user.is_authenticated:
        return redirect('role_dashboard')
    return render(request, 'home.html')


def register_view(request):
    """
    Handles user registration with comprehensive validation:
    - Unique username & email
    - Password hashing and strength validation
    - Password confirmation matching
    - Role selection (Student or Instructor)
    """
    if request.user.is_authenticated:
        return redirect('role_dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Account successfully created for {user.username}! You can now sign in."
            )
            return redirect('login')
        else:
            messages.error(request, "Registration failed. Please check the errors below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    Authenticates registered users via either username or email.
    Provides clear error messages on failure and session redirection on success.
    """
    if request.user.is_authenticated:
        return redirect('role_dashboard')

    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = UserLoginForm(request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(
                request,
                f"Welcome back, {user.first_name or user.username}! "
                f"Logged in as {user.get_role_display()}."
            )

            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}
            ):
                return redirect(next_url)

            return redirect('role_dashboard')
        else:
            messages.error(request, "Invalid username/email or password.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'next': next_url,
    })


def logout_view(request):
    """
    Ends the user's session and redirects to the login page with a success message.
    """
    if request.user.is_authenticated:
        auth_logout(request)
        messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def role_dashboard_view(request):
    """
    Central dispatcher that routes authenticated users to their specific dashboard
    based on their assigned role.
    """
    if request.user.role == 'INSTRUCTOR':
        return redirect('instructor_dashboard')
    elif request.user.role == 'STUDENT':
        return redirect('student_dashboard')
    return redirect('student_dashboard')


@login_required
@role_required(['INSTRUCTOR'])
def instructor_dashboard_view(request):
    """
    Role-specific dashboard for Instructors:
    - Overview of classes and recitation sessions
    - Metrics: Total Students, Active Sessions, Pending Evaluations, Class Average
    - Quick actions for managing recitations and rubric grading
    """
    context = {
        'role_title': 'Instructor Portal',
        'stats': {
            'total_students': 48,
            'active_sessions': 3,
            'pending_evaluations': 7,
            'class_average': '88.5%',
        },
        'upcoming_sessions': [
            {
                'title': 'Database Normalization & 3NF Defense',
                'section': 'CS301 - Section A',
                'date': 'Today, 2:00 PM',
                'students_count': 24,
                'status': 'In Progress',
            },
            {
                'title': 'Object-Oriented Design Patterns',
                'section': 'CS202 - Section B',
                'date': 'Tomorrow, 10:00 AM',
                'students_count': 22,
                'status': 'Scheduled',
            },
            {
                'title': 'Software Architecture & Microservices',
                'section': 'CS401 - Section A',
                'date': 'Friday, 1:30 PM',
                'students_count': 18,
                'status': 'Draft',
            },
        ],
        'recent_recitations': [
            {'student': 'John Smith', 'topic': 'B-Tree Indexing', 'score': '95/100', 'status': 'Graded'},
            {'student': 'Emily Davis', 'topic': 'Relational Algebra', 'score': '88/100', 'status': 'Graded'},
            {'student': 'Mark Wilson', 'topic': 'ACID Properties', 'score': 'Pending', 'status': 'Needs Review'},
        ]
    }
    return render(request, 'accounts/instructor_dashboard.html', context)


@login_required
@role_required(['STUDENT'])
def student_dashboard_view(request):
    """
    Role-specific dashboard for Students:
    - Real-time metrics: Completed Defenses, Decks Available, Overall Average, Readiness Score
    - Spotlight: Active/Next Recitation Deck to practice
    - Recitation attempt history with scores and timestamps
    """
    from recitations.models import PracticeSession, Deck
    from django.db.models import Avg

    user_sessions = PracticeSession.objects.filter(user=request.user, status='COMPLETED')
    completed_recitations = user_sessions.count()
    avg_score = user_sessions.aggregate(Avg('score_percentage'))['score_percentage__avg'] or 0.0

    user_decks = Deck.objects.filter(owner=request.user)
    total_decks = user_decks.count() + Deck.objects.filter(is_public=True).exclude(owner=request.user).count()
    readiness_score = min(100, int(avg_score * 1.05)) if avg_score > 0 else 0

    recent_sessions = user_sessions.select_related('deck').order_by('-completed_at')[:4]
    latest_deck = user_decks.first() or Deck.objects.filter(is_public=True).first()

    context = {
        'role_title': 'Student Portal',
        'stats': {
            'completed_recitations': completed_recitations,
            'upcoming_recitations': total_decks,
            'overall_grade': f"{round(avg_score, 1)}%",
            'readiness_score': f"{readiness_score}%",
            'readiness_num': readiness_score,
            'readiness_offset': round(314 - (314 * readiness_score / 100), 1),
        },
        'latest_deck': latest_deck,
        'recent_sessions': recent_sessions,
        'has_activity': completed_recitations > 0,
    }
    return render(request, 'accounts/student_dashboard.html', context)


@login_required
def profile_view(request):
    """
    Enables logged-in users to view their own profile.
    Strictly isolated: users can only view their own user account details.
    """
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })


@login_required
def profile_edit_view(request):
    """
    Enables logged-in users to update their profile information.
    Strictly isolated: users can only edit their own account details (instance=request.user).
    """
    if request.method == 'POST':
        form = UserProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Failed to update profile. Please check the errors below.")
    else:
        form = UserProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/profile_edit.html', {
        'form': form
    })


@login_required
def account_settings_view(request):
    """
    Account Management: View account settings, change password, and account options.
    """
    password_form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'accounts/account_settings.html', {
        'password_form': password_form,
    })


@login_required
def change_password_view(request):
    """
    Account Management: Handles password update securely.
    """
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been changed successfully!")
            return redirect('account_settings')
        else:
            messages.error(request, "Please correct the errors in the password form.")
            return render(request, 'accounts/account_settings.html', {'password_form': form})
    return redirect('account_settings')


@login_required
def deactivate_account_view(request):
    """
    Account Management: Deactivates student account upon confirmation.
    """
    if request.method == 'POST':
        user = request.user
        user.is_active = False
        user.save()
        auth_logout(request)
        messages.info(request, "Your account has been deactivated. Contact administration if you wish to reactivate.")
        return redirect('home')
    return render(request, 'accounts/account_deactivate_confirm.html')
