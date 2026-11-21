from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import UserRegistrationForm, UserLoginForm, UserProfileUpdateForm
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
    - Upcoming recitation schedules and prompts
    - Metrics: Completed Recitations, Upcoming Sessions, Overall Average, Readiness Score
    - Performance history and teacher feedback
    """
    context = {
        'role_title': 'Student Portal',
        'stats': {
            'completed_recitations': 5,
            'upcoming_recitations': 1,
            'overall_grade': '91.2%',
            'readiness_score': '95%',
        },
        'next_recitation': {
            'title': 'Database Normalization & 3NF Defense',
            'course': 'IM2 - Information Management 2',
            'instructor': 'Prof. Dela Cruz',
            'scheduled_time': 'Today, 2:00 PM - 3:30 PM',
            'room': 'Lab 402 / Online Portal',
            'guidelines': 'Be prepared to explain 1NF, 2NF, 3NF with real-world anomalies.',
        },
        'recitation_history': [
            {
                'title': 'Relational Schema Design',
                'course': 'IM2',
                'score': '92/100',
                'feedback': 'Excellent explanation of primary and foreign keys.',
                'date': 'Nov 12, 2026',
            },
            {
                'title': 'SQL DDL & DML Commands',
                'course': 'IM2',
                'score': '88/100',
                'feedback': 'Good grasp of constraints, clarify subquery logic.',
                'date': 'Nov 05, 2026',
            },
            {
                'title': 'ER Modeling & Cardinality',
                'course': 'IM2',
                'score': '94/100',
                'feedback': 'Clear diagrams and great confidence during defense.',
                'date': 'Oct 28, 2026',
            },
        ]
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
