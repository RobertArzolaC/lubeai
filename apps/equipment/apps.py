from django.apps import AppConfig


class EquipmentConfig(AppConfig):
    """Equipment application configuration."""

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "apps.equipment"
