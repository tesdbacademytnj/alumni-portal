from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

INSTITUTE_CHOICES = [
    ('SSS', 'SSS'),
    ('Sainora', 'Sainora'),
    ('SankthiDB Technology', 'SankthiDB Technology'),
    ('TesDB Academy', 'TesDB Academy'),
    ('Others', 'Others'),
]

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=15, blank=True)
    city = models.CharField(max_length=100, blank=True)   # "Current City" in profile
    batch = models.IntegerField(null=True, blank=True)
    institute = models.CharField(max_length=50, choices=INSTITUTE_CHOICES, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin_user = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Admin-only login identifier
    username = models.CharField(max_length=50, unique=True, null=True, blank=True)

    # Extended professional profile — filled after registration
    EMPLOYMENT_CHOICES = [
        ('Currently Working', 'Currently Working'),
        ('Not Working', 'Not Working'),
        ('Fresher', 'Fresher'),
    ]
    employment_status = models.CharField(max_length=30, choices=EMPLOYMENT_CHOICES, blank=True)
    current_company = models.CharField(max_length=200, blank=True)
    designation = models.CharField(max_length=200, blank=True)
    domain = models.CharField(max_length=100, blank=True)
    experience_years = models.CharField(max_length=20, blank=True)
    salary = models.CharField(max_length=100, blank=True)
    skills = models.TextField(blank=True)  # comma-separated list
    resume = models.FileField(upload_to='resumes/', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = CustomUserManager()

    def skills_list(self):
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    @property
    def profile_complete(self):
        """True when all mandatory professional fields are filled."""
        required = [self.employment_status, self.designation, self.domain, self.experience_years]
        return all(required)

    @property
    def profile_fully_complete(self):
        fields = [
            self.mobile, self.city, self.batch, self.institute,
            self.employment_status, self.designation, self.domain,
            self.experience_years, self.salary, self.skills, self.resume,
        ]
        return all(fields)

    @property
    def profile_completion_percentage(self):
        fields = [
            self.mobile, self.city, self.batch, self.institute,
            self.employment_status, self.designation, self.domain,
            self.experience_years, self.salary, self.skills, self.resume,
        ]
        total = len(fields)
        filled = sum(1 for f in fields if f)
        return int(filled / total * 100)

    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    name       = models.CharField(max_length=200)
    email      = models.EmailField()
    subject    = models.CharField(max_length=300, blank=True)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.subject or 'No subject'}"


class AdminProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='admin_profile')
    access_code = models.CharField(max_length=50)

    def __str__(self):
        return f"Admin: {self.user.username or self.user.email}"


class EmailOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    def is_expired(self):
        from django.conf import settings
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

    def is_locked(self):
        from django.conf import settings
        return self.attempts >= settings.OTP_MAX_ATTEMPTS

    def __str__(self):
        return f"OTP({self.code}) for {self.user.email}"
