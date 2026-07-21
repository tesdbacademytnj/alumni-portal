from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import CustomUser


class Command(BaseCommand):
    help = (
        'Delete user accounts that registered but never completed OTP '
        'verification, older than --hours (default 24). Safe to run on a '
        'schedule (cron / Task Scheduler) once this is deployed.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours', type=int, default=24,
            help='Delete unverified accounts older than this many hours (default: 24).'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be deleted without actually deleting it.'
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=options['hours'])
        stale = CustomUser.objects.filter(is_active=False, date_joined__lt=cutoff)
        count = stale.count()

        if options['dry_run']:
            for u in stale:
                self.stdout.write(f'Would delete: {u.email} (joined {u.date_joined})')
            self.stdout.write(self.style.WARNING(f'{count} unverified account(s) would be deleted (dry run).'))
            return

        stale.delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} unverified account(s) older than {options["hours"]}h.'))
