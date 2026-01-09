from django.db import models
from django.utils.translation import gettext_lazy as _


class ComponentAnalysis(models.Model):
    """
    Proxy model for component analysis permissions.

    This model doesn't create a database table - it exists solely
    to provide a custom permission for accessing component analysis features.
    """

    class Meta:
        managed = False
        default_permissions = ()  # Don't create default permissions
        permissions = [
            ("view_component_analysis", _("Can view component analysis")),
            (
                "export_component_analysis",
                _("Can export component analysis data"),
            ),
        ]
