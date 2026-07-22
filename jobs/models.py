import re

from django.db import models
from django.conf import settings

# How many days after the last-date-to-apply a listing stays visible (disabled)
# to its owner/admin before being permanently removed.
JOB_REMOVE_GRACE_DAYS = 5

# Options for the "Salary / Package" field that don't represent an actual number.
SALARY_NOT_DISCLOSED = 'Not Disclosed'
SALARY_INDUSTRY_STANDARD = 'As per Industry Standard'


def format_years_experience(raw):
    """Normalize any free-text years-of-experience entry into 'N+ Year' form.

    Accepts inputs like '3', '3+', '3 yrs', '3 years', '5 year', '2.5 yrs'
    and turns them into '3+ Year', '3+ Year', '5+ Year', '2.5+ Year' etc.
    Non-numeric or empty input is returned unchanged (trimmed).
    """
    raw = (raw or '').strip()
    if not raw:
        return raw
    match = re.search(r'\d+(\.\d+)?', raw)
    if not match:
        return raw
    num = match.group(0)
    if '.' in num:
        num = num.rstrip('0').rstrip('.')
    return f"{num}+ Year"

STATUS_CHOICES = [
    ('pending',   'Pending Review'),
    ('published', 'Published'),
    ('rejected',  'Rejected'),
    ('expired',   'Expired'),
]

EXPERIENCE_CHOICES = [
    ('Fresher', 'Fresher'),
    ('Experienced', 'Experienced'),
]

JOB_TYPE_CHOICES = [
    ('', '-- Job Type --'),
    ('Full Time', 'Full Time'),
    ('Part Time', 'Part Time'),
    ('Contract', 'Contract'),
    ('Internship', 'Internship'),
    ('Remote', 'Remote'),
    ('Hybrid', 'Hybrid'),
]

EMPLOYMENT_STATUS_CHOICES = [
    ('', '-- Current Status --'),
    ('Currently Working', 'Currently Working'),
    ('On Notice Period', 'On Notice Period'),
    ('Career Gap', 'Career Gap'),
    ('Left Job', 'Left Job'),
    ('Fresher', 'Fresher'),
]

JOINING_CHOICES = [
    ('', '-- Joining Preference --'),
    ('Immediate', 'Immediate'),
    ('15 Days', '15 Days'),
    ('1 Month', '1 Month'),
    ('Others', 'Others'),
]

OPENING_TYPE_CHOICES = [
    ('Regular', 'Regular'),
    ('Backdoor', 'Backdoor'),
]

QUALIFICATION_CHOICES = [
    ('', '-- Select Qualification --'),
    ('10th', '10th'),
    ('12th', '12th'),
    ('Diploma', 'Diploma'),
    ('BE/BTech', 'BE/BTech'),
    ('ME/MTech', 'ME/MTech'),
    ('BCA', 'BCA'),
    ('MCA', 'MCA'),
    ('BSc', 'BSc'),
    ('MSc', 'MSc'),
    ('MBA', 'MBA'),
    ('Others', 'Others'),
]


class JobOpening(models.Model):
    posted_by             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_openings')
    title                 = models.CharField(max_length=200)
    company               = models.CharField(max_length=200)
    description           = models.TextField()
    domain                = models.CharField(max_length=100)
    job_type              = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='Full Time')
    experience            = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='Fresher')
    years_of_experience   = models.CharField(max_length=20, blank=True)
    salary_package        = models.CharField(max_length=100, blank=True)
    city                  = models.CharField(max_length=100)
    last_date_to_apply    = models.DateField(null=True, blank=True)
    skills                = models.TextField(blank=True)
    opening_type          = models.CharField(max_length=20, choices=OPENING_TYPE_CHOICES, default='Regular')
    amount_to_pay         = models.CharField(max_length=200, blank=True, default='')
    backdoor_description  = models.TextField(blank=True)
    status                = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    published_at          = models.DateTimeField(null=True, blank=True)
    created_at            = models.DateTimeField(auto_now_add=True)

    def skills_list(self):
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    @property
    def is_expired(self):
        from django.utils import timezone
        return bool(self.last_date_to_apply) and self.last_date_to_apply < timezone.localdate()

    @property
    def is_live(self):
        """Visible in the public job board: published, approved, and not past its deadline."""
        return self.status == 'published' and not self.is_expired

    @property
    def days_left(self):
        from django.utils import timezone
        if not self.last_date_to_apply:
            return None
        return (self.last_date_to_apply - timezone.localdate()).days

    def __str__(self):
        return f"{self.title} at {self.company}"


def mark_expired_jobs():
    """Flip any published job whose deadline has passed to 'expired'. Safe to call often."""
    from django.utils import timezone
    JobOpening.objects.filter(status='published', last_date_to_apply__lt=timezone.localdate()).update(status='expired')


class JobApplication(models.Model):
    """Links a JobSeeker profile ('Looking for a Job' details) to a specific JobOpening."""
    job            = models.ForeignKey('JobOpening', on_delete=models.CASCADE, related_name='applications')
    applicant      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applications')
    seeker_profile = models.ForeignKey('JobSeeker', on_delete=models.CASCADE, related_name='applications')
    applied_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'applicant')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.full_name} → {self.job.title}"


class JobSeeker(models.Model):
    user                  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_seekings')
    title                 = models.CharField(max_length=200)
    email                 = models.EmailField()
    mobile                = models.CharField(max_length=15)
    qualification         = models.CharField(max_length=50, blank=True)
    qualification_course  = models.CharField(max_length=100, blank=True)
    employment_status     = models.CharField(max_length=30, blank=True)
    domain                = models.CharField(max_length=100)
    experience            = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='Fresher')
    years_of_experience   = models.CharField(max_length=20, blank=True)
    joining_preference    = models.CharField(max_length=50, blank=True)
    joining_months_others = models.CharField(max_length=20, blank=True)
    current_company       = models.CharField(max_length=200, blank=True)
    current_designation   = models.CharField(max_length=200, blank=True)
    current_city          = models.CharField(max_length=100, blank=True)
    expected_salary       = models.CharField(max_length=100, blank=True)
    salary_not_disclosed  = models.BooleanField(default=False)
    skills                = models.TextField(blank=True)
    resume                = models.FileField(upload_to='resumes/', blank=True, null=True)
    created_at            = models.DateTimeField(auto_now_add=True)

    def skills_list(self):
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    def __str__(self):
        return f"{self.user.full_name} — {self.title}"


class JobInterest(models.Model):
    job       = models.ForeignKey('JobOpening', on_delete=models.CASCADE, related_name='interests')
    user      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_interests')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} interested in {self.job.title}"
