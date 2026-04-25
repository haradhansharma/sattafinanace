import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


CURRENCY_CHOICES = [
    ("BDT", "Bangladeshi Taka"),
    ("USD", "US Dollar"),
    ("EUR", "Euro"),
    ("GBP", "British Pound"),
    ("INR", "Indian Rupee"),
    ("SGD", "Singapore Dollar"),
    ("SAR", "Saudi Riyal"),
]

DEFAULT_NOTIFICATIONS = {
    "email": True,
    "push": True,
    "budgetAlert": True,
    "lowBalance": True,
    "loanReminder": True,
}


def _default_notifications():
    return dict(DEFAULT_NOTIFICATIONS)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model matching the frontend User type exactly.
    Frontend interface: id, slug, name, email, avatar, currency, dateFormat,
                        darkMode, notifications, createdAt, updatedAt

    No 'owner' field needed — User IS the owner of all data.
    id: auto BigAutoField from Django Model (default PK).
    slug: UUID4 for public-facing URLs.
    """

    slug = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        editable=False,
        help_text="UUID used for public-facing URLs.",
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)
    avatar = models.URLField(blank=True, default="")

    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="BDT",
    )
    date_format = models.CharField(max_length=20, default="dd/MM/yyyy")
    dark_mode = models.BooleanField(default=False)

    notifications = models.JSONField(default=_default_notifications)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = "users_user"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email


class OTP(models.Model):
    """
    One-time password for email verification (registration & login).
    Each OTP is 6 digits, expires after OTP_EXPIRY_MINUTES.
    Rate-limited: max MAX_OTP_PER_HOUR per email per purpose.
    """

    PURPOSE_CHOICES = [
        ("register", "Registration Verification"),
        ("login", "Login Verification"),
        ("change_password", "Password Change Verification"),
        ("forgot_password", "Forgot Password Verification"),
    ]

    email = models.EmailField(db_index=True)
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="otps",
    )
    is_verified = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "users_otp"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "purpose", "is_verified"]),
        ]

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_valid(self):
        return not self.is_expired and not self.is_verified and self.attempts < 3

    def mark_verified(self):
        """Mark this OTP as verified."""
        self.is_verified = True
        self.save(update_fields=["is_verified"])

    @classmethod
    def generate_code(cls):
        """Generate a cryptographically secure 6-digit code."""
        import secrets

        return f"{secrets.randbelow(1_000_000):06d}"
