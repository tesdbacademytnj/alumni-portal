import secrets
import string

from django.core.management.base import BaseCommand, CommandError
from accounts.models import CustomUser, AdminProfile


def generate_access_code(length=12):
    """Random alphanumeric code, e.g. 'aB3xK9pQmZ7w'."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = (
        'Create an admin account. Admins do NOT self-register through the '
        'website — you create each one here and hand them their username '
        'and access code directly. That pair is all they need to log in '
        'at /accounts/admin-login/ (no email/password/OTP involved).'
    )

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Unique login username for this admin.')
        parser.add_argument('--name', required=True, help='Display name.')
        parser.add_argument('--email', required=True, help='Contact email (not used for login).')
        parser.add_argument(
            '--code', required=False,
            help='Access code for this admin. If omitted, a secure random one is generated and printed.'
        )

    def handle(self, *args, **options):
        username = options['username'].strip()
        name = options['name']
        email = options['email'].strip().lower()
        code = options['code'] or generate_access_code()

        if CustomUser.objects.filter(username__iexact=username).exists():
            raise CommandError(f'Username "{username}" is already taken.')
        if CustomUser.objects.filter(email=email).exists():
            raise CommandError(f'Email "{email}" is already in use.')

        user = CustomUser.objects.create_user(email=email, password=None, full_name=name)
        user.username = username
        user.is_admin_user = True
        user.is_staff = True
        user.is_active = True
        user.set_unusable_password()  # admins never log in with a password
        user.save()
        AdminProfile.objects.create(user=user, access_code=code)

        self.stdout.write(self.style.SUCCESS(
            f'\nAdmin "{name}" created.\n'
            f'  Username:    {username}\n'
            f'  Access code: {code}\n\n'
            f'Give these two values to the admin directly (not over email/chat '
            f'if you can help it) — they\'re the only credentials needed at '
            f'/accounts/admin-login/. This code is shown once; AdminProfile '
            f'is in the database if you need to look it up again, or just '
            f're-run this command with --code to reset it.\n'
        ))
