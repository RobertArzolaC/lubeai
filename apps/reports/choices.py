from django.db import models
from django.utils.translation import gettext_lazy as _


class ReportStatus(models.TextChoices):
    """Status choices for reports."""

    PENDING = "PENDING", _("Pending")
    REVIEWED = "REVIEWED", _("Reviewed")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")


class ReportCondition(models.TextChoices):
    """Condition choices for reports."""

    NORMAL = "NORMAL", _("Normal")
    CAUTION = "CAUTION", _("Caution")
    CRITICAL = "CRITICAL", _("Critical")
    SEVERE = "SEVERE", _("Severe")
