from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Deck, Question, PracticeSession, PracticeAttempt, PracticeReminder, Notification

User = get_user_model()


class RecitationFeaturesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='carl_student',
            email='carl@example.com',
            password='TestPassword123!',
            role='STUDENT',
            first_name='Carl',
            last_name='Naveo'
        )
        self.other_user = User.objects.create_user(
            username='jane_student',
            email='jane@example.com',
            password='TestPassword123!',
            role='STUDENT'
        )
        self.client.force_login(self.user)

        # Create sample deck
        self.deck = Deck.objects.create(
            owner=self.user,
            title='IM2 Oral Recitation',
            subject='Information Management',
            description='Normalization, SQL, and Transactions',
            is_public=True
        )

        # Create sample questions with difficulties
        self.q_easy = Question.objects.create(
            deck=self.deck,
            prompt='What is 1NF?',
            expected_answer='Each column contains atomic values and no repeating groups.',
            difficulty='EASY',
            tags='Normalization, 1NF'
        )
        self.q_med = Question.objects.create(
            deck=self.deck,
            prompt='Explain the difference between 2NF and 3NF.',
            expected_answer='2NF removes partial dependencies; 3NF removes transitive dependencies.',
            difficulty='MEDIUM',
            tags='Normalization, 2NF, 3NF'
        )
        self.q_hard = Question.objects.create(
            deck=self.deck,
            prompt='What is BCNF and how does it differ from 3NF?',
            expected_answer='In BCNF, every determinant must be a candidate key.',
            difficulty='HARD',
            tags='BCNF, Keys'
        )

    def test_deck_creation_and_unique_share_code(self):
        """Decks must automatically generate a unique RR-XXXXXX share code."""
        self.assertTrue(self.deck.share_code.startswith('RR-'))
        self.assertEqual(len(self.deck.share_code), 9)
        self.assertEqual(self.deck.question_count, 3)
        self.assertEqual(self.deck.easy_count, 1)
        self.assertEqual(self.deck.medium_count, 1)
        self.assertEqual(self.deck.hard_count, 1)

    def test_deck_list_view(self):
        """Deck list should display user decks."""
        response = self.client.get(reverse('deck_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'IM2 Oral Recitation')

    def test_deck_join_by_share_code(self):
        """Students can find and access decks using share codes."""
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('deck_join'), {
            'share_code': self.deck.share_code
        })
        self.assertRedirects(response, reverse('deck_detail', args=[self.deck.id]))

    def test_deck_cloning(self):
        """Students can clone public decks to their personal library."""
        self.client.force_login(self.other_user)
        response = self.client.get(reverse('deck_clone', args=[self.deck.id]))
        self.assertEqual(response.status_code, 302)
        cloned_decks = Deck.objects.filter(owner=self.other_user)
        self.assertEqual(cloned_decks.count(), 1)
        self.assertEqual(cloned_decks.first().question_count, 3)

    def test_randomized_practice_session_flow(self):
        """Randomized practice session initializes, questions queue, and scores."""
        # 1. Start setup
        response = self.client.post(reverse('practice_setup', args=[self.deck.id]), {
            'difficulty': 'ALL',
            'time_limit': 45,
            'question_count': 3,
            'randomize': True,
        })
        self.assertEqual(response.status_code, 302)
        session = PracticeSession.objects.filter(user=self.user, deck=self.deck).first()
        self.assertIsNotNone(session)
        self.assertEqual(session.status, 'IN_PROGRESS')
        self.assertEqual(session.total_questions, 3)

        # 2. View session
        session_url = reverse('practice_session', args=[session.id])
        resp_session = self.client.get(session_url)
        self.assertEqual(resp_session.status_code, 200)
        self.assertContains(resp_session, 'Question 1 of 3')

        # 3. Submit first answer with Mastered rating
        submit_url = reverse('practice_submit_answer', args=[session.id])
        self.client.post(submit_url, {
            'question_id': self.q_easy.id,
            'user_answer': 'Atomic values only',
            'self_rating': 'MASTERED',
            'time_spent': 15,
        })
        self.assertEqual(session.attempts.count(), 1)

        # 4. Submit second answer with Partial rating
        self.client.post(submit_url, {
            'question_id': self.q_med.id,
            'user_answer': '2NF partial dependency, 3NF transitive',
            'self_rating': 'PARTIAL',
            'time_spent': 20,
        })

        # 5. Submit third answer with Needs Practice rating
        self.client.post(submit_url, {
            'question_id': self.q_hard.id,
            'user_answer': 'Not sure',
            'self_rating': 'NEEDS_PRACTICE',
            'time_spent': 30,
        })

        # 6. Session completion and scoring
        resp_completed = self.client.get(session_url)
        self.assertRedirects(resp_completed, reverse('practice_results', args=[session.id]))

        session.refresh_from_db()
        self.assertEqual(session.status, 'COMPLETED')
        self.assertEqual(session.mastered_count, 1)
        self.assertEqual(session.partial_count, 1)
        self.assertEqual(session.needs_practice_count, 1)
        # Score: (1.0 + 0.5 + 0.0) / 3 = 1.5 / 3 = 50.0%
        self.assertEqual(session.score_percentage, 50.0)

    def test_analytics_dashboard_view(self):
        """Analytics page displays aggregate performance metrics."""
        response = self.client.get(reverse('analytics_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Performance Tracking')

    def test_practice_reminders_and_notifications(self):
        """Students can set practice reminder schedules and trigger notifications."""
        # Create reminder
        resp = self.client.post(reverse('reminders'), {
            'create_reminder': '1',
            'title': 'Nightly Drill',
            'reminder_time': '20:00',
            'days_of_week': 'Daily',
            'is_active': True,
        })
        self.assertRedirects(resp, reverse('reminders'))
        self.assertEqual(PracticeReminder.objects.filter(user=self.user).count(), 1)

        # Trigger test notification
        self.client.post(reverse('reminders'), {'send_test_notification': '1'})
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 1)

    def test_account_settings_and_password_change(self):
        """Account Management provides settings and password change."""
        resp = self.client.get(reverse('account_settings'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Account Management')

        # Change password
        pwd_resp = self.client.post(reverse('change_password'), {
            'old_password': 'TestPassword123!',
            'new_password1': 'NewSecurePassword456#',
            'new_password2': 'NewSecurePassword456#',
        })
        self.assertRedirects(pwd_resp, reverse('account_settings'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePassword456#'))

    def test_instructor_dashboard_live_data_and_role_access(self):
        """Instructor dashboard displays live DB stats and instructors can review student attempts."""
        instructor = User.objects.create_user(
            username='prof_recite',
            email='prof@example.com',
            password='TestPassword123!',
            role='INSTRUCTOR',
            first_name='Maria',
            last_name='Santos'
        )
        session = PracticeSession.objects.create(
            user=self.user,
            deck=self.deck,
            status='COMPLETED',
            total_questions=1,
            completed_questions=1,
            mastered_count=1,
            score_percentage=100.0
        )
        PracticeAttempt.objects.create(
            session=session,
            question=self.q_easy,
            user_answer='Atomic values',
            self_rating='MASTERED',
            time_spent_seconds=12
        )

        # Instructor can view live dashboard and inspect student's practice results
        self.client.force_login(instructor)
        dash_resp = self.client.get(reverse('instructor_dashboard'))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertContains(dash_resp, 'Carl Naveo')
        self.assertContains(dash_resp, '100%')

        results_resp = self.client.get(reverse('practice_results', args=[session.id]))
        self.assertEqual(results_resp.status_code, 200)

        # Another student cannot view Carl's private practice results
        self.client.force_login(self.other_user)
        blocked_resp = self.client.get(reverse('practice_results', args=[session.id]))
        self.assertEqual(blocked_resp.status_code, 404)
