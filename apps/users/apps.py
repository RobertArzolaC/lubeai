from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    verbose_name = _("Users Management")

    def ready(self):
        """Import signals when the app is ready."""
        import apps.users.signals  # noqa: F401
