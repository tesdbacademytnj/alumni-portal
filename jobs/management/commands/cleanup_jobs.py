from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from jobs.models import JobOpening, JOB_REMOVE_GRACE_DAYS, mark_expired_jobs


class Command(BaseCommand):
    """
    Daily maintenance for the job board:

    1. Any *published* job whose last_date_to_apply has passed is marked
       'expired' -> immediately disappears from the public job board.
    2. Any job (of any status) whose last_date_to_apply is more than
       JOB_REMOVE_GRACE_DAYS (default 5) days in the past is permanently
       deleted.

    Schedule this to run once a day, e.g. with cron:
        0 1 * * *  cd /path/to/alumni_portal && venv/bin/python manage.py cleanup_jobs
    or with Windows Task Scheduler running:
        python manage.py cleanup_jobs
    """
    help = 'Expires and removes job openings past their last date to apply.'

    def handle(self, *args, **options):
        today = timezone.localdate()

        expired_count = JobOpening.objects.filter(status='published', last_date_to_apply__lt=today).count()
        mark_expired_jobs()

        removal_cutoff = today - timedelta(days=JOB_REMOVE_GRACE_DAYS)
        to_remove = JobOpening.objects.filter(last_date_to_apply__lt=removal_cutoff)
        removed_count = to_remove.count()
        to_remove.delete()

        self.stdout.write(self.style.SUCCESS(
            f'Cleanup complete: {expired_count} job(s) marked expired, '
            f'{removed_count} job(s) permanently removed.'
        ))
