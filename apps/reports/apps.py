from django.apps import AppConfig


class ReportsConfig(AppConfig):
    """Reports application configuration."""

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "apps.reports"
