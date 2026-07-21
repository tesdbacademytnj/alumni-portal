"""
AlumniPortal — Jobs Test Suite
Covers: JobOpening form, JobSeeker form, post_opening view,
        seek_job view, my_opening_detail, my_seeker_detail,
        access control (owner-only), admin access.
"""
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import CustomUser, AdminProfile
from .models import JobOpening, JobSeeker
from .forms import JobOpeningForm, JobSeekerForm


# ─── helpers ────────────────────────────────────────────────────────────────

def make_user(email='user@test.com', password='Pass1234!', complete=True):
    u = CustomUser.objects.create_user(
        email=email, password=password, full_name='Test User')
    u.is_active = True
    if complete:
        u.current_company = 'TCS'
        u.designation = 'Developer'
        u.domain = 'Python'
        u.city = 'Chennai'
        u.experience_years = '3'
        u.skills = 'Python,Django'
        u.mobile = '9000000000'
        u.salary = '6 LPA'
    u.save()
    return u


def make_admin():
    u = CustomUser.objects.create_user(
        email='admin@local', password='x', full_name='Admin',
        is_admin_user=True, is_active=True, username='admin')
    AdminProfile.objects.create(user=u, access_code='admin123')
    return u


def opening_data(**override):
    data = {
        'title': 'Python Developer',
        'company': 'TechCorp',
        'domain': 'Web Development',
        'job_type': 'Full Time',
        'experience': 'Experienced',
        'years_of_experience': '2',
        'salary_package': '6 LPA',
        'city': 'Chennai',
        'last_date_to_apply': str(datetime.date.today() + datetime.timedelta(days=30)),
        'skills': 'Python,Django',
        'description': 'We need a skilled Python developer.',
    }
    data.update(override)
    return data


def seeker_data(**override):
    dummy_pdf = SimpleUploadedFile('resume.pdf', b'%PDF-1.4 test', content_type='application/pdf')
    data = {
        'title': 'Backend Developer',
        'email': 'user@test.com',
        'mobile': '9000000000',
        'qualification': 'BE/BTech',
        'qualification_course': 'Computer Science',
        'employment_status': 'Currently Working',
        'domain': 'Python',
        'experience': 'Experienced',
        'years_of_experience': '3',
        'joining_preference': 'Immediate',
        'joining_months_others': '',
        'current_company': 'TCS',
        'current_designation': 'Developer',
        'expected_salary': '8 LPA',
        'salary_not_disclosed': False,
        'current_city': 'Chennai',
        'skills': 'Python,Django,REST',
        'resume': dummy_pdf,
    }
    data.update(override)
    return data


# ─── JobOpeningForm ──────────────────────────────────────────────────────────

class JobOpeningFormTests(TestCase):

    def test_valid_form_passes(self):
        f = JobOpeningForm(data=opening_data())
        self.assertTrue(f.is_valid(), f.errors)

    def test_missing_title_fails(self):
        f = JobOpeningForm(data=opening_data(title=''))
        self.assertFalse(f.is_valid())
        self.assertIn('title', f.errors)

    def test_missing_company_fails(self):
        f = JobOpeningForm(data=opening_data(company=''))
        self.assertFalse(f.is_valid())

    def test_missing_description_fails(self):
        f = JobOpeningForm(data=opening_data(description=''))
        self.assertFalse(f.is_valid())

    def test_experienced_without_years_fails(self):
        f = JobOpeningForm(data=opening_data(experience='Experienced', years_of_experience=''))
        self.assertFalse(f.is_valid())

    def test_fresher_without_years_passes(self):
        f = JobOpeningForm(data=opening_data(experience='Fresher', years_of_experience=''))
        self.assertTrue(f.is_valid(), f.errors)

    def test_others_city_without_text_fails(self):
        f = JobOpeningForm(data=opening_data(city='Others', city_other=''))
        self.assertFalse(f.is_valid())

    def test_others_city_with_text_passes_and_saves_correctly(self):
        f = JobOpeningForm(data=opening_data(city='Others', city_other='America'))
        self.assertTrue(f.is_valid(), f.errors)
        # city should resolve to the free-text value
        self.assertEqual(f.cleaned_data.get('city_other'), 'America')

    def test_all_job_type_choices_valid(self):
        for jt in ('Full Time', 'Part Time', 'Contract', 'Internship', 'Remote', 'Hybrid'):
            f = JobOpeningForm(data=opening_data(job_type=jt))
            self.assertTrue(f.is_valid(), f'{jt}: {f.errors}')

    def test_missing_salary_fails(self):
        f = JobOpeningForm(data=opening_data(salary_package=''))
        self.assertFalse(f.is_valid())

    def test_missing_job_type_fails(self):
        f = JobOpeningForm(data=opening_data(job_type=''))
        self.assertFalse(f.is_valid())

    def test_skills_stored_as_comma_string(self):
        f = JobOpeningForm(data=opening_data(skills='Python,Django,React'))
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['skills'], 'Python,Django,React')


# ─── JobSeekerForm ───────────────────────────────────────────────────────────

class JobSeekerFormTests(TestCase):

    def test_valid_form_passes(self):
        f = JobSeekerForm(data=seeker_data(), files={'resume': seeker_data()['resume']})
        self.assertTrue(f.is_valid(), f.errors)

    def test_missing_title_fails(self):
        f = JobSeekerForm(data=seeker_data(title=''), files={})
        self.assertFalse(f.is_valid())

    def test_missing_email_fails(self):
        f = JobSeekerForm(data=seeker_data(email=''), files={})
        self.assertFalse(f.is_valid())

    def test_invalid_email_fails(self):
        f = JobSeekerForm(data=seeker_data(email='notanemail'), files={})
        self.assertFalse(f.is_valid())

    def test_fresher_does_not_need_experience_or_company(self):
        d = seeker_data(employment_status='Fresher', years_of_experience='',
                        current_company='', current_designation='')
        dummy = SimpleUploadedFile('r.pdf', b'%PDF', content_type='application/pdf')
        f = JobSeekerForm(data=d, files={'resume': dummy})
        self.assertTrue(f.is_valid(), f.errors)

    def test_non_fresher_requires_years_of_experience(self):
        d = seeker_data(employment_status='Currently Working', years_of_experience='')
        f = JobSeekerForm(data=d, files={})
        self.assertFalse(f.is_valid())

    def test_non_fresher_requires_current_company(self):
        d = seeker_data(employment_status='Currently Working', current_company='')
        f = JobSeekerForm(data=d, files={})
        self.assertFalse(f.is_valid())

    def test_non_fresher_requires_current_designation(self):
        d = seeker_data(employment_status='Currently Working', current_designation='')
        f = JobSeekerForm(data=d, files={})
        self.assertFalse(f.is_valid())

    def test_bsc_qualification_requires_course(self):
        d = seeker_data(qualification='BSc', qualification_course='')
        f = JobSeekerForm(data=d, files={})
        self.assertFalse(f.is_valid())

    def test_msc_qualification_requires_course(self):
        d = seeker_data(qualification='MSc', qualification_course='')
        f = JobSeekerForm(data=d, files={})
        self.assertFalse(f.is_valid())

    def test_10th_qualification_does_not_need_course(self):
        d = seeker_data(qualification='10th', qualification_course='')
        dummy = SimpleUploadedFile('r.pdf', b'%PDF', content_type='application/pdf')
        f = JobSeekerForm(data=d, files={'resume': dummy})
        self.assertTrue(f.is_valid(), f.errors)

    def test_12th_qualification_does_not_need_course(self):
        d = seeker_data(qualification='12th', qualification_course='')
        dummy = SimpleUploadedFile('r.pdf', b'%PDF', content_type='application/pdf')
        f = JobSeekerForm(data=d, files={'resume': dummy})
        self.assertTrue(f.is_valid(), f.errors)

    def test_joining_others_requires_preference_text(self):
        d = seeker_data(joining_preference='Others', joining_months_others='')
        f = JobSeekerForm(data=d, files={})
        self.assertFalse(f.is_valid())

    def test_joining_others_with_text_passes(self):
        d = seeker_data(joining_preference='Others', joining_months_others='3 months')
        dummy = SimpleUploadedFile('r.pdf', b'%PDF', content_type='application/pdf')
        f = JobSeekerForm(data=d, files={'resume': dummy})
        self.assertTrue(f.is_valid(), f.errors)

    def test_salary_not_disclosed_overrides_expected_salary(self):
        d = seeker_data(expected_salary='', salary_not_disclosed=True)
        dummy = SimpleUploadedFile('r.pdf', b'%PDF', content_type='application/pdf')
        f = JobSeekerForm(data=d, files={'resume': dummy})
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data.get('expected_salary'), 'Not Disclosed')

    def test_missing_salary_without_not_disclosed_fails(self):
        d = seeker_data(expected_salary='', salary_not_disclosed=False)
        f = JobSeekerForm(data=d, files={})
        self.assertFalse(f.is_valid())

    def test_missing_skills_fails(self):
        d = seeker_data(skills='')
        f = JobSeekerForm(data=d, files={})
        self.assertFalse(f.is_valid())

    def test_missing_resume_fails(self):
        d = seeker_data()
        f = JobSeekerForm(data=d, files={})   # no file
        self.assertFalse(f.is_valid())

    def test_missing_city_fails(self):
        d = seeker_data(current_city='')
        f = JobSeekerForm(data=d, files={})
        self.assertFalse(f.is_valid())

    def test_experience_set_to_fresher_for_fresher_status(self):
        d = seeker_data(employment_status='Fresher', years_of_experience='',
                        current_company='', current_designation='')
        dummy = SimpleUploadedFile('r.pdf', b'%PDF', content_type='application/pdf')
        f = JobSeekerForm(data=d, files={'resume': dummy})
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['experience'], 'Fresher')

    def test_experience_set_to_experienced_for_working_status(self):
        d = seeker_data(employment_status='Currently Working')
        dummy = SimpleUploadedFile('r.pdf', b'%PDF', content_type='application/pdf')
        f = JobSeekerForm(data=d, files={'resume': dummy})
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['experience'], 'Experienced')


# ─── Post Opening View ───────────────────────────────────────────────────────

class PostOpeningViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.url = reverse('post_opening')

    def test_get_requires_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)

    def test_get_page_loads_for_authenticated_user(self):
        self.client.force_login(self.user)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Post a Job Opening')

    def test_valid_post_creates_opening_and_redirects_to_detail(self):
        self.client.force_login(self.user)
        r = self.client.post(self.url, opening_data())
        job = JobOpening.objects.filter(posted_by=self.user).first()
        self.assertIsNotNone(job)
        self.assertEqual(job.title, 'Python Developer')
        self.assertRedirects(r, reverse('my_opening_detail', args=[job.pk]))

    def test_invalid_post_shows_form_errors(self):
        self.client.force_login(self.user)
        r = self.client.post(self.url, opening_data(title=''))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(JobOpening.objects.count(), 0)

    def test_others_city_saved_as_free_text(self):
        self.client.force_login(self.user)
        self.client.post(self.url, opening_data(city='Others', city_other='America'))
        job = JobOpening.objects.filter(posted_by=self.user).first()
        self.assertIsNotNone(job)
        self.assertEqual(job.city, 'America')

    def test_job_posted_by_correct_user(self):
        self.client.force_login(self.user)
        self.client.post(self.url, opening_data())
        job = JobOpening.objects.first()
        self.assertEqual(job.posted_by, self.user)


# ─── Seek Job View ───────────────────────────────────────────────────────────

class SeekJobViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.url = reverse('seek_job')

    def test_get_requires_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)

    def test_page_loads_for_authenticated_user(self):
        self.client.force_login(self.user)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_form_pre_filled_from_profile(self):
        self.client.force_login(self.user)
        r = self.client.get(self.url)
        self.assertContains(r, 'user@test.com')   # email pre-filled
        self.assertContains(r, 'TCS')             # company pre-filled
        self.assertContains(r, 'Chennai')         # city pre-filled

    def test_valid_post_creates_seeker_and_redirects(self):
        self.client.force_login(self.user)
        d = seeker_data()
        resume = SimpleUploadedFile('r.pdf', b'%PDF', content_type='application/pdf')
        r = self.client.post(self.url, {**d, 'resume': resume})
        seeker = JobSeeker.objects.filter(user=self.user).first()
        self.assertIsNotNone(seeker)
        self.assertRedirects(r, reverse('my_seeker_detail', args=[seeker.pk]))

    def test_invalid_post_shows_errors(self):
        self.client.force_login(self.user)
        r = self.client.post(self.url, seeker_data(title=''))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(JobSeeker.objects.count(), 0)


# ─── My Opening Detail ───────────────────────────────────────────────────────

class MyOpeningDetailTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.owner = make_user(email='owner@x.com')
        self.other = make_user(email='other@x.com')
        self.admin = make_admin()
        self.job = JobOpening.objects.create(
            posted_by=self.owner, title='Dev', company='Co', domain='Python',
            job_type='Full Time', experience='Fresher', salary_package='5L',
            city='Chennai', description='Test desc', skills='Python')

    def test_owner_can_view_detail(self):
        self.client.force_login(self.owner)
        r = self.client.get(reverse('my_opening_detail', args=[self.job.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Dev')

    def test_other_user_gets_404(self):
        self.client.force_login(self.other)
        r = self.client.get(reverse('my_opening_detail', args=[self.job.pk]))
        self.assertEqual(r.status_code, 404)

    def test_admin_can_view_any_detail(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('my_opening_detail', args=[self.job.pk]))
        self.assertEqual(r.status_code, 200)

    def test_unauthenticated_redirected(self):
        r = self.client.get(reverse('my_opening_detail', args=[self.job.pk]))
        self.assertEqual(r.status_code, 302)

    def test_nonexistent_job_returns_404(self):
        self.client.force_login(self.owner)
        r = self.client.get(reverse('my_opening_detail', args=[9999]))
        self.assertEqual(r.status_code, 404)

    def test_detail_shows_all_key_fields(self):
        self.client.force_login(self.owner)
        r = self.client.get(reverse('my_opening_detail', args=[self.job.pk]))
        self.assertContains(r, 'Co')        # company
        self.assertContains(r, 'Chennai')   # city
        self.assertContains(r, 'Full Time') # job type
        self.assertContains(r, '5L')        # salary


# ─── My Seeker Detail ────────────────────────────────────────────────────────

class MySeekDetailTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.owner = make_user(email='seeker@x.com')
        self.other = make_user(email='nosy@x.com')
        self.admin = make_admin()
        self.seeker = JobSeeker.objects.create(
            user=self.owner, title='Dev', email='seeker@x.com', mobile='9000000000',
            domain='Python', experience='Fresher', employment_status='Fresher',
            joining_preference='Immediate', expected_salary='4 LPA',
            current_city='Chennai', skills='Python,Django',
        )

    def test_owner_can_view_detail(self):
        self.client.force_login(self.owner)
        r = self.client.get(reverse('my_seeker_detail', args=[self.seeker.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Dev')

    def test_other_user_gets_404(self):
        self.client.force_login(self.other)
        r = self.client.get(reverse('my_seeker_detail', args=[self.seeker.pk]))
        self.assertEqual(r.status_code, 404)

    def test_admin_can_view_any_seeker(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('my_seeker_detail', args=[self.seeker.pk]))
        self.assertEqual(r.status_code, 200)

    def test_unauthenticated_redirected(self):
        r = self.client.get(reverse('my_seeker_detail', args=[self.seeker.pk]))
        self.assertEqual(r.status_code, 302)

    def test_detail_shows_key_fields(self):
        self.client.force_login(self.owner)
        r = self.client.get(reverse('my_seeker_detail', args=[self.seeker.pk]))
        self.assertContains(r, 'Fresher')
        self.assertContains(r, 'Chennai')
        self.assertContains(r, 'Immediate')
        self.assertContains(r, '4 LPA')


# ─── Job Model Methods ───────────────────────────────────────────────────────

class JobModelMethodTests(TestCase):

    def test_skills_list_splits_correctly(self):
        j = JobOpening(skills='Python,Django, React , ')
        self.assertEqual(j.skills_list(), ['Python', 'Django', 'React'])

    def test_skills_list_empty(self):
        j = JobOpening(skills='')
        self.assertEqual(j.skills_list(), [])

    def test_seeker_skills_list(self):
        s = JobSeeker(skills='Java,Spring Boot,MySQL')
        self.assertEqual(s.skills_list(), ['Java', 'Spring Boot', 'MySQL'])

    def test_opening_str(self):
        j = JobOpening(title='Dev', company='Corp')
        self.assertIn('Dev', str(j))
        self.assertIn('Corp', str(j))
