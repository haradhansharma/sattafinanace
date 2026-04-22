import uuid

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
    Frontend interface: id, name, email, avatar, currency, dateFormat,
                        darkMode, notifications, createdAt, updatedAt

    No 'owner' field needed — User IS the owner of all data.
    """

    slug = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True, db_index=True)
    avatar = models.URLField(blank=True, default="")

    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="BDT",
    )
    date_format = models.CharField(max_length=20, default="dd/MM/yyyy")
    dark_mode = models.BooleanField(default=False)

    notifications = notifications = models.JSONField(default=_default_notifications)

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
