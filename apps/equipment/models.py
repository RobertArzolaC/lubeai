"""Equipment models."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from apps.core import models as core_models
from apps.core.models import BaseUserTracked, IsActive
from apps.users import models as users_models


class Machine(TimeStampedModel, BaseUserTracked, IsActive):
    """
    Machine model.

    Represents industrial equipment/machinery used for condition monitoring
    and predictive maintenance.
    """

    organization = models.ForeignKey(
        users_models.Organization,
        verbose_name=_("Organization"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="machines",
        help_text=_("Organization that owns this machine"),
    )
    name = models.CharField(
        _("Name"),
        max_length=200,
        help_text=_("Machine name or identifier"),
    )
    serial_number = models.CharField(
        _("Serial Number"),
        max_length=100,
        unique=True,
        help_text=_("Unique serial number of the machine"),
    )
    model = models.CharField(
        _("Model"),
        max_length=200,
        help_text=_("Machine model or type designation"),
    )

    class Meta:
        verbose_name = _("Machine")
        verbose_name_plural = _("Machines")
        ordering = ("name",)
        indexes = [
            models.Index(fields=["serial_number"]),
            models.Index(fields=["organization", "is_active"]),
        ]

    def __str__(self) -> str:
        """Return string representation of machine."""
        return f"{self.name} ({self.serial_number})"


class MachineType(
    TimeStampedModel,
    BaseUserTracked,
    core_models.NameDescription,
    core_models.IsActive,
):
    """
    Machine Type model.

    Represents categories/types of industrial machines
    (e.g., Pump, Motor, Compressor, Turbine, etc.)
    """

    class Meta:
        verbose_name = _("Machine Type")
        verbose_name_plural = _("Machine Types")
        ordering = ("name",)

    # __str__ is inherited from NameDescription


class Component(TimeStampedModel, BaseUserTracked, IsActive):
    """
    Component model.

    Represents parts or components installed in a machine.
    """

    machine = models.ForeignKey(
        Machine,
        verbose_name=_("Machine"),
        on_delete=models.CASCADE,
        related_name="components",
        help_text=_("Machine this component belongs to"),
    )
    type = models.ForeignKey(
        MachineType,
        verbose_name=_("Type"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="components",
        help_text=_("Type/category of this component"),
    )
    serial_number = models.CharField(
        _("Serial Number"),
        max_length=100,
        help_text=_("Component serial number"),
    )
    installation_datetime = models.DateTimeField(
        _("Installation Date & Time"),
        help_text=_("When this component was installed"),
    )

    class Meta:
        verbose_name = _("Component")
        verbose_name_plural = _("Components")
        ordering = ("machine", "type", "installation_datetime")
        indexes = [
            models.Index(fields=["serial_number"]),
            models.Index(fields=["machine", "is_active"]),
            models.Index(fields=["installation_datetime"]),
        ]

    def __str__(self) -> str:
        """Return string representation of component."""
        type_name = self.type.name if self.type else "Unknown Type"
        return f"{type_name} - {self.serial_number} ({self.machine.name})"
