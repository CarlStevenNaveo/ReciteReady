from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class AccountFeatureTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Instructor account
        self.instructor = User.objects.create_user(
            username='instructor_jane',
            email='jane.instructor@example.com',
            password='Password123#Secure',
            role='INSTRUCTOR',
            first_name='Jane',
            last_name='Doe',
            contact_number='+63 912 345 6789'
        )

        # Student account
        self.student = User.objects.create_user(
            username='student_juan',
            email='juan.student@example.com',
            password='Password123#Secure',
            role='STUDENT',
            first_name='Juan',
            last_name='Dela Cruz',
            contact_number='+63 998 765 4321'
        )

    # =========================================================================
    # 1. REGISTRATION TESTS
    # =========================================================================

    def test_registration_success_hashes_password(self):
        """Users can register with valid fields; passwords must be securely hashed."""
        response = self.client.post(reverse('register'), {
            'username': 'new_student',
            'email': 'new_student@example.com',
            'role': 'STUDENT',
            'first_name': 'New',
            'last_name': 'Student',
            'contact_number': '+63 911 222 3333',
            'password': 'Password123#Secure',
            'confirm_password': 'Password123#Secure',
        })
        self.assertRedirects(response, reverse('login'))

        new_user = User.objects.get(username='new_student')
        self.assertEqual(new_user.email, 'new_student@example.com')
        self.assertEqual(new_user.role, 'STUDENT')
        # Crucial check: password must not be stored in plain text
        self.assertNotEqual(new_user.password, 'Password123#Secure')
        self.assertTrue(new_user.check_password('Password123#Secure'))

    def test_registration_duplicate_username_fails(self):
        """Duplicate username must be rejected with validation error."""
        response = self.client.post(reverse('register'), {
            'username': 'student_juan',  # Already exists
            'email': 'another_email@example.com',
            'role': 'STUDENT',
            'password': 'Password123#Secure',
            'confirm_password': 'Password123#Secure',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('This username is already taken. Please choose another.', response.context['form'].errors['username'])

    def test_registration_duplicate_email_fails(self):
        """Duplicate email must be rejected with validation error."""
        response = self.client.post(reverse('register'), {
            'username': 'unique_user_99',
            'email': 'juan.student@example.com',  # Already exists
            'role': 'STUDENT',
            'password': 'Password123#Secure',
            'confirm_password': 'Password123#Secure',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('An account with this email address already exists.', response.context['form'].errors['email'])

    def test_registration_password_mismatch_fails(self):
        """Mismatched password confirmation must fail."""
        response = self.client.post(reverse('register'), {
            'username': 'mismatch_user',
            'email': 'mismatch@example.com',
            'role': 'STUDENT',
            'password': 'Password123#Secure',
            'confirm_password': 'CompletelyDifferentPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Passwords do not match.', response.context['form'].errors['confirm_password'])

    # =========================================================================
    # 2. LOGIN / LOGOUT TESTS
    # =========================================================================

    def test_login_with_username_success(self):
        """User can log in using their username."""
        response = self.client.post(reverse('login'), {
            'username_or_email': 'student_juan',
            'password': 'Password123#Secure',
        })
        self.assertRedirects(response, reverse('role_dashboard'), target_status_code=302)

    def test_login_with_email_success(self):
        """User can log in using their registered email address."""
        response = self.client.post(reverse('login'), {
            'username_or_email': 'jane.instructor@example.com',
            'password': 'Password123#Secure',
        })
        self.assertRedirects(response, reverse('role_dashboard'), target_status_code=302)

    def test_login_invalid_credentials_fails(self):
        """Invalid credentials show error and re-render login page."""
        response = self.client.post(reverse('login'), {
            'username_or_email': 'student_juan',
            'password': 'WrongPassword123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username/email or password.")

    def test_logout_ends_session(self):
        """Logging out ends user session and redirects to login."""
        self.client.login(username='student_juan', password='Password123#Secure')
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        # Ensure session is cleared
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_protected_pages_redirect_unauthenticated_users(self):
        """Unauthenticated requests to protected pages redirect to login."""
        protected_urls = [
            reverse('role_dashboard'),
            reverse('instructor_dashboard'),
            reverse('student_dashboard'),
            reverse('profile'),
            reverse('profile_edit'),
        ]
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(reverse('login')))

    # =========================================================================
    # 3. ROLE-BASED DASHBOARDS & ACCESS CONTROL TESTS
    # =========================================================================

    def test_role_dashboard_routes_instructor(self):
        """Logging in as Instructor redirects to Instructor Dashboard."""
        self.client.login(username='instructor_jane', password='Password123#Secure')
        response = self.client.get(reverse('role_dashboard'))
        self.assertRedirects(response, reverse('instructor_dashboard'))

    def test_role_dashboard_routes_student(self):
        """Logging in as Student redirects to Student Dashboard."""
        self.client.login(username='student_juan', password='Password123#Secure')
        response = self.client.get(reverse('role_dashboard'))
        self.assertRedirects(response, reverse('student_dashboard'))

    def test_student_cannot_access_instructor_dashboard_by_url(self):
        """A Student cannot access the Instructor dashboard by typing its URL."""
        self.client.login(username='student_juan', password='Password123#Secure')
        response = self.client.get(reverse('instructor_dashboard'))
        # Must redirect student back to student dashboard with access denied error
        self.assertRedirects(response, reverse('student_dashboard'))

    def test_instructor_cannot_access_student_dashboard_by_url(self):
        """An Instructor cannot access the Student dashboard by typing its URL."""
        self.client.login(username='instructor_jane', password='Password123#Secure')
        response = self.client.get(reverse('student_dashboard'))
        # Must redirect instructor back to instructor dashboard
        self.assertRedirects(response, reverse('instructor_dashboard'))

    # =========================================================================
    # 4. USER PROFILE TESTS
    # =========================================================================

    def test_user_can_view_own_profile(self):
        """Logged-in user can view their own profile details."""
        self.client.login(username='student_juan', password='Password123#Secure')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'student_juan')
        self.assertContains(response, 'juan.student@example.com')
        self.assertContains(response, 'Juan Dela Cruz')

    def test_user_can_update_own_profile(self):
        """Logged-in user can update their own profile details."""
        self.client.login(username='student_juan', password='Password123#Secure')
        response = self.client.post(reverse('profile_edit'), {
            'first_name': 'Juanito',
            'last_name': 'Dela Cruz Jr.',
            'email': 'juanito.updated@example.com',
            'contact_number': '+63 900 111 2222',
        })
        self.assertRedirects(response, reverse('profile'))

        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'Juanito')
        self.assertEqual(self.student.last_name, 'Dela Cruz Jr.')
        self.assertEqual(self.student.email, 'juanito.updated@example.com')
        self.assertEqual(self.student.contact_number, '+63 900 111 2222')

    def test_profile_update_duplicate_email_fails(self):
        """Updating email to one already registered by another user fails."""
        self.client.login(username='student_juan', password='Password123#Secure')
        response = self.client.post(reverse('profile_edit'), {
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'email': 'jane.instructor@example.com',  # Jane's email
            'contact_number': '+63 998 765 4321',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('An account with this email address already exists.', response.context['form'].errors['email'])
