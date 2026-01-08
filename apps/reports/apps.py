from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReportsConfig(AppConfig):
    """Reports application configuration."""

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "apps.reports"
    verbose_name: str = _("Reports Management")
