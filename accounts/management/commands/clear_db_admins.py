from django.core.management.base import BaseCommand
from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Remove all DB-created admins (use .env admin credentials instead)'

    def handle(self, *args, **options):
        qs = CustomUser.objects.filter(is_admin_user=True)
        count = qs.count()
        qs.delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} admin account(s). Login via .env credentials now.'))
