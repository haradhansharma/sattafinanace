"""
OTP service for FinLife.
Handles generation, sending, and verification of one-time passwords
for registration and login email verification.
"""

from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import OTP
from .tasks import send_otp_email_task

# Configuration
OTP_EXPIRY_MINUTES = 5
MAX_OTP_PER_HOUR = 5
MAX_OTP_ATTEMPTS = 3


async def create_and_send_otp(email: str, purpose: str, user=None) -> OTP:
    """
    Generate a new OTP, invalidate old ones, persist, and dispatch email
    via Celery (fire-and-forget — response returns immediately).

    Args:
        email: Target email address
        purpose: "register", "login", or "change_password"
        user: Optional User instance (linked via FK)

    Returns:
        The created OTP instance

    Raises:
        ValueError: If rate limit is exceeded
    """
    # --- Rate limiting ---
    cutoff = timezone.now() - timedelta(hours=1)
    recent_count = await OTP.objects.filter(
        email=email,
        purpose=purpose,
        created_at__gte=cutoff,
    ).acount()

    if recent_count >= MAX_OTP_PER_HOUR:
        raise ValueError(f"Too many OTP requests. Please try again after {60} minutes.")

    # --- Invalidate previous unverified OTPs for this email+purpose ---
    await OTP.objects.filter(
        email=email,
        purpose=purpose,
        is_verified=False,
    ).aupdate(is_verified=True)

    # --- Generate and save new OTP ---
    code = OTP.generate_code()
    otp = await OTP.objects.acreate(
        email=email,
        otp_code=code,
        purpose=purpose,
        user=user,
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )

    # --- Dispatch email via Celery (fire-and-forget) ---
    send_otp_email_task.delay(
        subject=_get_subject(purpose),
        body=_get_email_body(code, purpose, email),
        recipient=email,
    )

    return otp


async def verify_otp(email: str, otp_code: str, purpose: str) -> OTP:
    """
    Verify an OTP code.

    Args:
        email: Email address
        otp_code: The 6-digit OTP entered by user
        purpose: "register", "login", or "change_password"

    Returns:
        The verified OTP instance

    Raises:
        ValueError: If OTP is invalid, expired, or max attempts exceeded
    """
    try:
        otp = await OTP.objects.aget(
            email=email,
            otp_code=otp_code,
            purpose=purpose,
            is_verified=False,
        )
    except OTP.DoesNotExist:
        # Increment attempts on the latest unverified OTP to prevent brute force
        latest = await OTP.objects.filter(
            email=email,
            purpose=purpose,
            is_verified=False,
        ).afirst()
        if latest and latest.attempts < MAX_OTP_ATTEMPTS:
            latest.attempts += 1
            await latest.asave(update_fields=["attempts"])
        raise ValueError("Invalid OTP code.")

    if otp.is_expired:
        raise ValueError("OTP has expired. Please request a new one.")

    if otp.attempts >= MAX_OTP_ATTEMPTS:
        raise ValueError("Too many failed attempts. Please request a new OTP.")

    # --- Mark as verified ---
    otp.is_verified = True
    await otp.asave(update_fields=["is_verified"])

    return otp


# ==================== Helpers ====================


def _get_subject(purpose: str) -> str:
    if purpose == "register":
        return "FinLife — Verify Your Email"
    if purpose == "change_password":
        return "FinLife — Password Change Verification"
    if purpose == "forgot_password":
        return "FinLife — Reset Your Password"
    return "FinLife — Login Verification"


def _get_email_body(code: str, purpose: str, email: str) -> str:
    if purpose == "register":
        action = "verify your email address"
    elif purpose == "change_password":
        action = "confirm your password change"
    elif purpose == "forgot_password":
        action = "reset your password"
    else:
        action = "confirm your login"
    return (
        f"Hello,\n\n"
        f"Your verification code is: {code}\n\n"
        f"This code expires in {OTP_EXPIRY_MINUTES} minutes.\n"
        f"Use it to {action} for your FinLife account.\n\n"
        f"If you did not request this code, please ignore this email.\n\n"
        f"— FinLife Team"
    )
