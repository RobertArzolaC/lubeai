from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusChoices(models.IntegerChoices):
    PENDING = 0, _("Pending")
    VALIDATING = 1, _("Validating")
    PROCESSING = 2, _("Processing")
    COMPLETED = 3, _("Completed")
    FAILED = 4, _("Failed")
    CANCELED = 5, _("Canceled")
    APPROVED = 6, _("Approved")


class MonthChoices(models.IntegerChoices):
    JANUARY = 1, _("January")
    FEBRUARY = 2, _("February")
    MARCH = 3, _("March")
    APRIL = 4, _("April")
    MAY = 5, _("May")
    JUNE = 6, _("June")
    JULY = 7, _("July")
    AUGUST = 8, _("August")
    SEPTEMBER = 9, _("September")
    OCTOBER = 10, _("October")
    NOVEMBER = 11, _("November")
    DECEMBER = 12, _("December")


class DocumentType(models.TextChoices):
    DOCUMENT = "DNI", _("National Identity Document")
    RUC = "RUC", _("Unique Taxpayer Registry")
    PASSPORT = "PASSPORT", _("Passport")
    FOREIGN_ID = "FOREIGN_ID", _("Foreigner ID")


class Gender(models.TextChoices):
    MALE = "M", _("Male")
    FEMALE = "F", _("Female")
    OTHER = "O", _("Other")
