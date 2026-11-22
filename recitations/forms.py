from django import forms
from .models import Deck, Question, PracticeReminder


class DeckForm(forms.ModelForm):
    class Meta:
        model = Deck
        fields = ['title', 'subject', 'description', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Information Management 2 - Normalization & SQL'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Database Systems / Software Engineering'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of what recitation questions are covered in this deck...'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['prompt', 'expected_answer', 'difficulty', 'tags']
        widgets = {
            'prompt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter the oral recitation prompt or question that the instructor might ask...'
            }),
            'expected_answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detail the expected answer, key formulas, bullet points, or grading criteria...'
            }),
            'difficulty': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 1NF, 2NF, 3NF, BCNF, Relational Anomalies (comma separated)'
            }),
        }


class JoinDeckForm(forms.Form):
    share_code = forms.CharField(
        max_length=15,
        label="Deck Share Code",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-uppercase font-monospace text-center',
            'placeholder': 'RR-XXXXXX'
        }),
        help_text="Ask your classmate or instructor for their 8-character deck share code."
    )

    def clean_share_code(self):
        code = self.cleaned_data.get('share_code', '').strip().upper()
        if not Deck.objects.filter(share_code=code).exists():
            raise forms.ValidationError("No recitation deck found with this share code.")
        return code


class PracticeSetupForm(forms.Form):
    DIFFICULTY_CHOICES = [
        ('ALL', 'All Difficulties (Mixed)'),
        ('EASY', 'Easy Only'),
        ('MEDIUM', 'Medium Only'),
        ('HARD', 'Hard Only'),
    ]

    TIMER_CHOICES = [
        (30, '30 Seconds (Fast Recall)'),
        (45, '45 Seconds (Standard Recitation)'),
        (60, '60 Seconds (Detailed Defense)'),
        (90, '90 Seconds (Deep Explanation)'),
        (120, '2 Minutes (Extended Response)'),
        (0, 'Untimed (Self-Paced Practice)'),
    ]

    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        required=False,
        initial='ALL',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    time_limit = forms.IntegerField(
        widget=forms.Select(choices=TIMER_CHOICES, attrs={'class': 'form-select'}),
        initial=45,
        label="Time Limit per Question"
    )
    question_count = forms.IntegerField(
        min_value=1,
        initial=10,
        label="Number of Questions",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 50})
    )
    randomize = forms.BooleanField(
        required=False,
        initial=True,
        label="Randomize Question Order",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class PracticeReminderForm(forms.ModelForm):
    class Meta:
        model = PracticeReminder
        fields = ['title', 'reminder_time', 'days_of_week', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Evening Recitation Drill'
            }),
            'reminder_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'days_of_week': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Mon, Wed, Fri or Daily'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
