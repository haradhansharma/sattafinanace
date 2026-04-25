# backend/users/managers.py

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager as DjangoBaseUserManager,
)
from django.utils.translation import gettext_lazy as _


class UserManager(DjangoBaseUserManager):
    use_in_migrations = True

    # --- Synchronous Logic ---

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("The email field must be set."))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        # ... validation checks ...
        return self._create_user(email, password, **extra_fields)

    # --- Asynchronous Logic ---

    async def _acreate_user(self, email, password, **extra_fields):
        """Async version of the private creation method."""
        if not email:
            raise ValueError(_("The email field must be set."))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        # Use asave() for the database hit
        await user.asave(using=self._db)
        return user

    async def acreate_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", False)
        return await self._acreate_user(email, password, **extra_fields)

    async def acreate_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return await self._acreate_user(email, password, **extra_fields)
