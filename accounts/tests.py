"""
AlumniPortal — Accounts Test Suite
Covers: registration, OTP verification, login (user + admin),
        profile completion enforcement, dashboard access, edit profile.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from unittest.mock import patch, MagicMock
from .models import CustomUser, AdminProfile, EmailOTP


# ─── helpers ────────────────────────────────────────────────────────────────

def make_active_user(email='user@example.com', password='Pass1234!',
                     full_name='Test User', **kwargs):
    u = CustomUser.objects.create_user(
        email=email, password=password, full_name=full_name, **kwargs)
    u.is_active = True
    u.save()
    return u


def make_complete_user(**kwargs):
    defaults = dict(
        email='complete@example.com', password='Pass1234!',
        full_name='Complete User',
        current_company='Infosys', designation='Developer',
        domain='Web', city='Chennai', experience_years='3',
    )
    defaults.update(kwargs)
    return make_active_user(**defaults)


def make_admin(username='admin', code='admin123'):
    u = CustomUser.objects.create_user(
        email=f'{username}@admin.local', password='irrelevant',
        full_name='Admin', is_admin_user=True, is_active=True,
        username=username,
    )
    AdminProfile.objects.create(user=u, access_code=code)
    return u


# ─── Registration ────────────────────────────────────────────────────────────

class UserRegistrationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('user_register')

    def _post(self, **override):
        data = {
            'full_name': 'Rose Tamil',
            'email': 'rose@example.com',
            'mobile': '9876543210',
            'password': 'Strong@123',
            'confirm_password': 'Strong@123',
            'batch': '2022',
            'institute': 'SSS',
        }
        data.update(override)
        return self.client.post(self.url, data)

    def test_register_page_loads(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Create Account')

    def test_city_field_not_on_register_page(self):
        r = self.client.get(self.url)
        # city was removed from registration form
        self.assertNotContains(r, 'id="id_city"')

    @patch('accounts.views.send_otp_email')
    def test_successful_registration_creates_inactive_user(self, mock_otp):
        r = self._post()
        self.assertEqual(r.status_code, 302)
        self.assertRedirects(r, reverse('verify_otp'))
        user = CustomUser.objects.get(email='rose@example.com')
        self.assertFalse(user.is_active)
        mock_otp.assert_called_once()

    def test_mismatched_passwords_rejected(self):
        r = self._post(confirm_password='Different1!')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(email='rose@example.com').exists())

    def test_duplicate_active_email_rejected(self):
        make_active_user(email='rose@example.com')
        r = self._post()
        self.assertContains(r, 'already exists')

    def test_disposable_email_rejected(self):
        r = self._post(email='test@mailinator.com')
        self.assertContains(r, 'disposable')

    def test_missing_required_fields(self):
        r = self.client.post(self.url, {'email': 'x@x.com'})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(email='x@x.com').exists())


# ─── OTP Verification ────────────────────────────────────────────────────────

class OTPVerificationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='otp@example.com', password='Pass1234!',
            full_name='OTP User', is_active=False)
        session = self.client.session
        session['pending_verification_user_id'] = self.user.id
        session.save()

    def _make_otp(self, code='123456', is_used=False):
        return EmailOTP.objects.create(user=self.user, code=code, is_used=is_used)

    def test_verify_page_loads(self):
        r = self.client.get(reverse('verify_otp'))
        self.assertEqual(r.status_code, 200)

    def test_correct_otp_activates_user_and_redirects_to_profile(self):
        self._make_otp('654321')
        r = self.client.post(reverse('verify_otp'), {'code': '654321'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertRedirects(r, reverse('edit_profile'))

    def test_wrong_otp_shows_error(self):
        self._make_otp('999999')
        r = self.client.post(reverse('verify_otp'), {'code': '111111'})
        self.assertContains(r, 'Incorrect')
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_used_otp_rejected(self):
        self._make_otp('777777', is_used=True)
        r = self.client.post(reverse('verify_otp'), {'code': '777777'})
        self.assertContains(r, 'No active code')

    def test_non_digit_otp_rejected(self):
        r = self.client.post(reverse('verify_otp'), {'code': 'abcdef'})
        self.assertContains(r, 'digit')

    def test_no_session_redirects_to_register(self):
        self.client.session.flush()
        r = self.client.get(reverse('verify_otp'))
        self.assertRedirects(r, reverse('user_register'))


# ─── User Login ──────────────────────────────────────────────────────────────

class UserLoginTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_complete_user(email='user@example.com', password='Pass1234!')
        self.url = reverse('user_login')

    def test_login_page_loads(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_correct_credentials_login_redirects_to_dashboard(self):
        r = self.client.post(self.url, {'username': 'user@example.com', 'password': 'Pass1234!'})
        self.assertRedirects(r, reverse('dashboard'))

    def test_wrong_password_shows_error(self):
        r = self.client.post(self.url, {'username': 'user@example.com', 'password': 'wrong'})
        self.assertContains(r, 'Invalid')

    def test_wrong_email_shows_error(self):
        r = self.client.post(self.url, {'username': 'nobody@x.com', 'password': 'Pass1234!'})
        self.assertContains(r, 'Invalid')

    @patch('accounts.views.send_otp_email')
    def test_unverified_user_triggers_otp_resend(self, mock_otp):
        u = CustomUser.objects.create_user(
            email='pending@example.com', password='Pass1234!',
            full_name='Pending', is_active=False)
        r = self.client.post(self.url, {'username': 'pending@example.com', 'password': 'Pass1234!'})
        self.assertRedirects(r, reverse('verify_otp'))
        mock_otp.assert_called_once()

    def test_admin_cannot_login_via_user_login(self):
        admin = make_admin()
        r = self.client.post(self.url, {'username': admin.email, 'password': 'irrelevant'})
        self.assertContains(r, 'Invalid')

    def test_authenticated_user_redirected_from_login_page(self):
        self.client.login(username='user@example.com', password='Pass1234!')
        r = self.client.get(self.url)
        self.assertRedirects(r, reverse('dashboard'))


# ─── Admin Login ─────────────────────────────────────────────────────────────

class AdminLoginTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('admin_login')

    def test_admin_login_page_loads(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_db_admin_login_succeeds(self):
        make_admin(username='dbadmin', code='secret')
        r = self.client.post(self.url, {'username': 'dbadmin', 'code': 'secret'})
        self.assertRedirects(r, reverse('admin_dashboard'))

    def test_wrong_code_rejected(self):
        make_admin(username='dbadmin', code='secret')
        r = self.client.post(self.url, {'username': 'dbadmin', 'code': 'wrong'})
        self.assertContains(r, 'Invalid')

    def test_env_admin_login_creates_user_and_succeeds(self):
        with self.settings(ADMIN_USERNAME='envadmin', ADMIN_ACCESS_CODE='envpass'):
            r = self.client.post(self.url, {'username': 'envadmin', 'code': 'envpass'})
            self.assertRedirects(r, reverse('admin_dashboard'))
            self.assertTrue(CustomUser.objects.filter(username='envadmin', is_admin_user=True).exists())

    def test_env_admin_wrong_code_rejected(self):
        with self.settings(ADMIN_USERNAME='envadmin', ADMIN_ACCESS_CODE='envpass'):
            r = self.client.post(self.url, {'username': 'envadmin', 'code': 'wrong'})
            self.assertContains(r, 'Invalid')


# ─── Dashboard & Profile Enforcement ─────────────────────────────────────────

class DashboardTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_unauthenticated_redirects_to_login(self):
        r = self.client.get(reverse('dashboard'))
        self.assertRedirects(r, f"{reverse('user_login')}?next={reverse('dashboard')}")

    def test_incomplete_profile_redirects_to_edit_profile(self):
        u = make_active_user(email='inc@x.com')  # no professional fields
        self.client.force_login(u)
        r = self.client.get(reverse('dashboard'))
        self.assertRedirects(r, reverse('edit_profile'))

    def test_complete_profile_shows_dashboard(self):
        u = make_complete_user(email='comp@x.com')
        self.client.force_login(u)
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Quick Actions')

    def test_admin_redirected_to_admin_dashboard(self):
        a = make_admin()
        self.client.force_login(a)
        r = self.client.get(reverse('dashboard'))
        self.assertRedirects(r, reverse('admin_dashboard'))


# ─── Edit Profile ────────────────────────────────────────────────────────────

class EditProfileTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_active_user()
        self.client.force_login(self.user)
        self.url = reverse('edit_profile')

    def test_profile_page_loads(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_completing_profile_redirects_to_dashboard(self):
        r = self.client.post(self.url, {
            'full_name': 'Rose Tamil',
            'email': 'user@example.com',
            'mobile': '9876543210',
            'batch': '2022',
            'institute': 'SSS',
            'current_company': 'TCS',
            'designation': 'Engineer',
            'domain': 'Python',
            'city': 'Chennai',
            'experience_years': '2',
            'salary': '5 LPA',
            'skills': 'Python,Django',
        })
        self.assertRedirects(r, reverse('dashboard'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.current_company, 'TCS')
        self.assertTrue(self.user.profile_complete)

    def test_missing_required_professional_field_shows_error(self):
        r = self.client.post(self.url, {
            'full_name': 'Rose Tamil',
            'email': 'user@example.com',
            'current_company': '',   # required — left blank
            'designation': 'Eng',
            'domain': 'Python',
            'city': 'Chennai',
            'experience_years': '2',
        })
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile_complete)

    def test_unauthenticated_redirects(self):
        self.client.logout()
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)


# ─── Admin Dashboard ─────────────────────────────────────────────────────────

class AdminDashboardTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_admin()
        self.regular_user = make_complete_user(email='reg@x.com')

    def test_admin_can_access_dashboard(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Admin Dashboard')

    def test_regular_user_cannot_access_admin_dashboard(self):
        self.client.force_login(self.regular_user)
        r = self.client.get(reverse('admin_dashboard'))
        self.assertRedirects(r, reverse('dashboard'))

    def test_unauthenticated_redirected(self):
        r = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(r.status_code, 302)

    def test_users_listed_in_admin_dashboard(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('admin_dashboard'))
        self.assertContains(r, self.regular_user.full_name)

    def test_admin_can_view_user_detail(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('user_detail', args=[self.regular_user.id]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.regular_user.full_name)

    def test_regular_user_cannot_view_user_detail(self):
        self.client.force_login(self.regular_user)
        r = self.client.get(reverse('user_detail', args=[self.regular_user.id]))
        self.assertRedirects(r, reverse('dashboard'))
