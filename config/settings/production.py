import sentry_sdk
from celery.schedules import crontab

from config.settings.base import *  # noqa
from config.settings.tools.django_constance import *  # noqa
from config.settings.tools.django_easy_audit import *  # noqa

# Email settings
# https://docs.djangoproject.com/en/5.0/topics/email/

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="sandbox.smtp.mailtrap.io")  # noqa
EMAIL_PORT = config("EMAIL_PORT", default="587")  # noqa
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")  # noqa
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")  # noqa
EMAIL_USE_TLS = True  # noqa
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="")  # noqa

# Logging settings
# https://docs.djangoproject.com/en/5.0/topics/logging/

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "debug.log",
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": True,
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# File upload settings

FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Configuración de CSRF

CSRF_USE_SESSIONS = True
CSRF_COOKIE_HTTPONLY = True

# Cambia a True cuando tengas HTTPS

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [f"http://{host}" for host in ALLOWED_HOSTS]  # noqa

# Configuración de seguridad para producción sin HTTPS

SECURE_SSL_REDIRECT = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Configuración de seguridad adicional

X_FRAME_OPTIONS = "DENY"

# Sentry

sentry_sdk.init(
    dsn=config("SENTRY_DSN", default=""),  # noqa
    traces_sample_rate=1.0,
    _experiments={
        "continuous_profiling_auto_start": True,
    },
)

# Celery tasks configuration

CELERY_BEAT_SCHEDULE = {
    "execute_test_task": {
        "task": "apps.core.tasks.test_task",
        "schedule": crontab(hour=22, minute=0),
        "kwargs": {},
    },
}

MIDDLEWARE += [  # noqa
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# WhiteNoise settings

WHITENOISE_USE_FINDERS = True
WHITENOISE_MAX_AGE = 31536000

# Django Constance settings

CONSTANCE_BACKEND = "constance.backends.redisd.RedisBackend"

CONSTANCE_REDIS_CONNECTION = config(  # noqa
    "REDIS_URL", default="redis://127.0.0.1:6379/"
)
