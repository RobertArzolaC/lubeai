from config.settings.base import *  # noqa
from config.settings.tools.django_constance import *  # noqa
from config.settings.tools.django_easy_audit import *  # noqa

# Disable easyaudit settings
DJANGO_EASY_AUDIT_WATCH_AUTH_EVENTS = False
DJANGO_EASY_AUDIT_WATCH_MODEL_EVENTS = False
DJANGO_EASY_AUDIT_WATCH_REQUEST_EVENTS = False

# Static files (CSS, JavaScript, Images)
# STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa
DEBUG = True

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Testing settings
TESTING = True
