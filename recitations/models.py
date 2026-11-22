import secrets
import string
from django.db import models
from django.conf import settings
from django.utils import timezone


def generate_unique_share_code():
    chars = string.ascii_uppercase + string.digits
    while True:
        code = 'RR-' + ''.join(secrets.choice(chars) for _ in range(6))
        if not Deck.objects.filter(share_code=code).exists():
            return code


class Deck(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='decks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=100, blank=True)
    is_public = models.BooleanField(
        default=False,
        help_text="If public, any registered student can view and practice this deck."
    )
    share_code = models.CharField(
        max_length=12,
        unique=True,
        db_index=True,
        default=generate_unique_share_code,
        help_text="Unique share code for classmates to join or import this deck."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.owner.username})"

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def easy_count(self):
        return self.questions.filter(difficulty='EASY').count()

    @property
    def medium_count(self):
        return self.questions.filter(difficulty='MEDIUM').count()

    @property
    def hard_count(self):
        return self.questions.filter(difficulty='HARD').count()


class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
    ]

    deck = models.ForeignKey(
        Deck,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    prompt = models.TextField(
        help_text="The recitation prompt, question, or problem to answer."
    )
    expected_answer = models.TextField(
        help_text="Key points, formula, explanation, or ideal response for self-evaluation."
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='MEDIUM'
    )
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated keywords or topics (e.g. Normalization, 3NF, ERD)."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"[{self.difficulty}] {self.prompt[:60]}"

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]


class PracticeSession(models.Model):
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ABANDONED', 'Abandoned'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='practice_sessions'
    )
    deck = models.ForeignKey(
        Deck,
        on_delete=models.CASCADE,
        related_name='practice_sessions'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='IN_PROGRESS'
    )
    time_limit_per_question = models.IntegerField(
        default=60,
        help_text="Time limit in seconds per question (0 for untimed)."
    )
    difficulty_filter = models.CharField(
        max_length=10,
        blank=True,
        default='ALL'
    )
    total_questions = models.IntegerField(default=0)
    completed_questions = models.IntegerField(default=0)
    mastered_count = models.IntegerField(default=0)
    partial_count = models.IntegerField(default=0)
    needs_practice_count = models.IntegerField(default=0)
    score_percentage = models.FloatField(default=0.0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Session #{self.id} - {self.user.username} on {self.deck.title} ({self.status})"

    def calculate_score(self):
        attempts = self.attempts.all()
        if not attempts.exists():
            self.score_percentage = 0.0
            self.save(update_fields=['score_percentage'])
            return 0.0

        total_pts = 0.0
        max_pts = attempts.count() * 1.0
        m_count = 0
        p_count = 0
        np_count = 0

        for att in attempts:
            if att.self_rating == 'MASTERED':
                total_pts += 1.0
                m_count += 1
            elif att.self_rating == 'PARTIAL':
                total_pts += 0.5
                p_count += 1
            else:
                np_count += 1

        self.mastered_count = m_count
        self.partial_count = p_count
        self.needs_practice_count = np_count
        self.completed_questions = attempts.count()
        self.score_percentage = round((total_pts / max_pts) * 100, 1) if max_pts > 0 else 0.0
        self.save(update_fields=[
            'mastered_count', 'partial_count', 'needs_practice_count',
            'completed_questions', 'score_percentage'
        ])
        return self.score_percentage


class PracticeAttempt(models.Model):
    RATING_CHOICES = [
        ('MASTERED', 'Mastered / Correct'),
        ('PARTIAL', 'Partially Correct'),
        ('NEEDS_PRACTICE', 'Needs Practice'),
        ('SKIPPED', 'Skipped'),
    ]

    session = models.ForeignKey(
        PracticeSession,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    user_answer = models.TextField(
        blank=True,
        help_text="Spoken / transcribed or typed response during practice"
    )
    self_rating = models.CharField(
        max_length=20,
        choices=RATING_CHOICES,
        default='NEEDS_PRACTICE'
    )
    time_spent_seconds = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Attempt on Q#{self.question.id}: {self.self_rating}"


class PracticeReminder(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    title = models.CharField(max_length=150, default="Daily Recitation Drill")
    reminder_time = models.TimeField()
    days_of_week = models.CharField(
        max_length=150,
        default="Mon, Wed, Fri",
        help_text="Days when reminder is active (e.g. Daily, Mon, Wed, Fri)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['reminder_time']

    def __str__(self):
        return f"{self.title} at {self.reminder_time} ({self.user.username})"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('REMINDER', 'Practice Reminder'),
        ('ACHIEVEMENT', 'Achievement'),
        ('SYSTEM', 'System Alert'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='REMINDER'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} for {self.user.username}"
