from django.contrib import admin
from .models import Deck, Question, PracticeSession, PracticeAttempt, PracticeReminder, Notification


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'subject', 'is_public', 'share_code', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['title', 'subject', 'share_code', 'owner__username']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['prompt_preview', 'deck', 'difficulty', 'tags', 'created_at']
    list_filter = ['difficulty', 'deck']
    search_fields = ['prompt', 'expected_answer', 'tags']

    def prompt_preview(self, obj):
        return obj.prompt[:75]


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'deck', 'status', 'score_percentage', 'time_limit_per_question', 'started_at']
    list_filter = ['status', 'started_at']
    search_fields = ['user__username', 'deck__title']


@admin.register(PracticeAttempt)
class PracticeAttemptAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'question', 'self_rating', 'time_spent_seconds']
    list_filter = ['self_rating']


@admin.register(PracticeReminder)
class PracticeReminderAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'reminder_time', 'days_of_week', 'is_active']
    list_filter = ['is_active']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
