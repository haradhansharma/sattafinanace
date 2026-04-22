# from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.conf import settings


class SattaSite(Site):
    """Custom site model extending Django's built-in Site."""

    # Example additional fields
    site_title = models.CharField(max_length=255, blank=True, default="")
    support_email = models.EmailField(blank=True, null=True)
    maintenance_mode = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Satta Site"
        verbose_name_plural = "Satta Sites"

    def __str__(self):
        return f"{self.domain} ({self.site_title or 'No title'})"


class SiteSettings(models.Model):
    """Site-specific settings attached to the Django sites framework."""

    site = models.OneToOneField(Site, on_delete=models.CASCADE, related_name="settings")
    homepage_description = models.TextField(blank=True)
    allow_registration = models.BooleanField(default=True)
    max_users = models.PositiveIntegerField(default=0, help_text="0 means unlimited")

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return f"Settings for {self.site.domain}"


class TenantMixin(models.Model):
    """
    Abstract base model that enforces tenant isolation.
    Adds an `owner` FK to the User model on every child.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
        db_index=True,
    )

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        # Allow setting owner as a positional arg or keyword
        owner = kwargs.pop("owner", None)
        super().__init__(*args, **kwargs)
        if owner is not None:
            self.owner = owner


class TenantManager(models.Manager):
    """
    Custom manager that auto-filters by owner.
    Usage: MyModel.objects.for_user(request.user).all()
    """

    def for_user(self, user):
        return self.get_queryset().filter(owner=user)
