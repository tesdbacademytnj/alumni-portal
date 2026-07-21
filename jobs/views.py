from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from .forms import JobOpeningForm, JobSeekerForm
from .models import JobOpening, JobSeeker, JobApplication, JobInterest, mark_expired_jobs, JOB_TYPE_CHOICES, EXPERIENCE_CHOICES


@login_required
def post_opening(request):
    form = JobOpeningForm()
    if request.method == 'POST':
        form = JobOpeningForm(request.POST)
        if form.is_valid():
            opening = form.save(commit=False)
            opening.posted_by = request.user
            opening.status = 'pending'
            opening.save()
            messages.success(
                request,
                'Your job opening has been submitted for review. It will appear on the '
                'public job board once approved by an administrator.'
            )
            return redirect('my_opening_detail', pk=opening.pk)
    return render(request, 'jobs/post_opening.html', {'form': form})


@login_required
def admin_post_opening(request):
    if not request.user.is_admin_user:
        return redirect('job_board')
    form = JobOpeningForm()
    if request.method == 'POST':
        form = JobOpeningForm(request.POST)
        if form.is_valid():
            opening = form.save(commit=False)
            opening.posted_by = request.user
            opening.status = 'published'
            opening.published_at = timezone.now()
            opening.save()
            messages.success(
                request,
                f'"{opening.title}" has been published and is now visible on the public job board.'
            )
            return redirect('my_opening_detail', pk=opening.pk)
    return render(request, 'jobs/post_opening.html', {'form': form, 'admin_mode': True})


@login_required
def seek_job(request):
    user = request.user
    initial = {
        'email':               user.email,
        'mobile':              user.mobile,
        'current_company':     user.current_company,
        'current_designation': user.designation,
        'years_of_experience': user.experience_years,
        'expected_salary':     user.salary,
        'current_city':        user.city,
        'skills':              user.skills,
    }
    form = JobSeekerForm(initial=initial)
    if request.method == 'POST':
        form = JobSeekerForm(request.POST, request.FILES)
        if form.is_valid():
            seeker = form.save(commit=False)
            seeker.user = user
            seeker.save()
            messages.success(request, 'Your profile has been saved successfully!')
            apply_job_id = request.session.pop('apply_after_profile', None)
            if apply_job_id:
                return redirect('job_apply', pk=apply_job_id)
            return redirect('my_seeker_detail', pk=seeker.pk)
    return render(request, 'jobs/seek_job.html', {'form': form})


@login_required
def my_opening_detail(request, pk):
    """Only the person who posted this opening (or an admin) can view it, along with applicants."""
    job = get_object_or_404(JobOpening, pk=pk)
    if job.posted_by != request.user and not request.user.is_admin_user:
        raise Http404
    applications = job.applications.select_related('seeker_profile', 'applicant').order_by('-applied_at')
    interests = JobInterest.objects.filter(job=job).select_related('user').order_by('-created_at')
    return render(request, 'jobs/my_opening_detail.html', {'job': job, 'applications': applications, 'interests': interests})


@login_required
def my_seeker_detail(request, pk):
    """Only the person who submitted this profile can view it."""
    seeker = get_object_or_404(JobSeeker, pk=pk)
    if seeker.user != request.user and not request.user.is_admin_user:
        raise Http404
    return render(request, 'jobs/my_seeker_detail.html', {'seeker': seeker})


# ─────────────────────────────  PUBLIC JOB BOARD  ──────────────────────────

@login_required
def job_board(request):
    """Card listing of every published, non-expired job opening. Company & poster hidden."""
    mark_expired_jobs()
    today = timezone.localdate()

    q = request.GET.get('q', '').strip()
    job_type = request.GET.get('job_type', '').strip()
    experience = request.GET.get('experience', '').strip()
    city = request.GET.get('city', '').strip()
    domain = request.GET.get('domain', '').strip()

    jobs = (JobOpening.objects
            .filter(status='published', last_date_to_apply__gte=today)
            .order_by('-published_at', '-created_at'))

    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(skills__icontains=q) |
            Q(domain__icontains=q) |
            Q(company__icontains=q) |
            Q(city__icontains=q)
        )

    if job_type:
        jobs = jobs.filter(job_type=job_type)

    if experience:
        jobs = jobs.filter(experience=experience)

    if city:
        jobs = jobs.filter(city__icontains=city)

    if domain:
        jobs = jobs.filter(domain__icontains=domain)

    cities = (JobOpening.objects
              .filter(status='published', last_date_to_apply__gte=today)
              .values_list('city', flat=True).distinct().order_by('city'))

    domains = (JobOpening.objects
               .filter(status='published', last_date_to_apply__gte=today)
               .values_list('domain', flat=True).distinct().order_by('domain'))

    applied_job_ids = set(
        JobApplication.objects.filter(applicant=request.user).values_list('job_id', flat=True)
    )
    interested_job_ids = set(
        JobInterest.objects.filter(user=request.user).values_list('job_id', flat=True)
    )

    return render(request, 'jobs/job_board.html', {
        'jobs': jobs,
        'applied_job_ids': applied_job_ids,
        'interested_job_ids': interested_job_ids,
        'q': q,
        'selected_job_type': job_type,
        'selected_experience': experience,
        'selected_city': city,
        'selected_domain': domain,
        'cities': cities,
        'domains': domains,
        'job_type_choices': [c for c in JOB_TYPE_CHOICES if c[0]],
        'experience_choices': [c for c in EXPERIENCE_CHOICES if c[0]],
    })


@login_required
def job_detail(request, pk):
    """Full detail view of a single opening. Company name & poster identity are never shown."""
    job = get_object_or_404(JobOpening, pk=pk)
    is_owner_or_admin = job.posted_by == request.user or request.user.is_admin_user
    if not job.is_live and not is_owner_or_admin:
        raise Http404
    already_applied = JobApplication.objects.filter(job=job, applicant=request.user).exists()
    has_seeker_profile = JobSeeker.objects.filter(user=request.user).exists()
    is_interested = JobInterest.objects.filter(job=job, user=request.user).exists()
    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'already_applied': already_applied,
        'has_seeker_profile': has_seeker_profile,
        'is_interested': is_interested,
        'is_own_posting': job.posted_by == request.user,
    })


@login_required
def job_quick_view(request, pk):
    """Returns job details as JSON for the site's custom popup/modal preview on the job board."""
    job = get_object_or_404(JobOpening, pk=pk)
    is_owner_or_admin = job.posted_by == request.user or request.user.is_admin_user
    if not job.is_live and not is_owner_or_admin:
        raise Http404
    is_interested = JobInterest.objects.filter(job=job, user=request.user).exists()
    return JsonResponse({
        'title': job.title,
        'domain': job.domain,
        'job_type': job.job_type,
        'experience': job.experience,
        'years_of_experience': job.years_of_experience,
        'city': job.city,
        'salary_package': job.salary_package,
        'last_date_to_apply': job.last_date_to_apply.strftime('%d %b %Y') if job.last_date_to_apply else '',
        'skills': job.skills_list(),
        'description': job.description,
        'is_interested': is_interested,
        'detail_url': reverse('job_detail', args=[job.pk]),
        'interest_url': reverse('toggle_interest', args=[job.pk]),
    })


@login_required
def job_apply(request, pk):
    """Shows the applicant's saved 'Looking for a Job' profile and confirms the application."""
    job = get_object_or_404(JobOpening, pk=pk)
    if not job.is_live:
        raise Http404
    if job.posted_by == request.user:
        messages.error(request, "You can't apply to your own job posting.")
        return redirect('job_detail', pk=pk)

    seeker_profile = JobSeeker.objects.filter(user=request.user).order_by('-created_at').first()
    if not seeker_profile:
        request.session['apply_after_profile'] = job.pk
        messages.warning(request, 'Please complete your "Looking for a Job" profile first, then you can apply.')
        return redirect('seek_job')

    if JobApplication.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, "You've already applied to this job.")
        return redirect('job_detail', pk=pk)

    if request.method == 'POST':
        JobApplication.objects.create(job=job, applicant=request.user, seeker_profile=seeker_profile)
        messages.success(request, 'Your application has been submitted successfully!')
        return redirect('job_detail', pk=pk)

    return render(request, 'jobs/job_apply_confirm.html', {'job': job, 'seeker_profile': seeker_profile})


@login_required
def toggle_interest(request, pk):
    job = get_object_or_404(JobOpening, pk=pk)
    next_url = request.GET.get('next') or request.POST.get('next')
    if not job.is_live:
        raise Http404
    if request.user.is_staff:
        if next_url:
            return redirect(next_url)
        return redirect('job_detail', pk=pk)
    if job.posted_by == request.user:
        if next_url:
            return redirect(next_url)
        return redirect('job_detail', pk=pk)
    if not request.user.profile_fully_complete:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Please complete your full profile first.'}, status=400)
        messages.warning(request, 'Please complete your full profile (including resume) to express interest.')
        return redirect('edit_profile')
    interest, created = JobInterest.objects.get_or_create(job=job, user=request.user)
    if created:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'interested': True})
        messages.success(request, 'You have registered your interest!')
    else:
        interest.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'interested': False})
        messages.info(request, 'Interest removed.')
    if next_url:
        return redirect(next_url)
    return redirect('job_detail', pk=pk)


@login_required
def interest_list(request, pk):
    if not request.user.is_admin_user:
        raise Http404
    job = get_object_or_404(JobOpening, pk=pk)
    interests = JobInterest.objects.filter(job=job).select_related('user')
    return render(request, 'jobs/interest_list.html', {'job': job, 'interests': interests})
