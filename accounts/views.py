from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from .forms import UserRegisterForm, UserLoginForm, AdminLoginForm, EditProfileForm, OTPVerifyForm, ForgotPasswordForm, ResetPasswordForm
from .models import CustomUser, AdminProfile, EmailOTP, ContactMessage
from .utils import send_otp_email, send_job_unpublished_email, OTPSendError
from jobs.models import JobOpening, JobSeeker, JobApplication, JobInterest, mark_expired_jobs


def user_register(request):
    form = UserRegisterForm()
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            CustomUser.objects.filter(email=email, is_active=False).delete()
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            try:
                send_otp_email(user)
            except OTPSendError:
                user.delete()
                messages.error(request, "We couldn't send the verification email. Please check the address and try again.")
                return render(request, 'accounts/user_register.html', {'form': form})
            request.session['pending_verification_user_id'] = user.id
            request.session['otp_last_sent'] = timezone.now().isoformat()
            messages.success(request, f'We sent a 6-digit code to {user.email}. Enter it below to verify.')
            return redirect('verify_otp')
    return render(request, 'accounts/user_register.html', {'form': form})


def verify_otp(request):
    user_id = request.session.get('pending_verification_user_id')
    if not user_id:
        messages.error(request, 'Your verification session expired. Please register again.')
        return redirect('user_register')
    user = CustomUser.objects.filter(id=user_id, is_active=False).first()
    if not user:
        request.session.pop('pending_verification_user_id', None)
        return redirect('user_login')
    form = OTPVerifyForm()
    if request.method == 'POST':
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            otp  = EmailOTP.objects.filter(user=user, is_used=False).order_by('-created_at').first()
            if not otp:
                messages.error(request, 'No active code found. Tap "Resend code".')
            elif otp.is_expired():
                messages.error(request, 'Code expired. Tap "Resend code".')
            elif otp.is_locked():
                messages.error(request, 'Too many attempts. Tap "Resend code".')
            elif otp.code != code:
                otp.attempts += 1
                otp.save(update_fields=['attempts'])
                remaining = settings.OTP_MAX_ATTEMPTS - otp.attempts
                messages.error(request, f'Incorrect code. {max(remaining,0)} attempt(s) left.')
            else:
                otp.is_used = True
                otp.save(update_fields=['is_used'])
                user.is_active = True
                user.save(update_fields=['is_active'])
                request.session.pop('pending_verification_user_id', None)
                request.session.pop('otp_last_sent', None)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Email verified! Welcome to the Alumni Portal.')
                return redirect('job_board')
    return render(request, 'accounts/verify_otp.html', {'form': form, 'email': user.email})


def resend_otp(request):
    user_id = request.session.get('pending_verification_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please register again.')
        return redirect('user_register')
    user = CustomUser.objects.filter(id=user_id, is_active=False).first()
    if not user:
        return redirect('user_login')
    last_sent_iso = request.session.get('otp_last_sent')
    if last_sent_iso:
        elapsed = (timezone.now() - timezone.datetime.fromisoformat(last_sent_iso)).total_seconds()
        if elapsed < settings.OTP_RESEND_COOLDOWN_SECONDS:
            wait = int(settings.OTP_RESEND_COOLDOWN_SECONDS - elapsed)
            messages.error(request, f'Please wait {wait}s before requesting another code.')
            return redirect('verify_otp')
    try:
        send_otp_email(user)
    except OTPSendError:
        messages.error(request, "Couldn't send email right now. Please try again shortly.")
        return redirect('verify_otp')
    request.session['otp_last_sent'] = timezone.now().isoformat()
    messages.success(request, f'A new code was sent to {user.email}.')
    return redirect('verify_otp')


def user_login(request):
    if request.user.is_authenticated and not request.user.is_admin_user:
        return redirect('job_board')
    form = UserLoginForm()
    show_forgot_password = False
    if request.method == 'POST':
        email    = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user and not user.is_admin_user:
            login(request, user)
            return redirect('job_board')
        else:
            unverified = CustomUser.objects.filter(email__iexact=email, is_active=False).first()
            if unverified and unverified.check_password(password):
                try:
                    send_otp_email(unverified)
                    request.session['otp_last_sent'] = timezone.now().isoformat()
                except OTPSendError:
                    messages.error(request, "Email not verified and couldn't resend code. Try again shortly.")
                    return render(request, 'accounts/user_login.html', {'form': form})
                request.session['pending_verification_user_id'] = unverified.id
                messages.error(request, "Email not verified. We resent your code.")
                return redirect('verify_otp')
            messages.error(request, 'Invalid email or password.')
            show_forgot_password = True
    return render(request, 'accounts/user_login.html', {'form': form, 'show_forgot_password': show_forgot_password})


def admin_login(request):
    if request.user.is_authenticated and request.user.is_admin_user:
        return redirect('job_board')
    form = AdminLoginForm()
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].strip()
            code     = form.cleaned_data['code'].strip()

            # 1. Check .env master admin credentials
            env_username = getattr(settings, 'ADMIN_USERNAME', '').strip()
            env_code     = getattr(settings, 'ADMIN_ACCESS_CODE', '').strip()
            if env_username and env_code and username == env_username and code == env_code:
                # Auto-create or retrieve the env-based admin user
                env_email = f"{env_username}@admin.alumniportal.local"
                user, created = CustomUser.objects.get_or_create(
                    username=env_username,
                    defaults={
                        'email': env_email,
                        'full_name': 'Admin',
                        'is_admin_user': True,
                        'is_staff': True,
                        'is_active': True,
                    }
                )
                if not created:
                    user.is_admin_user = True
                    user.is_active     = True
                    user.save(update_fields=['is_admin_user', 'is_active'])
                if not hasattr(user, 'admin_profile'):
                    AdminProfile.objects.create(user=user, access_code=env_code)
                else:
                    user.admin_profile.access_code = env_code
                    user.admin_profile.save(update_fields=['access_code'])
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return redirect('job_board')

            # 2. Fall back to DB-based admins (created via manage.py create_admin)
            user = CustomUser.objects.filter(
                username__iexact=username, is_admin_user=True, is_active=True
            ).select_related('admin_profile').first()
            if user and hasattr(user, 'admin_profile') and user.admin_profile.access_code == code:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return redirect('job_board')

            messages.error(request, 'Invalid username or access code.')
    return render(request, 'accounts/admin_login.html', {'form': form})


def forgot_password(request):
    if request.user.is_authenticated and not request.user.is_admin_user:
        return redirect('job_board')
    form = ForgotPasswordForm()
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = CustomUser.objects.filter(email__iexact=email, is_active=True).first()
            if user:
                try:
                    send_otp_email(user, purpose='reset')
                except OTPSendError:
                    messages.error(request, "Couldn't send the password reset email. Please try again shortly.")
                    return render(request, 'accounts/forgot_password.html', {'form': form})
                request.session['reset_password_user_id'] = user.id
                request.session['otp_last_sent'] = timezone.now().isoformat()
                messages.success(request, f'We sent a password reset code to {user.email}.')
                return redirect('verify_reset_otp')
            else:
                messages.error(request, 'No active account found with that email address.')
    return render(request, 'accounts/forgot_password.html', {'form': form})


def verify_reset_otp(request):
    user_id = request.session.get('reset_password_user_id')
    if not user_id:
        messages.error(request, 'Your password reset session expired. Please start again.')
        return redirect('forgot_password')
    user = CustomUser.objects.filter(id=user_id, is_active=True).first()
    if not user:
        request.session.pop('reset_password_user_id', None)
        return redirect('forgot_password')
    form = OTPVerifyForm()
    if request.method == 'POST':
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            otp  = EmailOTP.objects.filter(user=user, is_used=False).order_by('-created_at').first()
            if not otp:
                messages.error(request, 'No active code found. Tap "Resend code".')
            elif otp.is_expired():
                messages.error(request, 'Code expired. Tap "Resend code".')
            elif otp.is_locked():
                messages.error(request, 'Too many attempts. Tap "Resend code".')
            elif otp.code != code:
                otp.attempts += 1
                otp.save(update_fields=['attempts'])
                remaining = settings.OTP_MAX_ATTEMPTS - otp.attempts
                messages.error(request, f'Incorrect code. {max(remaining,0)} attempt(s) left.')
            else:
                otp.is_used = True
                otp.save(update_fields=['is_used'])
                request.session['reset_password_verified'] = True
                messages.success(request, 'Code verified. Now set your new password.')
                return redirect('reset_password')
    return render(request, 'accounts/verify_otp.html', {'form': form, 'email': user.email, 'reset_mode': True})


def resend_reset_otp(request):
    user_id = request.session.get('reset_password_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('forgot_password')
    user = CustomUser.objects.filter(id=user_id, is_active=True).first()
    if not user:
        return redirect('forgot_password')
    last_sent_iso = request.session.get('otp_last_sent')
    if last_sent_iso:
        elapsed = (timezone.now() - timezone.datetime.fromisoformat(last_sent_iso)).total_seconds()
        if elapsed < settings.OTP_RESEND_COOLDOWN_SECONDS:
            wait = int(settings.OTP_RESEND_COOLDOWN_SECONDS - elapsed)
            messages.error(request, f'Please wait {wait}s before requesting another code.')
            return redirect('verify_reset_otp')
    try:
        send_otp_email(user, purpose='reset')
    except OTPSendError:
        messages.error(request, "Couldn't send email right now. Please try again shortly.")
        return redirect('verify_reset_otp')
    request.session['otp_last_sent'] = timezone.now().isoformat()
    messages.success(request, f'A new code was sent to {user.email}.')
    return redirect('verify_reset_otp')


def reset_password(request):
    user_id = request.session.get('reset_password_user_id')
    verified = request.session.get('reset_password_verified')
    if not user_id or not verified:
        messages.error(request, 'Your password reset session expired. Please start again.')
        return redirect('forgot_password')
    user = CustomUser.objects.filter(id=user_id, is_active=True).first()
    if not user:
        return redirect('forgot_password')
    form = ResetPasswordForm()
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password'])
            user.save(update_fields=['password'])
            request.session.pop('reset_password_user_id', None)
            request.session.pop('reset_password_verified', None)
            request.session.pop('otp_last_sent', None)
            messages.success(request, 'Password reset successfully. Please sign in with your new password.')
            return redirect('user_login')
    return render(request, 'accounts/reset_password.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    if request.user.is_admin_user:
        return redirect('job_board')

    job_posts = JobOpening.objects.filter(posted_by=request.user).order_by('-created_at')
    job_applied = JobApplication.objects.filter(applicant=request.user).select_related('job').order_by('-applied_at')
    job_interests = JobInterest.objects.filter(user=request.user).select_related('job').order_by('-created_at')
    return render(request, 'accounts/dashboard.html', {
        'job_posts': job_posts,
        'job_applied': job_applied,
        'job_interests': job_interests,
    })


@login_required
def edit_profile(request):
    user = request.user
    initial = {'batch': str(user.batch) if user.batch else ''}
    if user.city:
        initial['city'] = user.city
    form = EditProfileForm(instance=user, initial=initial)
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('job_board')
    return render(request, 'accounts/edit_profile.html', {
        'form': form,
        'profile_complete': user.profile_complete,
    })


@login_required
def admin_dashboard(request):
    if not request.user.is_admin_user:
        return redirect('job_board')
    mark_expired_jobs()
    users        = CustomUser.objects.filter(is_admin_user=False).order_by('-date_joined')
    all_openings = JobOpening.objects.select_related('posted_by').prefetch_related('interests').order_by('-created_at')
    pending_openings   = all_openings.filter(status='pending')
    published_openings = all_openings.filter(status='published')
    other_openings      = all_openings.exclude(status__in=['pending', 'published'])
    all_seekers  = JobSeeker.objects.select_related('user').order_by('-created_at')
    messages_qs  = ContactMessage.objects.all()
    unread_count = messages_qs.filter(is_read=False).count()
    user_count = users.count()
    pending_count = pending_openings.count()
    openings_count = all_openings.count()
    messages_count = messages_qs.count()
    return render(request, 'accounts/admin_dashboard.html', {
        'users': users,
        'all_openings': all_openings,
        'pending_openings': pending_openings,
        'published_openings': published_openings,
        'other_openings': other_openings,
        'all_seekers': all_seekers,
        'contact_messages': messages_qs,
        'unread_count': unread_count,
        'user_count': user_count,
        'pending_count': pending_count,
        'openings_count': openings_count,
        'messages_count': messages_count,
        'totals': [
            ('Users', user_count),
            ('Pending', pending_count),
            ('Openings', openings_count),
            ('Messages', messages_count),
        ],
    })


@login_required
def publish_job(request, pk):
    if not request.user.is_admin_user:
        return redirect('job_board')
    job = get_object_or_404(JobOpening, pk=pk)
    if request.method == 'POST':
        job.status = 'published'
        job.published_at = timezone.now()
        job.save(update_fields=['status', 'published_at'])
        messages.success(request, f'"{job.title}" is now published on the public job board.')
    return redirect('job_board')


@login_required
def reject_job(request, pk):
    if not request.user.is_admin_user:
        return redirect('job_board')
    job = get_object_or_404(JobOpening, pk=pk)
    if request.method == 'POST':
        job.status = 'rejected'
        job.save(update_fields=['status'])
        messages.success(request, f'"{job.title}" has been rejected.')
    return redirect('job_board')


@login_required
def unpublish_job(request, pk):
    if not request.user.is_admin_user:
        return redirect('job_board')
    job = get_object_or_404(JobOpening, pk=pk)
    if request.method == 'POST':
        job.status = 'pending'
        job.published_at = None
        job.save(update_fields=['status', 'published_at'])
        send_job_unpublished_email(job)
        messages.success(request, f'"{job.title}" has been unpublished and sent back for review.')
    return redirect('job_board')


@login_required
def mark_message_read(request, message_id):
    if not request.user.is_admin_user:
        return redirect('job_board')
    if request.method == 'POST':
        ContactMessage.objects.filter(id=message_id).update(is_read=True)
    return redirect('job_board')


@login_required
def user_detail(request, user_id):
    if not request.user.is_admin_user:
        return redirect('job_board')
    profile_user = get_object_or_404(CustomUser, id=user_id, is_admin_user=False)
    openings = JobOpening.objects.filter(posted_by=profile_user).order_by('-created_at')
    seekings = JobSeeker.objects.filter(user=profile_user).order_by('-created_at')
    job_applications = JobApplication.objects.filter(applicant=profile_user).select_related('job').order_by('-applied_at')
    return render(request, 'accounts/user_detail.html', {
        'profile_user': profile_user,
        'openings': openings,
        'seekings': seekings,
        'job_applications': job_applications,
    })
