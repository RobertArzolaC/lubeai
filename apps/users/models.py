from allauth.account.models import EmailAddress
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField
from model_utils.models import SoftDeletableModel, TimeStampedModel

from apps.core import models as core_models
from apps.users.managers import CustomUserManager


class Organization(
    SoftDeletableModel,
    TimeStampedModel,
    core_models.BaseAddress,
    core_models.BaseContact,
    core_models.BaseUserTracked,
    core_models.NameDescription,
    core_models.IsActive,
):
    slug = AutoSlugField(populate_from="name", unique=True, editable=True)
    tax_id = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
        ordering = ("name",)

    def __str__(self):
        return self.name


class User(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)
    avatar = models.ImageField(
        upload_to="users/avatars/", null=True, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @cached_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @cached_property
    def is_account(self):
        return hasattr(self, "account")


class Account(SoftDeletableModel, TimeStampedModel):
    user = models.OneToOneField(
        User,
        verbose_name=_("User"),
        on_delete=models.CASCADE,
        related_name="account",
    )
    organization = models.ForeignKey(
        Organization,
        verbose_name=_("Organization"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts",
    )

    class Meta:
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")
        ordering = ("user__last_name", "user__first_name")

    def __str__(self):
        return self.user.get_full_name()

    @cached_property
    def full_name(self):
        return self.user.get_full_name()

    @cached_property
    def is_email_verified(self):
        return EmailAddress.objects.filter(
            user=self.user, verified=True
        ).exists()
