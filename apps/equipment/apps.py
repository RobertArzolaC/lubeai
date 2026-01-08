from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EquipmentConfig(AppConfig):
    """Equipment application configuration."""

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "apps.equipment"
    verbose_name: str = _("Equipment Management")
