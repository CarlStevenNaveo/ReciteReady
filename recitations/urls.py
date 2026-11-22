from django.urls import path
from . import views

urlpatterns = [
    # Deck Management (Question Bank & Deck Sharing)
    path('decks/', views.deck_list_view, name='deck_list'),
    path('decks/create/', views.deck_create_view, name='deck_create'),
    path('decks/join/', views.deck_join_view, name='deck_join'),
    path('decks/<int:deck_id>/', views.deck_detail_view, name='deck_detail'),
    path('decks/<int:deck_id>/edit/', views.deck_edit_view, name='deck_edit'),
    path('decks/<int:deck_id>/delete/', views.deck_delete_view, name='deck_delete'),
    path('decks/<int:deck_id>/clone/', views.deck_clone_view, name='deck_clone'),

    # Question Creation & Management
    path('decks/<int:deck_id>/questions/add/', views.question_create_view, name='question_create'),
    path('questions/<int:question_id>/edit/', views.question_edit_view, name='question_edit'),
    path('questions/<int:question_id>/delete/', views.question_delete_view, name='question_delete'),

    # Practice Management (Random Practice & Scoring)
    path('decks/<int:deck_id>/practice/', views.practice_setup_view, name='practice_setup'),
    path('practice/<int:session_id>/', views.practice_session_view, name='practice_session'),
    path('practice/<int:session_id>/submit/', views.practice_submit_answer_view, name='practice_submit_answer'),
    path('practice/<int:session_id>/results/', views.practice_results_view, name='practice_results'),

    # Performance Analytics
    path('analytics/', views.analytics_dashboard_view, name='analytics_dashboard'),

    # Notifications & Practice Reminders
    path('reminders/', views.reminders_view, name='reminders'),
]
