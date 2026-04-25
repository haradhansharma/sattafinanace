"""
Celery tasks for FinLife — OTP email sending and cleanup.
Uses the shared celery instance from config/celery.py.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=300,
    acks_late=True,
)
def send_otp_email_task(
    self,
    subject: str,
    body: str,
    recipient: str,
):
    """
    Send OTP email via Celery worker.

    Args:
        self: Celery task instance (for self.retry)
        subject: Email subject line
        body: Email body text
        recipient: Recipient email address
    """
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        logger.info(f"OTP email sent successfully to {recipient}")
    except Exception as exc:
        logger.warning(f"OTP email to {recipient} failed: {exc}. Retrying...")
        raise self.retry(exc=exc)


@shared_task(name="users.cleanup_expired_otps")
def cleanup_expired_otps():
    """
    Periodic task: Delete expired and verified OTP records older than 24 hours.
    Keeps the OTP table lean — prevents unbounded growth.

    Scheduled via celery beat (every 30 minutes).
    """
    from .models import OTP

    cutoff = timezone.now() - timezone.timedelta(hours=24)
    deleted, _ = OTP.objects.filter(
        created_at__lte=cutoff,
    ).delete()

    logger.info(f"OTP cleanup: deleted {deleted} expired/old OTP records")
    return deleted
