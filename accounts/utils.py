import logging
import random
import smtplib
import socket

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import EmailOTP
from jobs.models import JobOpening

logger = logging.getLogger('accounts')


class OTPSendError(Exception):
    """
    Raised when the verification email could not be delivered (bad SMTP
    credentials, network down, provider rejected it, etc). Callers should
    catch this and show the user a friendly retry message instead of
    letting it surface as a 500 page.
    """
    pass


def generate_otp_code():
    """6-digit numeric code, e.g. '042918'."""
    return f"{random.randint(0, 999999):06d}"


def send_otp_email(user, purpose='verification'):
    """
    Invalidate any previous unused codes for this user, create a fresh one,
    and email it (HTML + plain-text fallback). Purpose can be 'verification'
    (registration) or 'reset' (password reset). Returns the EmailOTP instance.

    Raises OTPSendError on delivery failure.
    """
    EmailOTP.objects.filter(user=user, is_used=False).delete()
    otp = EmailOTP.objects.create(user=user, code=generate_otp_code())

    context = {
        'full_name': user.full_name,
        'code': otp.code,
        'expiry_minutes': settings.OTP_EXPIRY_MINUTES,
    }
    html_body = render_to_string('accounts/email/otp_email.html', context)

    if purpose == 'reset':
        text_body = (
            f"Hi {user.full_name},\n\n"
            f"Your AlumniPortal password reset code is: {otp.code}\n\n"
            f"This code expires in {settings.OTP_EXPIRY_MINUTES} minutes. "
            f"If you didn't request this, someone may have tried to access your "
            f"account — you can safely ignore this email.\n\n"
            f"— AlumniPortal"
        )
        email = EmailMultiAlternatives(
            subject='Reset your AlumniPortal password',
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
    else:
        text_body = (
            f"Hi {user.full_name},\n\n"
            f"Your AlumniPortal verification code is: {otp.code}\n\n"
            f"This code expires in {settings.OTP_EXPIRY_MINUTES} minutes. "
            f"If you didn't request this, you can safely ignore this email — "
            f"no account will be created.\n\n"
            f"— AlumniPortal"
        )
        email = EmailMultiAlternatives(
            subject='Your AlumniPortal verification code',
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )

    email.attach_alternative(html_body, 'text/html')

    try:
        email.send(fail_silently=False)
    except (smtplib.SMTPException, socket.error, ConnectionError, OSError) as exc:
        logger.error('OTP email failed to send to %s: %s', user.email, exc)
        raise OTPSendError(str(exc)) from exc

    return otp


def send_job_unpublished_email(job):
    user = job.posted_by
    context = {
        'full_name': user.full_name,
        'job_title': job.title,
        'job_company': job.company,
    }
    html_body = render_to_string('accounts/email/job_unpublished.html', context)
    text_body = (
        f"Hi {user.full_name},\n\n"
        f"Your job posting \"{job.title}\" at {job.company} has been unpublished by an administrator "
        f"and sent back for review. Please log in to your dashboard to make any necessary changes.\n\n"
        f"— AlumniPortal"
    )
    email = EmailMultiAlternatives(
        subject='Your job posting has been unpublished',
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_body, 'text/html')

    try:
        email.send(fail_silently=False)
    except (smtplib.SMTPException, socket.error, ConnectionError, OSError) as exc:
        logger.error('Unpublished notification email failed to send to %s: %s', user.email, exc)
