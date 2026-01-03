from django.utils.translation import gettext_lazy as _

# Django Constance
# https://django-constance.readthedocs.io/en/latest/

CONSTANCE_FILE_ROOT = "constance"

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

CONSTANCE_ADDITIONAL_FIELDS = {
    "image_field": ["django.forms.ImageField", {}],
    "json_field": ["django.forms.JSONField", {}],
}

CONSTANCE_CONFIG = {
    "PROJECT_NAME": ("Project Name", _("Project name.")),
    "COMPANY_LOGO": ("default.png", _("Company logo"), "image_field"),
    "COMPANY_DOMAIN": ("https://company.com/", _("Website domain.")),
    "JSON_FIELD_EXAMPLE": ({"name": "test"}, _("Test json field"), "json_field"),
    "ENABLE_SEND_EMAIL": (True, _("Enable sending emails.")),
    "ENABLE_VERIFICATION_EMAIL": (True, _("Enable email verification.")),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "1. General Options": {
        "fields": (
            "PROJECT_NAME",
            "COMPANY_LOGO",
            "JSON_FIELD_EXAMPLE",
            "COMPANY_DOMAIN",
            "ENABLE_SEND_EMAIL",
            "ENABLE_VERIFICATION_EMAIL",
        ),
        "collapse": False,
    },
}
